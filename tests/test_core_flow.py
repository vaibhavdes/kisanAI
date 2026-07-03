import os

os.environ["DATA_STORE_PROVIDER"] = "local"

from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import WeatherContextRequest
from app.repositories.store import store
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


def test_extension_interfaces_for_data_soil_and_conversation() -> None:
    farmer_id = create_demo_farmer()

    sources_response = client.get("/api/v1/data/sources")
    assert sources_response.status_code == 200
    assert any("IMD" in f'{item["name"]} {item["provider"]}' for item in sources_response.json())

    context_response = client.post(
        "/api/v1/data/context",
        json={"state": "Andhra Pradesh", "district": "Guntur", "crop": "chilli", "season": "kharif"},
    )
    assert context_response.status_code == 200
    assert context_response.json()["recommended_datasets"]

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


def test_provider_config_can_be_switched_by_feature() -> None:
    config_response = client.get("/api/v1/providers/config")
    assert config_response.status_code == 200
    routes = {item["feature"]: item for item in config_response.json()["routes"]}
    assert routes["weather"]["primary"] == "imd"
    assert routes["weather"]["secondary"] == "open_meteo"
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
