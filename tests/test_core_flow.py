import base64
import os

os.environ["DATA_STORE_PROVIDER"] = "local"
os.environ["ENABLE_GOOGLE_INTEGRATIONS"] = "false"

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.models.schemas import (
    AdvisoryTestResponse,
    DataSignal,
    GovernmentDataContextRequest,
    GovernmentDataContextResponse,
    RiskLevel,
    SatelliteHistoryPoint,
    SatelliteSignalResponse,
    DetectLanguageResponse,
    TranslateTextResponse,
    WeatherContextRequest,
    VoiceSpeakResponse,
    VoiceTranscribeResponse,
)
from app.repositories.store import store
from app.services.bigquery_ingestion_service import PublicDataIngestionService
from app.services.bigquery_public_data_service import BigQueryPublicDataService
from app.services.dialogflow_channel_service import DialogflowChannelResult
from app.services.weather_context_service import WeatherContextService

client = TestClient(app)


def setup_function() -> None:
    store.reset()


def create_demo_farmer() -> str:
    response = client.post(
        "/api/v1/farmers",
        json={
            "name": "Ravi",
            "phone": "9999999999",
            "language": "te-IN",
            "village": "Demo Village",
            "district": "Guntur",
            "state": "Andhra Pradesh",
            "farm": {
                "area_acres": 2.5,
                "soil_type": "black",
                "soil_ph": 6.8,
                "groundwater_depth_m": 18,
                "latitude": 16.3,
                "longitude": 80.4,
            },
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_end_to_end_farmer_advisory_and_diagnosis_flow() -> None:
    farmer_id = create_demo_farmer()

    crop_response = client.post(
        "/api/v1/recommendations/crop",
        json={
            "farmer_id": farmer_id,
            "season": "kharif",
            "expected_rainfall_mm": 620,
            "ndvi": 0.42,
            "water_availability": "medium",
        },
    )
    assert crop_response.status_code == 200
    assert len(crop_response.json()["recommendations"]) == 3

    advisory_response = client.post(
        "/api/v1/advisories/dry-spell",
        json={
            "farmer_id": farmer_id,
            "crop": "maize",
            "soil_moisture": 0.18,
            "rainfall_forecast_mm": [0, 0, 0, 1, 0, 0, 3],
            "temperature_c": 36,
        },
    )
    assert advisory_response.status_code == 200
    assert advisory_response.json()["risk_level"] in {"high", "critical"}

    diagnosis_response = client.post(
        "/api/v1/diagnosis/log",
        json={
            "farmer_id": farmer_id,
            "crop": "chilli",
            "symptoms_text": "Leaves curling and white insects visible",
            "photo_uri": "gs://demo/chilli-leaf.jpg",
        },
    )
    assert diagnosis_response.status_code == 200
    assert diagnosis_response.json()["expert_ticket"]["status"] == "open"

    tickets_response = client.get(f"/api/v1/expert/tickets/{farmer_id}")
    assert tickets_response.status_code == 200
    assert len(tickets_response.json()) == 1

    stage_response = client.post(
        "/api/v1/advisories/crop-stage",
        json={
            "farmer_id": farmer_id,
            "crop": "maize",
            "stage": "flowering",
            "rainfall_forecast_mm": [0, 0, 0, 0, 1, 0, 2],
            "humidity_percent": 88,
            "soil_moisture": 0.19,
        },
    )
    assert stage_response.status_code == 200
    assert stage_response.json()["alert_plan"]["channels"]


def test_admin_dashboard_serves_provider_switch_ui() -> None:
    response = client.get("/admin")

    assert response.status_code == 200
    assert "Kisan Alert Admin" in response.text
    assert "/api/v1/providers/config" in response.text
    assert "/health" in response.text


def test_low_connectivity_channels_accept_farmer_intent() -> None:
    sms_response = client.post(
        "/api/v1/sms/webhook",
        json={"from_phone": "9999999999", "text": "WATER maize 522001", "language": "hi-IN"},
    )
    assert sms_response.status_code == 200
    assert sms_response.json()["intent"] == "irrigation_advisory"

    whatsapp_response = client.post(
        "/api/v1/whatsapp/webhook",
        json={
            "from_phone": "9999999999",
            "text": "my crop leaf has spots",
            "language": "en-IN",
        },
    )
    assert whatsapp_response.status_code == 200
    assert whatsapp_response.json()["intent"] == "crop_diagnosis"

    call_response = client.post(
        "/api/v1/calls/webhook",
        json={
            "from_phone": "9999999999",
            "call_id": "demo-call-1",
            "dtmf_digit": "2",
            "language": "te-IN",
        },
    )
    assert call_response.status_code == 200
    assert call_response.json()["intent"] == "crop_recommendation"


def test_channels_use_dialogflow_adapter_when_available(monkeypatch) -> None:
    def fake_route(self, **kwargs):
        assert kwargs["language"] == "en-IN"
        return DialogflowChannelResult(
            intent="irrigation_advisory",
            confidence=0.91,
            reply="Dialogflow says irrigate lightly this evening.",
            parameters={"crop": "maize"},
            session_id=kwargs["session_id"],
        )

    monkeypatch.setattr("app.services.dialogflow_channel_service.DialogflowChannelService.route_text", fake_route)

    sms_response = client.post(
        "/api/v1/sms/webhook",
        json={"from_phone": "9999999999", "text": "Should I irrigate?", "language": "en-IN"},
    )
    assert sms_response.status_code == 200
    assert sms_response.json()["reply"].startswith("Dialogflow says")

    whatsapp_response = client.post(
        "/api/v1/whatsapp/webhook",
        json={"from_phone": "9999999999", "text": "Should I irrigate?", "language": "en-IN"},
    )
    assert whatsapp_response.status_code == 200
    assert whatsapp_response.json()["intent"] == "irrigation_advisory"
    assert whatsapp_response.json()["template_name"] == "dialogflow_reply"

    call_response = client.post(
        "/api/v1/calls/webhook",
        json={
            "from_phone": "9999999999",
            "call_id": "dialogflow-call-1",
            "transcript": "Should I irrigate?",
            "language": "en-IN",
        },
    )
    assert call_response.status_code == 200
    assert call_response.json()["spoken_reply"].startswith("Dialogflow says")


def test_whatsapp_text_identifies_farmer_and_logs_conversation() -> None:
    response = client.post(
        "/api/v1/whatsapp/webhook",
        json={
            "from_phone": "+91 99999 88888",
            "text": "Should I irrigate today?",
            "language": "en-IN",
            "message_id": "wa-text-1",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["farmer_id"]
    assert body["intent"] == "irrigation_advisory"
    assert body["delivery_status"] in {"skipped_no_authkey", "skipped_no_template", "dry_run"}

    recent = client.get(f"/api/v1/conversations/{body['farmer_id']}")
    assert recent.status_code == 200
    assert [item["role"] for item in recent.json()] == ["farmer", "assistant"]


def test_whatsapp_location_updates_farmer_farm_coordinates() -> None:
    response = client.post(
        "/api/v1/whatsapp/webhook",
        json={
            "from_phone": "+91 99999 77777",
            "latitude": 16.3,
            "longitude": 80.4,
            "location_label": "Farm",
            "language": "te-IN",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "location_update"
    farmer = store.get_farmer(body["farmer_id"])
    assert farmer is not None
    assert farmer.farm.latitude == 16.3
    assert farmer.farm.longitude == 80.4


def test_whatsapp_voice_note_transcribes_and_replies(monkeypatch) -> None:
    def fake_transcribe(self, payload):
        return VoiceTranscribeResponse(
            transcript="Should I irrigate today?",
            language="en-IN",
            provider="google_stt",
        )

    monkeypatch.setattr("app.services.voice_service.VoiceService.transcribe", fake_transcribe)

    response = client.post(
        "/api/v1/whatsapp/webhook",
        json={
            "from_phone": "+91 99999 66666",
            "audio_base64": base64.b64encode(b"voice").decode("ascii"),
            "audio_mime_type": "audio/ogg",
            "media_type": "audio",
            "language": "en-IN",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["transcript"] == "Should I irrigate today?"
    assert body["intent"] == "irrigation_advisory"


def test_whatsapp_crop_photo_creates_diagnosis_ticket() -> None:
    response = client.post(
        "/api/v1/whatsapp/webhook",
        json={
            "from_phone": "+91 99999 55555",
            "text": "chilli leaf has spots",
            "media_base64": base64.b64encode(b"leaf").decode("ascii"),
            "media_mime_type": "image/jpeg",
            "media_type": "image",
            "language": "en-IN",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "crop_diagnosis"
    assert body["should_escalate"] is True
    assert "Ticket:" in body["reply"]
    tickets = client.get(f"/api/v1/expert/tickets/{body['farmer_id']}")
    assert tickets.status_code == 200
    assert len(tickets.json()) == 1


def test_alert_delivery_uses_configured_channels_in_dry_run(monkeypatch) -> None:
    farmer_id = create_demo_farmer()
    monkeypatch.setattr(settings, "authkey_api_key", "secret-key")
    monkeypatch.setattr(settings, "authkey_sms_sender", "KISAN")
    monkeypatch.setattr(settings, "authkey_whatsapp_template_id", "template-1")
    monkeypatch.setattr(settings, "authkey_send_enabled", False)

    response = client.post(
        "/api/v1/alerts/deliver",
        json={
            "farmer_id": farmer_id,
            "message": "Heavy rain risk today. Keep drainage open and avoid spraying.",
            "alert_plan": {
                "priority": "urgent",
                "channels": ["whatsapp", "sms", "voice_call"],
                "reason": "Critical rainfall risk.",
                "call_required": True,
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["overall_status"] == "dry_run"
    assert {item["channel"] for item in body["results"]} == {"whatsapp", "sms", "voice_call"}
    assert all(item["provider"] == "authkey" for item in body["results"])
    assert all(item["status"] == "dry_run" for item in body["results"])


def test_daily_alert_runner_generates_and_delivers_high_risk_alert(monkeypatch) -> None:
    farmer_id = create_demo_farmer()
    monkeypatch.setattr(settings, "authkey_api_key", "secret-key")
    monkeypatch.setattr(settings, "authkey_sms_sender", "KISAN")
    monkeypatch.setattr(settings, "authkey_whatsapp_template_id", "template-1")
    monkeypatch.setattr(settings, "authkey_send_enabled", False)

    response = client.post(
        "/api/v1/alerts/run-daily",
        json={
            "farmer_ids": [farmer_id],
            "crop": "maize",
            "min_priority": "medium",
            "rainfall_forecast_mm": [0, 0, 0, 0, 0, 0, 0],
            "soil_moisture": 0.12,
            "temperature_c": 38,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["processed"] == 1
    assert body["generated"] == 1
    assert body["delivered"] == 1
    result = body["results"][0]
    assert result["risk_level"] == "critical"
    assert result["priority"] == "urgent"
    assert result["delivery"]["overall_status"] == "dry_run"

    recent = client.get(f"/api/v1/conversations/{farmer_id}")
    assert recent.status_code == 200
    assert recent.json()[-1]["intent"] == "daily_dry_spell_alert"


def test_daily_alert_runner_skips_farmer_without_location_or_forecast() -> None:
    farmer_response = client.post(
        "/api/v1/farmers",
        json={
            "name": "Location Pending",
            "phone": "8888888888",
            "language": "hi-IN",
            "village": "Unknown",
            "district": "Unknown",
            "state": "Unknown",
            "farm": {"area_acres": 1, "soil_type": "unknown"},
        },
    )
    assert farmer_response.status_code == 200

    response = client.post(
        "/api/v1/alerts/run-daily",
        json={"farmer_ids": [farmer_response.json()["id"]], "crop": "cotton"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["processed"] == 1
    assert body["generated"] == 0
    assert body["skipped"] == 1
    assert body["results"][0]["skipped_reason"] == "farm_location_required"


def test_dialogflow_webhook_runs_irrigation_fulfillment() -> None:
    response = client.post(
        "/api/v1/dialogflow/webhook",
        json={
            "languageCode": "en-IN",
            "fulfillmentInfo": {"tag": "irrigation_advisory"},
            "sessionInfo": {
                "parameters": {
                    "phone": "9999999999",
                    "name": "Ravi",
                    "state": "Andhra Pradesh",
                    "district": "Guntur",
                    "village": "Demo Village",
                    "crop": "maize",
                    "rainfall_forecast_mm": [0, 0, 0, 0, 0, 0, 0],
                    "soil_moisture": 0.13,
                    "temperature_c": 37,
                    "text": "Should I irrigate maize today?",
                }
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["payload"]["intent"] == "irrigation_advisory"
    assert body["sessionInfo"]["parameters"]["farmer_id"]
    assert "fulfillmentResponse" in body
    assert body["fulfillmentResponse"]["messages"][0]["text"]["text"][0]


def test_dialogflow_webhook_runs_crop_recommendation_fulfillment() -> None:
    farmer_id = create_demo_farmer()
    farmer = store.get_farmer(farmer_id)
    assert farmer is not None

    response = client.post(
        "/api/v1/dialogflow/webhook",
        json={
            "languageCode": "en-IN",
            "intentInfo": {"displayName": "crop_recommendation"},
            "sessionInfo": {
                "parameters": {
                    "phone": farmer.phone,
                    "season": "kharif",
                    "expected_rainfall_mm": 620,
                    "water_availability": "medium",
                }
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["payload"]["intent"] == "crop_recommendation"
    assert "Recommended crops:" in body["fulfillmentResponse"]["messages"][0]["text"]["text"][0]


def test_dialogflow_webhook_detects_intent_from_text_when_tag_missing() -> None:
    response = client.post(
        "/api/v1/dialogflow/webhook",
        json={
            "languageCode": "en-IN",
            "sessionInfo": {"parameters": {"text": "my cotton leaf has spots"}},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["payload"]["intent"] == "crop_diagnosis"
    assert body["payload"]["should_escalate"] is True


def test_voice_transcribe_and_speak_use_configured_fallback(monkeypatch) -> None:
    calls: list[str] = []

    def google_stt_failure(self, payload, audio):
        calls.append("google_stt")
        raise RuntimeError("google stt unavailable")

    def sarvam_stt_success(self, payload, audio):
        calls.append("sarvam_stt")
        return VoiceTranscribeResponse(
            transcript="Should I irrigate today?",
            language="en-IN",
            provider="sarvam_stt",
            confidence=0.91,
        )

    def google_tts_failure(self, payload):
        calls.append("google_tts")
        raise RuntimeError("google tts unavailable")

    def sarvam_tts_success(self, payload):
        calls.append("sarvam_tts")
        return VoiceSpeakResponse(
            audio_base64=base64.b64encode(b"audio").decode("ascii"),
            provider="sarvam_tts",
            audio_encoding=payload.audio_encoding,
            content_type="audio/mpeg",
        )

    monkeypatch.setattr("app.services.voice_service.VoiceService._transcribe_with_google", google_stt_failure)
    monkeypatch.setattr("app.services.voice_service.VoiceService._transcribe_with_sarvam", sarvam_stt_success)
    monkeypatch.setattr("app.services.voice_service.VoiceService._speak_with_google", google_tts_failure)
    monkeypatch.setattr("app.services.voice_service.VoiceService._speak_with_sarvam", sarvam_tts_success)

    transcribe_response = client.post(
        "/api/v1/voice/transcribe",
        json={
            "audio_base64": base64.b64encode(b"fake wav").decode("ascii"),
            "language": "en-IN",
        },
    )
    assert transcribe_response.status_code == 200
    assert transcribe_response.json()["provider"] == "sarvam_stt"

    speak_response = client.post(
        "/api/v1/voice/speak",
        json={"text": "Avoid spraying before rain.", "language": "en-IN"},
    )
    assert speak_response.status_code == 200
    assert speak_response.json()["provider"] == "sarvam_tts"
    assert calls == ["google_stt", "sarvam_stt", "google_tts", "sarvam_tts"]


def test_translation_and_language_detection_use_configured_fallback(monkeypatch) -> None:
    calls: list[str] = []

    def google_translate_failure(self, payload):
        calls.append("google_translate")
        raise RuntimeError("google translate unavailable")

    def sarvam_translate_success(self, payload):
        calls.append("sarvam_translate")
        return TranslateTextResponse(
            translated_text="आज सिंचाई मत करें।",
            source_language="en-IN",
            target_language="hi-IN",
            provider="sarvam_translate",
        )

    def google_detect_failure(self, payload):
        calls.append("google_detect")
        raise RuntimeError("google detect unavailable")

    def sarvam_detect_success(self, payload):
        calls.append("sarvam_detect")
        return DetectLanguageResponse(
            language="hi-IN",
            script="Deva",
            provider="sarvam_translate",
        )

    monkeypatch.setattr(
        "app.services.translation_service.TranslationService._translate_with_google",
        google_translate_failure,
    )
    monkeypatch.setattr(
        "app.services.translation_service.TranslationService._translate_with_sarvam",
        sarvam_translate_success,
    )
    monkeypatch.setattr(
        "app.services.translation_service.TranslationService._detect_with_google",
        google_detect_failure,
    )
    monkeypatch.setattr(
        "app.services.translation_service.TranslationService._detect_with_sarvam",
        sarvam_detect_success,
    )

    translate_response = client.post(
        "/api/v1/translate/text",
        json={
            "text": "Do not irrigate today.",
            "source_language": "en-IN",
            "target_language": "hi-IN",
        },
    )
    assert translate_response.status_code == 200
    assert translate_response.json()["provider"] == "sarvam_translate"

    detect_response = client.post(
        "/api/v1/translate/detect-language",
        json={"text": "आज सिंचाई मत करें।"},
    )
    assert detect_response.status_code == 200
    assert detect_response.json()["language"] == "hi-IN"
    assert calls == ["google_translate", "sarvam_translate", "google_detect", "sarvam_detect"]


def test_progressive_farmer_identity_reuses_phone_across_channels() -> None:
    first_response = client.post(
        "/api/v1/farmers/identify",
        json={"phone": "+91 99999 99999", "channel": "whatsapp", "language": "hi-IN"},
    )
    assert first_response.status_code == 200
    first = first_response.json()
    assert first["is_new"] is True
    assert "farm_location" in first["missing_fields"]

    second_response = client.post(
        "/api/v1/farmers/identify",
        json={
            "phone": "9999999999",
            "channel": "sms",
            "village": "Demo Village",
            "district": "Guntur",
            "state": "Andhra Pradesh",
            "latitude": 16.3,
            "longitude": 80.4,
        },
    )
    assert second_response.status_code == 200
    second = second_response.json()
    assert second["is_new"] is False
    assert second["farmer"]["id"] == first["farmer"]["id"]
    assert second["farmer"]["phone"] == "919999999999"
    assert "farm_location" not in second["missing_fields"]


def test_weather_context_uses_open_meteo_fallback(monkeypatch) -> None:
    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "current": {
                    "temperature_2m": 31.5,
                    "relative_humidity_2m": 72,
                    "precipitation": 0,
                    "weather_code": 1,
                    "wind_speed_10m": 12,
                },
                "hourly": {
                    "soil_temperature_0cm": [28.2],
                    "soil_moisture_0_to_1cm": [0.21],
                },
                "daily": {
                    "time": ["2026-07-03", "2026-07-04"],
                    "precipitation_sum": [0.0, 7.2],
                    "precipitation_probability_max": [10, 85],
                    "temperature_2m_max": [33.0, 30.0],
                    "temperature_2m_min": [24.0, 23.0],
                    "wind_speed_10m_max": [18.0, 22.0],
                    "et0_fao_evapotranspiration": [5.1, 3.8],
                },
            }

    def fake_get(*args, **kwargs):
        return Response()

    monkeypatch.setattr("app.services.weather_context_service.requests.get", fake_get)
    context = WeatherContextService().get_context(
        WeatherContextRequest(latitude=18.5204, longitude=73.8567, days=2)
    )

    assert context.source == "open_meteo"
    assert context.fallback_used is True
    assert context.daily[1].rainfall_mm == 7.2
    assert context.soil_moisture == 0.21


def test_dry_spell_fetches_weather_when_forecast_missing(monkeypatch) -> None:
    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "current": {
                    "temperature_2m": 36.0,
                    "relative_humidity_2m": 55,
                    "precipitation": 0,
                    "weather_code": 0,
                    "wind_speed_10m": 14,
                },
                "hourly": {
                    "soil_temperature_0cm": [31.0],
                    "soil_moisture_0_to_1cm": [0.16],
                },
                "daily": {
                    "time": [
                        "2026-07-03",
                        "2026-07-04",
                        "2026-07-05",
                        "2026-07-06",
                        "2026-07-07",
                        "2026-07-08",
                        "2026-07-09",
                    ],
                    "precipitation_sum": [0, 0, 0, 0, 0, 1, 0],
                    "precipitation_probability_max": [5, 5, 5, 10, 10, 20, 10],
                    "temperature_2m_max": [36, 37, 37, 36, 35, 34, 34],
                    "temperature_2m_min": [24, 24, 25, 25, 24, 24, 24],
                    "wind_speed_10m_max": [16, 18, 18, 15, 14, 14, 15],
                    "et0_fao_evapotranspiration": [6, 6, 6, 5.8, 5.7, 5.6, 5.5],
                },
            }

    def fake_get(*args, **kwargs):
        return Response()

    monkeypatch.setattr("app.services.weather_context_service.requests.get", fake_get)
    farmer_id = create_demo_farmer()
    response = client.post(
        "/api/v1/advisories/dry-spell",
        json={
            "farmer_id": farmer_id,
            "crop": "maize",
            "soil_moisture": 0.16,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["weather_source"] == "open_meteo"
    assert body["weather_fallback_used"] is True
    assert body["dry_days"] == 7
    assert body["risk_level"] in {"high", "critical"}


def test_dry_spell_uses_satellite_water_stress(monkeypatch) -> None:
    farmer_id = create_demo_farmer()

    def fake_signal(self, **kwargs):
        return SatelliteSignalResponse(
            farmer_id=kwargs["farmer_id"],
            latitude=kwargs["latitude"],
            longitude=kwargs["longitude"],
            geometry_type="point_buffer",
            buffer_m=250,
            start_date="2026-04-05",
            end_date="2026-07-04",
            source="earth_engine_sentinel_2",
            ndvi=0.31,
            ndwi=-0.2,
            ndmi=-0.12,
            evi=0.28,
            ndre=0.16,
            water_stress="high",
            vegetation_status="moderate",
            moisture_status="very_dry",
            chlorophyll_status="low",
            note="Sentinel-2 farm signal.",
        )

    monkeypatch.setattr("app.services.earth_engine_service.EarthEngineService.get_farm_signal", fake_signal)

    response = client.post(
        "/api/v1/advisories/dry-spell",
        json={
            "farmer_id": farmer_id,
            "crop": "maize",
            "rainfall_forecast_mm": [3, 3, 3, 3, 3, 3, 3],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == "medium"
    assert body["irrigation_mm"] == 10
    assert body["satellite_source"] == "earth_engine_sentinel_2"
    assert body["satellite_water_stress"] == "high"
    assert body["satellite_ndwi"] == -0.2
    assert body["satellite_ndmi"] == -0.12
    assert "chlorophyll signal is low" in body["fertilizer_note"]


def test_extension_interfaces_for_data_soil_and_conversation(monkeypatch) -> None:
    farmer_id = create_demo_farmer()

    sources_response = client.get("/api/v1/data/sources")
    assert sources_response.status_code == 200
    assert any("IMD" in f'{item["name"]} {item["provider"]}' for item in sources_response.json())

    def fake_context(self, payload):
        return GovernmentDataContextResponse(
            state=payload.state,
            district=payload.district,
            crop=payload.crop,
            rainfall_normal=DataSignal(
                available=False,
                source="district_rainfall_normals",
                note="No rainfall normal found for district/month.",
            ),
            groundwater=DataSignal(
                available=False,
                source="district_groundwater_level",
                note="No groundwater level found for district.",
            ),
            soil_health=DataSignal(
                available=False,
                source="soil_health_summary",
                note="No soil-health baseline found for district.",
            ),
            crop_history=DataSignal(
                available=False,
                source="crop_production_history",
                note="No crop production/yield history found.",
            ),
            agromet_advisory=DataSignal(
                available=False,
                source="agromet_advisory",
                note="No IMD agromet advisory found for district/crop.",
            ),
            recommended_datasets=[],
            missing_sources=[
                "rainfall_normal",
                "groundwater",
                "soil_health",
                "crop_history",
                "agromet_advisory",
            ],
        )

    monkeypatch.setattr("app.services.bigquery_public_data_service.BigQueryPublicDataService.build_context", fake_context)
    context_response = client.post(
        "/api/v1/data/context",
        json={"state": "Andhra Pradesh", "district": "Guntur", "crop": "chilli", "season": "kharif"},
    )
    assert context_response.status_code == 200
    assert context_response.json()["missing_sources"]
    assert "missing_sources" in context_response.json()

    soil_response = client.post(
        "/api/v1/soil-cards/extract",
        json={
            "farmer_id": farmer_id,
            "extracted_text": "pH 6.8 EC 0.42 organic carbon 0.55 nitrogen medium phosphorus 18 potassium high",
        },
    )
    assert soil_response.status_code == 200
    assert soil_response.json()["ph"] == 6.8

    log_response = client.post(
        "/api/v1/conversations/log",
        json={
            "farmer_id": farmer_id,
            "role": "farmer",
            "text": "Should I irrigate today?",
            "language": "en-IN",
            "channel": "whatsapp",
            "intent": "irrigation_advisory",
        },
    )
    assert log_response.status_code == 200
    assert log_response.json()["saved"] is True

    recent_response = client.get(f"/api/v1/conversations/{farmer_id}")
    assert recent_response.status_code == 200
    assert len(recent_response.json()) == 1


def test_crop_photo_diagnosis_uses_vision_and_creates_expert_ticket(monkeypatch) -> None:
    farmer_id = create_demo_farmer()

    def fake_generate_json(self, provider, prompt, image, mime_type):
        assert image == b"leaf image"
        return (
            {
                "likely_issue": "Possible leaf blight",
                "confidence": 0.84,
                "severity": "high",
                "immediate_action": "Isolate affected leaves and request expert validation.",
                "needs_expert_followup": True,
            },
            "gemini-2.5-flash",
        )

    monkeypatch.setattr("app.services.vision_ocr_service.settings.enable_google_integrations", True)
    monkeypatch.setattr("app.services.vision_ocr_service.VisionOcrService._generate_json", fake_generate_json)

    response = client.post(
        "/api/v1/diagnosis/log",
        json={
            "farmer_id": farmer_id,
            "crop": "chilli",
            "symptoms_text": "spots on leaves",
            "image_base64": base64.b64encode(b"leaf image").decode("ascii"),
            "mime_type": "image/jpeg",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "vertex_ai_vision"
    assert body["likely_issue"] == "Possible leaf blight"
    assert body["expert_ticket"]["issue"] == "Possible leaf blight"


def test_soil_card_image_extraction_uses_vision(monkeypatch) -> None:
    def fake_generate_json(self, provider, prompt, image, mime_type):
        assert image == b"soil card image"
        return (
            {
                "ph": 6.7,
                "ec": 0.38,
                "organic_carbon": 0.52,
                "nitrogen": "medium",
                "phosphorus": 18,
                "potassium": "high",
                "micronutrients": {"zinc": "low"},
                "confidence": 0.88,
                "needs_manual_review": False,
                "raw_text": "pH 6.7 EC 0.38 OC 0.52",
            },
            "gemini-2.5-flash",
        )

    monkeypatch.setattr("app.services.vision_ocr_service.VisionOcrService._generate_json", fake_generate_json)

    response = client.post(
        "/api/v1/soil-cards/extract",
        json={
            "image_base64": base64.b64encode(b"soil card image").decode("ascii"),
            "mime_type": "image/jpeg",
            "language": "en-IN",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "vertex_ai_vision"
    assert body["ph"] == 6.7
    assert body["micronutrients"]["zinc"] == "low"


def test_soil_card_extraction_persists_to_farmer_profile() -> None:
    response = client.post(
        "/api/v1/farmers",
        json={
            "name": "Lakshmi",
            "phone": "9888888888",
            "language": "te-IN",
            "village": "Demo Village",
            "district": "Guntur",
            "state": "Andhra Pradesh",
            "farm": {
                "area_acres": 1.5,
                "soil_type": "unknown",
                "groundwater_depth_m": 20,
                "latitude": 16.3,
                "longitude": 80.4,
            },
        },
    )
    assert response.status_code == 200
    farmer_id = response.json()["id"]

    extraction_response = client.post(
        "/api/v1/soil-cards/extract",
        json={
            "farmer_id": farmer_id,
            "extracted_text": (
                "Black soil pH 6.4 EC 0.2 organic carbon 0.55 "
                "nitrogen medium phosphorus low potassium high"
            ),
        },
    )

    assert extraction_response.status_code == 200
    body = extraction_response.json()
    assert body["persisted"] is True
    assert body["farmer"]["farm"]["soil_type"] == "black"
    assert body["farmer"]["farm"]["soil_ph"] == 6.4
    assert body["farmer"]["farm"]["soil_nitrogen"] == "medium"
    assert body["farmer"]["farm"]["soil_phosphorus"] == "low"
    assert body["farmer"]["farm"]["soil_potassium"] == "high"

    saved = store.get_farmer(farmer_id)
    assert saved is not None
    assert saved.farm.soil_type == "black"
    assert saved.farm.soil_ph == 6.4

    recommendation_response = client.post(
        "/api/v1/recommendations/crop",
        json={
            "farmer_id": farmer_id,
            "season": "kharif",
            "expected_rainfall_mm": 620,
            "water_availability": "medium",
        },
    )
    assert recommendation_response.status_code == 200
    data_sources = recommendation_response.json()["data_sources"]
    assert data_sources["soil"] == "farmer_profile"
    assert data_sources["soilPh"] == 6.4


def test_bigquery_public_context_maps_available_signals() -> None:
    class Row(dict):
        def items(self):
            return super().items()

    class QueryResult:
        def __init__(self, rows):
            self.rows = rows

        def result(self):
            return self.rows

    class Client:
        def query(self, query, job_config=None):
            if "district_rainfall_normals" in query:
                return QueryResult([Row(normal_rainfall_mm=640.5, source_name="IMD rainfall normals")])
            if "district_groundwater_level" in query:
                return QueryResult(
                    [Row(groundwater_depth_m=18.2, category="safe", source_name="Groundwater Board")]
                )
            if "soil_health_summary" in query:
                return QueryResult(
                    [
                        Row(
                            ph=6.8,
                            organic_carbon=0.55,
                            nitrogen="medium",
                            phosphorus="medium",
                            potassium="high",
                            source_name="Soil Health Card",
                        )
                    ]
                )
            if "crop_production_history" in query:
                return QueryResult([Row(yield_kg_per_hectare=2400, crop_year=2024, source_name="UPAg")])
            if "agromet_advisory" in query:
                return QueryResult(
                    [
                        Row(
                            advisory_text="Avoid spraying before heavy rain.",
                            bulletin_date="2026-07-03",
                            source_name="IMD Agromet",
                        )
                    ]
                )
            return QueryResult([])

    context = BigQueryPublicDataService(client=Client()).build_context(
        GovernmentDataContextRequest(
            state="Andhra Pradesh",
            district="Guntur",
            crop="chilli",
            season="kharif",
            month=7,
        )
    )

    assert context.rainfall_normal.available is True
    assert context.groundwater.value == 18.2
    assert context.soil_health.available is True
    assert context.crop_history.value == 2400.0
    assert context.agromet_advisory.available is True
    assert context.missing_sources == []
    assert context.rainfall_normal.metadata["month"] == 7
    assert context.soil_health.metadata["ph"] == 6.8


def test_bigquery_public_data_ingestion_loads_normalized_csv(tmp_path) -> None:
    class Job:
        def result(self):
            return None

    class Client:
        def __init__(self):
            self.loaded_rows = []
            self.run_rows = []
            self.table_id = None

        def load_table_from_json(self, rows, table_id, job_config=None):
            self.loaded_rows.extend(rows)
            self.table_id = table_id
            return Job()

        def insert_rows_json(self, table_id, rows):
            self.run_rows.extend(rows)
            return []

    csv_path = tmp_path / "rainfall_normals.csv"
    csv_path.write_text(
        "state,district,month,normal_rainfall_mm\n"
        "Andhra Pradesh,Guntur,7,640.5\n",
        encoding="utf-8",
    )
    client = Client()

    result = PublicDataIngestionService(client=client).ingest_csv(
        source_key="rainfall_normals",
        csv_path=csv_path,
        source_name="IMD rainfall normals",
        source_url="https://dsp.imdpune.gov.in/",
        source_file_uri="gs://bucket/raw/imd/rainfall_normals.csv",
    )

    assert result.status == "success"
    assert result.records_loaded == 1
    assert client.table_id.endswith(".kisan_ai_curated.district_rainfall_normals")
    assert client.loaded_rows[0]["month"] == 7
    assert client.loaded_rows[0]["normal_rainfall_mm"] == 640.5
    assert client.loaded_rows[0]["source_name"] == "IMD rainfall normals"
    assert [row["status"] for row in client.run_rows] == ["running", "success"]


def test_bigquery_public_data_ingestion_validates_required_columns(tmp_path) -> None:
    class Client:
        def insert_rows_json(self, table_id, rows):
            return []

    csv_path = tmp_path / "bad_groundwater.csv"
    csv_path.write_text("state,groundwater_depth_m\nMaharashtra,18.2\n", encoding="utf-8")

    try:
        PublicDataIngestionService(client=Client()).ingest_csv(
            source_key="groundwater_level",
            csv_path=csv_path,
            source_name="Groundwater sample",
        )
    except ValueError as exc:
        assert "district" in str(exc)
    else:
        raise AssertionError("Expected required-column validation to fail")


def test_advisory_generation_prefers_vertex_and_falls_back_to_gemini(monkeypatch) -> None:
    calls: list[str] = []

    def vertex_failure(self, payload):
        calls.append("vertex")
        raise RuntimeError("temporary vertex failure")

    def gemini_success(self, payload):
        calls.append("gemini")
        return AdvisoryTestResponse(
            source="gemini",
            model="gemini-2.5-flash",
            advisory_text="Keep drainage open before heavy rain.",
            risk_level=RiskLevel.high,
            recommended_actions=["Avoid spraying before rain."],
        )

    monkeypatch.setattr(
        "app.services.gemini_service.GeminiService._generate_advisory_with_vertex",
        vertex_failure,
    )
    monkeypatch.setattr(
        "app.services.gemini_service.GeminiService._generate_advisory_with_gemini",
        gemini_success,
    )

    response = client.post(
        "/api/v1/advisory/test",
        json={
            "farmer_name": "Ravi",
            "language": "te-IN",
            "crop": "cotton",
            "crop_stage": "vegetative",
            "location": "Guntur",
            "weather_summary": "Heavy rain likely.",
            "rainfall_forecast_mm": 50,
        },
    )

    assert response.status_code == 200
    assert response.json()["source"] == "gemini"
    assert calls == ["vertex", "gemini"]


def test_farmer_advisories_include_ai_source_when_google_enabled(monkeypatch) -> None:
    farmer_id = create_demo_farmer()

    def ai_success(self, payload):
        return AdvisoryTestResponse(
            source="vertex_ai",
            model="gemini-2.5-flash",
            advisory_text=f"AI advice for {payload.crop}: irrigate carefully.",
            risk_level=RiskLevel.medium,
            recommended_actions=["Irrigate in the evening.", "Check soil moisture first."],
        )

    monkeypatch.setattr(
        "app.services.weather_service.settings.enable_google_integrations",
        True,
    )
    monkeypatch.setattr(
        "app.services.crop_stage_advisory_service.settings.enable_google_integrations",
        True,
    )
    monkeypatch.setattr(
        "app.services.gemini_service.GeminiService.generate_test_advisory",
        ai_success,
    )

    dry_spell_response = client.post(
        "/api/v1/advisories/dry-spell",
        json={
            "farmer_id": farmer_id,
            "crop": "maize",
            "soil_moisture": 0.16,
            "rainfall_forecast_mm": [0, 0, 0, 0, 0, 1, 0],
        },
    )
    assert dry_spell_response.status_code == 200
    assert dry_spell_response.json()["ai_source"] == "vertex_ai"
    assert dry_spell_response.json()["advisory"].startswith("AI advice")

    stage_response = client.post(
        "/api/v1/advisories/crop-stage",
        json={
            "farmer_id": farmer_id,
            "crop": "maize",
            "stage": "flowering",
            "rainfall_forecast_mm": [0, 0, 0, 0, 1, 0, 2],
            "humidity_percent": 88,
            "soil_moisture": 0.19,
        },
    )
    assert stage_response.status_code == 200
    assert stage_response.json()["ai_source"] == "vertex_ai"
    assert stage_response.json()["actions"] == ["Irrigate in the evening.", "Check soil moisture first."]


def test_crop_stage_advisory_uses_satellite_water_and_chlorophyll_status(monkeypatch) -> None:
    farmer_id = create_demo_farmer()

    def fake_signal(self, **kwargs):
        return SatelliteSignalResponse(
            farmer_id=kwargs["farmer_id"],
            latitude=kwargs["latitude"],
            longitude=kwargs["longitude"],
            geometry_type="point_buffer",
            buffer_m=250,
            start_date="2026-04-05",
            end_date="2026-07-04",
            source="earth_engine_sentinel_2",
            ndvi=0.34,
            ndwi=-0.22,
            ndmi=-0.14,
            evi=0.29,
            ndre=0.15,
            water_stress="high",
            vegetation_status="moderate",
            moisture_status="very_dry",
            chlorophyll_status="low",
            note="Sentinel-2 farm signal.",
        )

    monkeypatch.setattr("app.services.earth_engine_service.EarthEngineService.get_farm_signal", fake_signal)

    response = client.post(
        "/api/v1/advisories/crop-stage",
        json={
            "farmer_id": farmer_id,
            "crop": "maize",
            "stage": "flowering",
            "rainfall_forecast_mm": [3, 3, 3, 3, 3, 3, 3],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["risk_level"] == "high"
    assert body["data_used"]["satelliteWaterStress"] == "high"
    assert body["data_used"]["satelliteNdmi"] == -0.14
    assert body["data_used"]["satelliteChlorophyllStatus"] == "low"
    assert any("Satellite moisture signal" in action for action in body["actions"])
    assert any("Satellite chlorophyll signal" in action for action in body["actions"])


def test_crop_recommendation_uses_public_context_when_rainfall_is_missing(monkeypatch) -> None:
    farmer_response = client.post(
        "/api/v1/farmers",
        json={
            "name": "Ravi",
            "phone": "9999999998",
            "language": "te-IN",
            "village": "Demo Village",
            "district": "Guntur",
            "state": "Andhra Pradesh",
            "farm": {
                "area_acres": 2.5,
                "soil_type": "black",
            },
        },
    )
    assert farmer_response.status_code == 200

    def fake_context(self, payload):
        return GovernmentDataContextResponse(
            state=payload.state,
            district=payload.district,
            crop=payload.crop,
            rainfall_normal=DataSignal(
                available=True,
                source="district_rainfall_normals",
                value=640.0,
                unit="mm",
                metadata={"month": payload.month},
            ),
            groundwater=DataSignal(
                available=True,
                source="district_groundwater_level",
                value=18.0,
                unit="m",
                metadata={"groundwater_depth_m": 18.0},
            ),
            soil_health=DataSignal(
                available=True,
                source="soil_health_summary",
                value="pH 6.8",
                metadata={"ph": 6.8},
            ),
            crop_history=DataSignal(available=False, source="crop_production_history"),
            agromet_advisory=DataSignal(available=False, source="agromet_advisory"),
            recommended_datasets=[],
            missing_sources=["crop_history", "agromet_advisory"],
        )

    monkeypatch.setattr("app.services.bigquery_public_data_service.BigQueryPublicDataService.build_context", fake_context)

    response = client.post(
        "/api/v1/recommendations/crop",
        json={
            "farmer_id": farmer_response.json()["id"],
            "season": "kharif",
            "month": 7,
            "ndvi": 0.4,
            "water_availability": "medium",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["recommendations"]) == 3
    assert body["data_sources"]["rainfall"] == 640.0
    assert body["data_sources"]["rainfallSource"] == "district_rainfall_normals"
    assert body["data_sources"]["groundwaterDepthM"] == 18.0


def test_satellite_farm_signal_accepts_farmer_profile_and_polygon(monkeypatch) -> None:
    farmer_id = create_demo_farmer()

    def fake_signal(self, **kwargs):
        assert kwargs["farmer_id"] == farmer_id
        assert kwargs["latitude"] == 16.3
        assert len(kwargs["polygon"]) == 3
        return SatelliteSignalResponse(
            farmer_id=kwargs["farmer_id"],
            latitude=kwargs["latitude"],
            longitude=kwargs["longitude"],
            geometry_type="polygon",
            start_date="2026-04-05",
            end_date="2026-07-04",
            source="earth_engine_sentinel_2",
            ndvi=0.52,
            ndwi=-0.04,
            ndmi=0.08,
            evi=0.46,
            ndre=0.35,
            water_stress="medium",
            vegetation_status="healthy",
            moisture_status="dry",
            chlorophyll_status="good",
            history=[
                SatelliteHistoryPoint(
                    start_date="2026-04-05",
                    end_date="2026-05-05",
                    ndvi=0.42,
                    ndwi=-0.1,
                    ndmi=0.04,
                    evi=0.36,
                    ndre=0.28,
                    water_stress="medium",
                )
            ],
            note="Sentinel-2 farm signal.",
        )

    monkeypatch.setattr("app.services.earth_engine_service.EarthEngineService.get_farm_signal", fake_signal)

    response = client.post(
        "/api/v1/satellite/farm-signal",
        json={
            "farmer_id": farmer_id,
            "polygon": [
                {"latitude": 16.3, "longitude": 80.4},
                {"latitude": 16.301, "longitude": 80.4},
                {"latitude": 16.301, "longitude": 80.401},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "earth_engine_sentinel_2"
    assert body["geometry_type"] == "polygon"
    assert body["ndvi"] == 0.52
    assert body["ndwi"] == -0.04
    assert body["ndmi"] == 0.08
    assert body["evi"] == 0.46
    assert body["ndre"] == 0.35
    assert body["water_stress"] == "medium"
    assert body["moisture_status"] == "dry"
    assert body["chlorophyll_status"] == "good"
    assert body["history"][0]["ndvi"] == 0.42
    assert body["history"][0]["ndmi"] == 0.04


def test_crop_recommendation_uses_earth_engine_farm_signal(monkeypatch) -> None:
    farmer_id = create_demo_farmer()

    def fake_signal(self, **kwargs):
        assert kwargs["farmer_id"] == farmer_id
        return SatelliteSignalResponse(
            farmer_id=kwargs["farmer_id"],
            latitude=kwargs["latitude"],
            longitude=kwargs["longitude"],
            geometry_type="point_buffer",
            buffer_m=250,
            start_date="2026-04-05",
            end_date="2026-07-04",
            source="earth_engine_sentinel_2",
            ndvi=0.36,
            ndwi=-0.18,
            ndmi=-0.11,
            evi=0.3,
            ndre=0.21,
            water_stress="high",
            vegetation_status="moderate",
            moisture_status="very_dry",
            chlorophyll_status="medium",
            note="Sentinel-2 farm signal.",
        )

    monkeypatch.setattr("app.services.earth_engine_service.EarthEngineService.get_farm_signal", fake_signal)

    response = client.post(
        "/api/v1/recommendations/crop",
        json={
            "farmer_id": farmer_id,
            "season": "kharif",
            "expected_rainfall_mm": 620,
            "water_availability": "medium",
        },
    )

    assert response.status_code == 200
    data_sources = response.json()["data_sources"]
    assert data_sources["ndvi"] == 0.36
    assert data_sources["ndwi"] == -0.18
    assert data_sources["ndmi"] == -0.11
    assert data_sources["evi"] == 0.3
    assert data_sources["ndre"] == 0.21
    assert data_sources["waterStress"] == "high"
    assert data_sources["vegetationStatus"] == "moderate"
    assert data_sources["moistureStatus"] == "very_dry"
    assert data_sources["chlorophyllStatus"] == "medium"
    assert data_sources["satellite"] == "earth_engine_sentinel_2"


def test_provider_config_can_be_switched_by_feature() -> None:
    config_response = client.get("/api/v1/providers/config")
    assert config_response.status_code == 200
    routes = {item["feature"]: item for item in config_response.json()["routes"]}
    assert routes["weather"]["primary"] == "imd"
    assert routes["weather"]["secondary"] == "open_meteo"
    assert routes["llm_advisory"]["primary"] == "vertex_ai"
    assert routes["llm_advisory"]["secondary"] == "gemini"
    assert routes["vision_ocr"]["primary"] == "vertex_ai_vision"
    assert routes["vision_ocr"]["secondary"] == "gemini_vision"
    assert routes["satellite"]["primary"] == "earth_engine"
    assert routes["satellite"]["allow_fallback"] is False

    update_response = client.patch(
        "/api/v1/providers/config",
        json={
            "routes": {
                "weather": {
                    "primary": "open_meteo",
                    "secondary": "imd",
                    "note": "Temporary demo switch.",
                }
            }
        },
    )
    assert update_response.status_code == 200
    updated = {item["feature"]: item for item in update_response.json()["routes"]}
    assert updated["weather"]["primary"] == "open_meteo"
    assert updated["weather"]["secondary"] == "imd"

    invalid_response = client.patch(
        "/api/v1/providers/config",
        json={"routes": {"satellite": {"primary": "earth_engine", "secondary": "osm_nominatim"}}},
    )
    assert invalid_response.status_code == 400
