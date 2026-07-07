import re
from datetime import UTC, datetime

from app.core.config import settings
from app.models.schemas import (
    ConversationLogRequest,
    ConversationRole,
    CropRecommendationRequest,
    DiagnosisRequest,
    FarmerIdentifyRequest,
    FarmerResponse,
    GovernmentDataContextRequest,
    DetectLanguageRequest,
    DrySpellAdvisoryRequest,
    RiskLevel,
    SoilCardExtractionRequest,
    SoilCardExtractionResponse,
    WaterAvailability,
    WeatherContextRequest,
    VoiceSpeakRequest,
    VoiceIntakeRequest,
    VoiceTranscribeRequest,
    WhatsAppWebhookRequest,
    WhatsAppWebhookResponse,
)
from app.repositories.store import store
from app.services.channel_intent import detect_farmer_intent, is_crop_followup_text, is_water_followup_text
from app.services.conversation_store import ConversationStore
from app.services.dialogflow_channel_service import DialogflowChannelService, DialogflowChannelUnavailable
from app.services.earth_engine_service import EarthEngineService
from app.services.expert_service import ExpertService
from app.services.geocoding_service import GeocodingProviderUnavailable, GeocodingService, LocationResolution
from app.services.bigquery_public_data_service import BigQueryPublicDataService
from app.services.gemini_service import AdvisoryProviderUnavailable, GeminiService
from app.services.recommendation_engine import RecommendationEngine
from app.services.sensor_service import SensorService
from app.services.soil_card_vision_service import SoilCardVisionService
from app.services.translation_service import TranslationProviderUnavailable, TranslationService
from app.services.vision_ocr_service import VisionOcrService, VisionProviderUnavailable
from app.services.weather_context_service import WeatherContextService, WeatherProviderUnavailable
from app.services.weather_service import WeatherService
from app.services.voice_service import VoiceProviderUnavailable, VoiceService
from app.utils.language import infer_message_language, phrase


class WhatsAppService:
    def handle_message(
        self,
        payload: WhatsAppWebhookRequest,
        *,
        channel: str = "whatsapp",
        send_outbound: bool = True,
    ) -> WhatsAppWebhookResponse:
        existing_farmer = store.get_farmer_by_phone(payload.from_phone)
        requested_language = self._requested_language(payload.language)
        inferred_language = infer_message_language(payload.text)
        detected_language = self._detect_language(payload.text) if not requested_language and not inferred_language else None
        response_language = requested_language or inferred_language or detected_language or (existing_farmer.language if existing_farmer else None) or settings.default_language
        identity = store.identify_farmer(
            FarmerIdentifyRequest(
                phone=payload.from_phone,
                channel=channel,
                language=response_language if existing_farmer is None else None,
                latitude=payload.latitude,
                longitude=payload.longitude,
            )
        )
        farmer = identity.farmer

        transcript = self._transcribe_voice(payload, response_language)
        text = transcript or payload.text
        media_uri_for_intent = None if transcript else payload.media_uri
        media_type_for_intent = None if transcript else payload.media_type
        intent = detect_farmer_intent(
            text,
            media_uri_for_intent,
            media_type=media_type_for_intent,
            has_location=payload.latitude is not None and payload.longitude is not None,
        )
        intent, intent_ai_meta = self._refine_intent_with_ai(
            farmer.id,
            channel,
            response_language,
            text,
            intent,
            payload,
        )
        intent = self._intent_with_context(farmer.id, text, intent)

        dialogflow_response = self._dialogflow_response(payload, farmer.id, response_language, text, transcript, intent)
        if dialogflow_response:
            dialogflow_response.data_sources.update(intent_ai_meta)
            dialogflow_response.farmer_id = farmer.id
            dialogflow_response.detected_language = response_language
            dialogflow_response.missing_fields = identity.missing_fields
            self._log_farmer_message(
                farmer.id,
                text or self._message_summary(payload),
                response_language,
                dialogflow_response.intent,
                payload,
                channel,
            )
            if send_outbound:
                dialogflow_response.outbound_provider, dialogflow_response.delivery_status = self._send_whatsapp_reply(
                    payload.from_phone,
                    dialogflow_response.reply,
                    dialogflow_response.template_name,
                )
            else:
                dialogflow_response.delivery_status = "app_response"
            self._attach_audio(farmer.id, dialogflow_response, response_language)
            self._log_assistant_message(
                farmer.id,
                dialogflow_response.reply,
                response_language,
                dialogflow_response.intent,
                dialogflow_response,
                channel,
            )
            return dialogflow_response

        self._log_farmer_message(farmer.id, text or self._message_summary(payload), response_language, intent, payload, channel)
        response = self._build_response(payload, farmer.id, response_language, text, transcript, intent, channel)
        response.data_sources.update(intent_ai_meta)
        response.farmer_id = farmer.id
        response.detected_language = response_language
        response.missing_fields = identity.missing_fields
        self._naturalize_response(response, farmer.id, response_language, text or "", channel)
        self._attach_day_start_bulletin(response, farmer, response_language, channel)

        if not self._should_skip_voice_attachment(response, channel):
            self._attach_audio(farmer.id, response, response_language)

        if send_outbound:
            response.outbound_provider, response.delivery_status = self._send_whatsapp_reply(
                payload.from_phone,
                response.reply,
                response.template_name,
                response.media_url,
            )
        else:
            response.delivery_status = "app_response"
        self._log_assistant_message(farmer.id, response.reply, response_language, response.intent, response, channel)
        return response

    def _build_response(
        self,
        payload: WhatsAppWebhookRequest,
        farmer_id: str,
        language: str,
        text: str | None,
        transcript: str | None,
        intent: str,
        channel: str,
    ) -> WhatsAppWebhookResponse:
        farmer = store.get_farmer(farmer_id)
        if not farmer:
            return WhatsAppWebhookResponse(intent="unknown", reply=phrase("sms_unknown", language))

        self._capture_profile_facts(farmer, text)
        farmer = store.get_farmer(farmer_id) or farmer

        if intent == "crop_planning" or (intent != "crop_recommendation" and self._is_crop_planning_text(text)):
            return self._crop_planning_response(farmer, language, text, transcript)

        if intent == "location_update":
            response = self._handle_coordinate_location(payload, farmer, language, transcript)
            return response

        location_from_text = self._location_from_text(text)
        if location_from_text and intent in {"general_advisory", "unknown", "weather_query", "crop_recommendation", "irrigation_advisory"}:
            farmer = GeocodingService().apply_to_farmer(farmer, location_from_text)
            previous_intent = self._last_active_intent(farmer_id)
            if intent == "weather_query" or previous_intent == "weather_query":
                return self._weather_response(farmer, language, transcript)
            if intent == "crop_recommendation" or previous_intent == "crop_recommendation":
                return self._crop_recommendation_response(farmer, language, text, transcript)
            return WhatsAppWebhookResponse(
                intent="location_update",
                reply=self._location_saved_reply(language, location_from_text),
                template_name="location_saved",
                transcript=transcript,
                data_sources={"geocoding": location_from_text.source},
                stored_context=self._stored_context(farmer),
            )

        if intent == "voice_message":
            return self._voice_intake_response(farmer_id, language, text or "", transcript, payload)

        if intent == "document_message":
            return WhatsAppWebhookResponse(
                intent=intent,
                reply=phrase("whatsapp_document_received", language),
                template_name="document_received",
                transcript=transcript,
            )

        if intent in {"greeting", "general_advisory"}:
            if self._needs_name(farmer):
                return WhatsAppWebhookResponse(
                    intent="general_advisory",
                    reply=phrase("first_greeting_name", language),
                    template_name="ask_name_first",
                    transcript=transcript,
                    stored_context=self._stored_context(farmer),
                )
            name = self._display_name(farmer.name if farmer else "Farmer", language)
            ticket_status = self._open_ticket_status(farmer_id, language)
            reply = phrase("general_response", language, name=name)
            if ticket_status:
                reply = f"{reply}\n\n{ticket_status}"
            return WhatsAppWebhookResponse(
                intent="general_advisory",
                reply=reply,
                template_name="friendly_start",
                transcript=transcript,
                stored_context=self._stored_context(farmer),
            )

        if intent == "identity_query":
            farmer = store.get_farmer(farmer_id)
            name = self._display_name(farmer.name if farmer else "Farmer", language)
            return WhatsAppWebhookResponse(
                intent=intent,
                reply=phrase("identity_response", language, name=name),
                template_name="identity_reply",
                transcript=transcript,
            )

        if intent == "weather_query":
            return self._weather_response(farmer, language, transcript)

        if intent == "satellite_advisory":
            return self._satellite_response(farmer, language, transcript)

        if intent == "crop_diagnosis":
            if payload.media_uri or payload.media_base64:
                return self._image_response(payload, farmer_id, language, text, transcript)
            return WhatsAppWebhookResponse(
                intent=intent,
                reply=phrase("sms_photo", language),
                template_name="crop_photo_followup",
                transcript=transcript,
            )

        if intent == "irrigation_advisory":
            if self._last_active_intent(farmer_id) == "irrigation_advisory" and is_water_followup_text(text):
                return WhatsAppWebhookResponse(
                    intent=intent,
                    reply=phrase("water_followup_ack", language),
                    template_name="water_followup",
                    transcript=transcript,
                )
            return self._irrigation_response(farmer, language, text, transcript, payload)

        if intent == "crop_recommendation":
            if self._is_crop_detail_followup(text):
                self._capture_profile_facts(farmer, text)
                farmer = store.get_farmer(farmer_id) or farmer
            return self._crop_recommendation_response(farmer, language, text, transcript)

        return WhatsAppWebhookResponse(
            intent=intent,
            reply=phrase("sms_unknown", language),
            template_name="main_menu",
            transcript=transcript,
        )

    def _dialogflow_response(
        self,
        payload: WhatsAppWebhookRequest,
        farmer_id: str,
        language: str,
        text: str | None,
        transcript: str | None,
        local_intent: str,
    ) -> WhatsAppWebhookResponse | None:
        if local_intent in {"greeting", "identity_query", "weather_query", "unknown"}:
            return None
        if not text:
            return None
        if payload.latitude is not None or payload.longitude is not None:
            return None
        if payload.media_type in {"image", "photo", "document"} or payload.media_uri or payload.media_base64:
            return None
        try:
            result = DialogflowChannelService().route_text(
                text=text,
                language=language,
                session_id=f"whatsapp-{farmer_id}",
                parameters={
                    "phone": payload.from_phone,
                    "from_phone": payload.from_phone,
                    "farmer_id": farmer_id,
                    "language": language,
                    "text": text,
                },
            )
        except DialogflowChannelUnavailable:
            return None
        if not result.reply:
            return None
        if self._is_stale_menu_reply(result.reply):
            return None
        if local_intent not in {"general_advisory", "unknown"} and result.intent != local_intent:
            return None
        return WhatsAppWebhookResponse(
            intent=result.intent,
            reply=result.reply,
            template_name="dialogflow_reply",
            transcript=transcript,
        )

    def _handle_coordinate_location(
        self,
        payload: WhatsAppWebhookRequest,
        farmer: FarmerResponse,
        language: str,
        transcript: str | None,
    ) -> WhatsAppWebhookResponse:
        if payload.latitude is None or payload.longitude is None:
            return WhatsAppWebhookResponse(
                intent="location_update",
                reply=phrase("weather_response", language),
                template_name="location_missing_coordinates",
                transcript=transcript,
            )
        resolution = GeocodingService().resolve_coordinates(payload.latitude, payload.longitude)
        if payload.location_label and not resolution.formatted_address:
            resolution = LocationResolution(**{**resolution.__dict__, "formatted_address": payload.location_label})
        farmer = GeocodingService().apply_to_farmer(farmer, resolution)
        return WhatsAppWebhookResponse(
            intent="location_update",
            reply=self._location_saved_reply(language, resolution),
            template_name="location_saved",
            transcript=transcript,
            data_sources={"geocoding": resolution.source},
            stored_context=self._stored_context(farmer),
        )

    def _weather_response(
        self,
        farmer: FarmerResponse,
        language: str,
        transcript: str | None,
    ) -> WhatsAppWebhookResponse:
        if farmer.farm.latitude is None or farmer.farm.longitude is None:
            public_context = self._public_context(farmer, crop=None)
            if public_context:
                reply = phrase(
                    "weather_public_context",
                    language,
                    location=self._location_label(farmer),
                    rainfall=public_context.rainfall_normal.value or "unknown",
                    source=public_context.rainfall_normal.source,
                )
                return WhatsAppWebhookResponse(
                    intent="weather_query",
                    reply=reply,
                    template_name="weather_public_context",
                    transcript=transcript,
                    data_sources={"rainfall": public_context.rainfall_normal.source},
                    stored_context=self._stored_context(farmer),
                )
            return WhatsAppWebhookResponse(
                intent="weather_query",
                reply=phrase("weather_need_location", language),
                template_name="weather_need_location",
                transcript=transcript,
                stored_context=self._stored_context(farmer),
            )
        warnings: list[str] = []
        try:
            weather = WeatherContextService().get_context(
                WeatherContextRequest(latitude=farmer.farm.latitude, longitude=farmer.farm.longitude)
            )
            rainfall_3d = sum((day.rainfall_mm or 0) for day in weather.daily[:3])
            rainfall_7d = sum((day.rainfall_mm or 0) for day in weather.daily[:7])
            reply = phrase(
                "weather_answer",
                language,
                location=self._location_label(farmer),
                temp=weather.current_temperature_c if weather.current_temperature_c is not None else "unknown",
                humidity=weather.current_humidity_percent if weather.current_humidity_percent is not None else "unknown",
                rain3=round(rainfall_3d, 1),
                rain7=round(rainfall_7d, 1),
                source=weather.source.value,
            )
            if weather.fallback_used:
                warnings.append("Primary weather provider failed; fallback provider was used.")
            return WhatsAppWebhookResponse(
                intent="weather_query",
                reply=reply,
                template_name="weather_answer",
                transcript=transcript,
                data_sources={
                    "weather": weather.source.value,
                    "fallbackUsed": weather.fallback_used,
                    "rainfall3DayMm": round(rainfall_3d, 1),
                    "rainfall7DayMm": round(rainfall_7d, 1),
                },
                service_warnings=warnings + self._provider_warnings(weather.provider_statuses),
                stored_context=self._stored_context(farmer),
            )
        except WeatherProviderUnavailable as exc:
            return WhatsAppWebhookResponse(
                intent="weather_query",
                reply=phrase("weather_failed", language, location=self._location_label(farmer)),
                template_name="weather_failed",
                transcript=transcript,
                service_warnings=[str(exc)],
                stored_context=self._stored_context(farmer),
            )

    def _satellite_response(
        self,
        farmer: FarmerResponse,
        language: str,
        transcript: str | None,
    ) -> WhatsAppWebhookResponse:
        if farmer.farm.latitude is None or farmer.farm.longitude is None:
            return WhatsAppWebhookResponse(
                intent="satellite_advisory",
                reply=self._localized_location_needed(language, "whatsapp"),
                template_name="satellite_need_location",
                transcript=transcript,
                stored_context=self._stored_context(farmer),
            )
        try:
            signal = WeatherService()._satellite_signal(farmer)
        except Exception as exc:
            return WhatsAppWebhookResponse(
                intent="satellite_advisory",
                reply=phrase("weather_failed", language, location=self._location_label(farmer)),
                template_name="satellite_failed",
                transcript=transcript,
                service_warnings=[f"Earth Engine satellite signal failed: {exc}"],
                stored_context=self._stored_context(farmer),
            )
        if not signal:
            return WhatsAppWebhookResponse(
                intent="satellite_advisory",
                reply=phrase("weather_failed", language, location=self._location_label(farmer)),
                template_name="satellite_unavailable",
                transcript=transcript,
                service_warnings=["Earth Engine satellite signal unavailable."],
                stored_context=self._stored_context(farmer),
            )
        crop = self._crop_label(farmer.active_crop or "crop", language)
        planted = farmer.active_crop_planted_at or "unknown"
        variety = farmer.active_crop_variety or "unknown"
        growth_status = self._localized_satellite_status(signal.vegetation_status, language)
        water_status = self._localized_satellite_status(signal.water_stress, language)
        moisture_status = self._localized_satellite_status(signal.moisture_status, language)
        chlorophyll_status = self._localized_satellite_status(signal.chlorophyll_status, language)
        action = self._satellite_farmer_action(signal, language)
        technical = self._satellite_technical_line(signal)
        media_url = None
        media_content_type = None
        preview_sources: dict[str, str | float | int | bool | None] = {}
        preview_warnings: list[str] = []
        try:
            preview = EarthEngineService().get_farm_map_preview(
                farmer_id=farmer.id,
                latitude=farmer.farm.latitude,
                longitude=farmer.farm.longitude,
                buffer_m=250,
                days=90,
                index="NDMI",
            )
            media_url = preview.map_url
            media_content_type = "image/png"
            preview_sources.update(
                {
                    "satelliteMap": preview.source,
                    "satelliteMapIndex": preview.index,
                    "satelliteMapMeaning": preview.meaning,
                }
            )
        except Exception as exc:
            preview_warnings.append(f"Earth Engine map preview failed: {exc}")
        if language == "hi-IN":
            reply = (
                f"{self._location_label(farmer)} में आपके {crop} खेत का सैटेलाइट अंदाज:\n\n"
                f"फसल बढ़वार: {growth_status}\n"
                f"पानी का तनाव: {water_status}\n"
                f"मिट्टी/फसल नमी: {moisture_status}\n"
                f"हरियाली/क्लोरोफिल: {chlorophyll_status}\n\n"
                f"सलाह: {action}\n\n"
                f"फसल जानकारी: बुवाई तारीख {planted}, किस्म {variety}.\n"
                f"नोट: यह अंदाज Sentinel-2 उपग्रह पर आधारित है. अंतिम निर्णय के लिए मौसम, फसल अवस्था और खेत में असली जांच साथ में देखें.\n\n"
                f"तकनीकी जानकारी: {technical}"
            )
        elif language == "mr-IN":
            reply = (
                f"{self._location_label(farmer)} येथील तुमच्या {crop} शेताचा सॅटेलाइट अंदाज:\n\n"
                f"पीक वाढ: {growth_status}\n"
                f"पाण्याचा ताण: {water_status}\n"
                f"माती/पीक ओलावा: {moisture_status}\n"
                f"हिरवळ/क्लोरोफिल: {chlorophyll_status}\n\n"
                f"सल्ला: {action}\n\n"
                f"पीक माहिती: लागवड तारीख {planted}, वाण {variety}.\n"
                f"टीप: हा अंदाज Sentinel-2 उपग्रहावर आधारित आहे. अचूक निर्णयासाठी हवामान, पीक अवस्था आणि शेतातील प्रत्यक्ष तपासणी जोडली जाते.\n\n"
                f"तांत्रिक माहिती: {technical}"
            )
        else:
            reply = (
                f"Satellite estimate for your {crop} field at {self._location_label(farmer)}:\n\n"
                f"Crop growth: {growth_status}\n"
                f"Water stress: {water_status}\n"
                f"Soil/crop moisture: {moisture_status}\n"
                f"Greenness/chlorophyll: {chlorophyll_status}\n\n"
                f"Advice: {action}\n\n"
                f"Crop context: planted date {planted}, variety {variety}.\n"
                f"Note: this estimate uses Sentinel-2 satellite data. For the final decision, combine it with weather, crop stage and a field check.\n\n"
                f"Technical details: {technical}"
            )
        return WhatsAppWebhookResponse(
            intent="satellite_advisory",
            reply=reply,
            template_name="satellite_answer",
            transcript=transcript,
            data_sources={
                "satellite": signal.source,
                "ndvi": signal.ndvi,
                "ndwi": signal.ndwi,
                "ndmi": signal.ndmi,
                "evi": signal.evi,
                "ndre": signal.ndre,
                "waterStress": signal.water_stress,
                "vegetationStatus": signal.vegetation_status,
                "moistureStatus": signal.moisture_status,
                "chlorophyllStatus": signal.chlorophyll_status,
                **preview_sources,
            },
            media_url=media_url,
            media_content_type=media_content_type,
            service_warnings=preview_warnings,
            stored_context=self._stored_context(farmer),
        )

    def _refine_intent_with_ai(
        self,
        farmer_id: str,
        channel: str,
        language: str,
        text: str | None,
        local_intent: str,
        payload: WhatsAppWebhookRequest,
    ) -> tuple[str, dict[str, str | None]]:
        if local_intent not in {"general_advisory", "unknown"}:
            return local_intent, {}
        if not settings.enable_google_integrations or not text:
            return local_intent, {}
        if payload.latitude is not None or payload.longitude is not None:
            return local_intent, {}
        if payload.media_uri or payload.media_base64 or payload.media_type in {"image", "photo", "audio", "voice", "document"}:
            return local_intent, {}
        try:
            refined, meta = GeminiService().classify_farmer_intent(
                farmer_id=farmer_id,
                channel=channel,
                language=language,
                user_message=text,
                local_intent=local_intent,
            )
            return refined, meta if refined != local_intent else {}
        except AdvisoryProviderUnavailable:
            return local_intent, {}

    def _localized_satellite_status(self, status: str | None, language: str) -> str:
        normalized = status or "unknown"
        labels = {
            "hi-IN": {
                "unknown": "अभी साफ नहीं",
                "poor": "कमजोर",
                "moderate": "मध्यम",
                "healthy": "अच्छी",
                "high": "ज्यादा",
                "medium": "मध्यम",
                "low": "कम",
                "very_dry": "बहुत कम",
                "dry": "कम",
                "adequate": "ठीक",
                "moist": "अच्छा",
                "good": "अच्छा",
            },
            "mr-IN": {
                "unknown": "सध्या स्पष्ट नाही",
                "poor": "कमकुवत",
                "moderate": "मध्यम",
                "healthy": "चांगली",
                "high": "जास्त",
                "medium": "मध्यम",
                "low": "कमी",
                "very_dry": "खूप कमी",
                "dry": "कमी",
                "adequate": "ठीक",
                "moist": "चांगला",
                "good": "चांगला",
            },
        }
        if language in labels:
            return labels[language].get(normalized, normalized.replace("_", " "))
        english = {
            "unknown": "not clear yet",
            "poor": "weak",
            "moderate": "moderate",
            "healthy": "good",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "very_dry": "very low",
            "dry": "low",
            "adequate": "adequate",
            "moist": "good",
            "good": "good",
        }
        return english.get(normalized, normalized.replace("_", " "))

    def _satellite_farmer_action(self, signal, language: str) -> str:
        water_stress = signal.water_stress
        moisture = signal.moisture_status
        chlorophyll = signal.chlorophyll_status
        if language == "hi-IN":
            action = "आज या कल खेत में 3-4 जगह मिट्टी की नमी हाथ से जांचें."
            if water_stress == "high" or moisture in {"very_dry", "dry"}:
                action += " अगर 2-3 इंच तक मिट्टी सूखी है तो हल्की सिंचाई करें."
            elif water_stress == "medium":
                action += " नमी कम लगे तो अगले 24 घंटे में हल्की सिंचाई की तैयारी रखें."
            else:
                action += " अभी तुरंत सिंचाई की जरूरत नहीं दिखती; सामान्य निगरानी रखें."
            if chlorophyll == "low":
                action += " पत्तों में पीलापन दिखे तो फोटो भेजें; बिना जांच नाइट्रोजन न बढ़ाएं."
            return action
        if language == "mr-IN":
            action = "आज किंवा उद्या शेतात 3-4 ठिकाणी मातीचा ओलावा हाताने तपासा."
            if water_stress == "high" or moisture in {"very_dry", "dry"}:
                action += " जमीन 2-3 इंच कोरडी असेल तर हलके सिंचन करा."
            elif water_stress == "medium":
                action += " ओलावा कमी वाटला तर पुढील 24 तासांत हलक्या सिंचनाची तयारी ठेवा."
            else:
                action += " सध्या लगेच पाणी देण्याची गरज दिसत नाही; नियमित पाहणी ठेवा."
            if chlorophyll == "low":
                action += " पानांवर पिवळेपणा दिसत असेल तर फोटो पाठवा; तपासणीशिवाय नायट्रोजन वाढवू नका."
            return action
        action = "Check soil moisture by hand at 3-4 spots today or tomorrow."
        if water_stress == "high" or moisture in {"very_dry", "dry"}:
            action += " If the top 2-3 inches are dry, give light irrigation."
        elif water_stress == "medium":
            action += " If moisture feels low, prepare light irrigation within 24 hours."
        else:
            action += " Immediate irrigation is not indicated; continue normal monitoring."
        if chlorophyll == "low":
            action += " If leaves look yellow, send a photo and avoid increasing nitrogen without checking."
        return action

    def _satellite_technical_line(self, signal) -> str:
        return (
            f"NDVI {signal.ndvi}, NDWI {signal.ndwi}, NDMI {signal.ndmi}, "
            f"EVI {signal.evi}, NDRE {signal.ndre}. Source: {self._satellite_source_label(signal.source)}."
        )

    def _satellite_source_label(self, source: str | None) -> str:
        if source == "earth_engine_sentinel_2":
            return "Google Earth Engine / Sentinel-2"
        return source or "satellite provider"

    def _crop_recommendation_response(
        self,
        farmer: FarmerResponse,
        language: str,
        text: str | None,
        transcript: str | None,
    ) -> WhatsAppWebhookResponse:
        self._capture_profile_facts(farmer, text)
        farmer = store.get_farmer(farmer.id) or farmer
        public_context = self._public_context(farmer, crop=farmer.active_crop)
        expected_rainfall = None
        warnings: list[str] = []
        source_note = None
        if public_context and public_context.rainfall_normal.available:
            source_note = public_context.rainfall_normal.source
        elif farmer.farm.latitude is not None and farmer.farm.longitude is not None:
            try:
                weather = WeatherContextService().get_context(
                    WeatherContextRequest(latitude=farmer.farm.latitude, longitude=farmer.farm.longitude)
                )
                expected_rainfall = sum((day.rainfall_mm or 0) for day in weather.daily[:7])
                source_note = weather.source.value
                warnings.extend(self._provider_warnings(weather.provider_statuses))
            except WeatherProviderUnavailable as exc:
                warnings.append(str(exc))

        if not public_context and expected_rainfall is None and self._has_location_context(farmer):
            expected_rainfall = 650
            source_note = "regional_assumption_after_public_data_unavailable"
            warnings.append("Public rainfall context was unavailable; regional rainfall assumption used for a preliminary recommendation.")

        if not self._has_location_context(farmer):
            return WhatsAppWebhookResponse(
                intent="crop_recommendation",
                reply=phrase("crop_need_location", language),
                template_name="crop_need_location",
                transcript=transcript,
                stored_context=self._stored_context(farmer),
            )

        try:
            water_availability, sensor_sources = self._crop_water_availability(farmer)
            recommendation = RecommendationEngine().recommend(
                farmer=farmer,
                payload=CropRecommendationRequest(
                    farmer_id=farmer.id,
                    expected_rainfall_mm=expected_rainfall,
                    water_availability=water_availability,
                ),
                ndvi=None,
                public_context=public_context,
                public_context_error=None if public_context else "BigQuery context unavailable",
            )
            recommendation.data_sources.update(sensor_sources)
            top = recommendation.recommendations[:3]
            crops = ", ".join(self._crop_label(score.crop, language) for score in top)
            best = top[0] if top else None
            reason = best.reasons[0] if best and best.reasons else phrase("crop_reason_available_data", language)
            reply = phrase(
                "crop_recommendation_answer",
                language,
                location=self._location_label(farmer),
                crops=crops,
                reason=self._translate_reason(reason, language),
                source=self._source_summary(recommendation.data_sources, source_note),
            )
            if farmer.farm.soil_type == "unknown" and farmer.farm.soil_ph is None:
                reply = f"{reply}\n{phrase('crop_soil_refine', language)}"
            return WhatsAppWebhookResponse(
                intent="crop_recommendation",
                reply=reply,
                template_name="crop_recommendation_answer",
                transcript=transcript,
                data_sources={key: value for key, value in recommendation.data_sources.items() if value is not None},
                service_warnings=warnings,
                stored_context=self._stored_context(farmer),
            )
        except Exception as exc:
            return WhatsAppWebhookResponse(
                intent="crop_recommendation",
                reply=phrase("crop_recommendation_failed", language, location=self._location_label(farmer)),
                template_name="crop_recommendation_failed",
                transcript=transcript,
                service_warnings=warnings + [str(exc)],
                stored_context=self._stored_context(farmer),
            )

    def _crop_water_availability(
        self,
        farmer: FarmerResponse,
    ) -> tuple[WaterAvailability, dict[str, str | float | int | bool | None]]:
        latest_sensor = SensorService().latest_for_farmer(farmer.id)
        if latest_sensor and latest_sensor.readings.soil_moisture is not None:
            moisture = latest_sensor.readings.soil_moisture
            if latest_sensor.soil_moisture_risk in {RiskLevel.critical, RiskLevel.high}:
                availability = WaterAvailability.low
            elif latest_sensor.soil_moisture_risk == RiskLevel.low:
                availability = WaterAvailability.high
            else:
                availability = WaterAvailability.medium
            return availability, {
                "sensor": latest_sensor.source,
                "sensorDeviceType": latest_sensor.device_type,
                "soilMoisture": moisture,
                "soilMoistureRisk": latest_sensor.soil_moisture_risk.value,
                "waterAvailabilityFromSensor": availability.value,
            }
        return farmer.water_availability or WaterAvailability.medium, {}

    def _irrigation_response(
        self,
        farmer: FarmerResponse,
        language: str,
        text: str | None,
        transcript: str | None,
        payload: WhatsAppWebhookRequest | None = None,
    ) -> WhatsAppWebhookResponse:
        self._capture_profile_facts(farmer, text)
        farmer = store.get_farmer(farmer.id) or farmer
        if farmer.farm.latitude is None or farmer.farm.longitude is None:
            return WhatsAppWebhookResponse(
                intent="irrigation_advisory",
                reply=phrase("water_need_location", language),
                template_name="water_need_location",
                transcript=transcript,
                stored_context=self._stored_context(farmer),
            )
        crop = farmer.active_crop or self._extract_crop(text) or "crop"
        try:
            advisory = WeatherService().build_dry_spell_advisory(
                farmer,
                DrySpellAdvisoryRequest(farmer_id=farmer.id, crop=crop),
            )
            reply = phrase(
                "irrigation_answer",
                language,
                location=self._location_label(farmer),
                risk=advisory.risk_level.value,
                dry_days=advisory.dry_days,
                irrigation=advisory.irrigation_mm,
                advisory=advisory.advisory,
                source=self._join_sources([advisory.weather_source, advisory.satellite_source, advisory.ai_source]),
            )
            return WhatsAppWebhookResponse(
                intent="irrigation_advisory",
                reply=reply,
                template_name="irrigation_answer",
                transcript=transcript,
                data_sources={
                    "weather": advisory.weather_source,
                    "weatherFallbackUsed": advisory.weather_fallback_used,
                    "sensor": advisory.sensor_source,
                    "sensorId": advisory.sensor_id,
                    "sensorSoilMoisture": advisory.sensor_soil_moisture,
                    "sensorRisk": advisory.sensor_risk_level.value if advisory.sensor_risk_level else None,
                    "satellite": advisory.satellite_source,
                    "ai": advisory.ai_source,
                    "riskLevel": advisory.risk_level.value,
                },
                stored_context=self._stored_context(farmer),
            )
        except Exception as exc:
            fallback = self._voice_intake_response(farmer.id, language, text or "water advice", transcript, payload)
            fallback.service_warnings.append(str(exc))
            fallback.stored_context = self._stored_context(farmer)
            return fallback

    def _crop_planning_response(
        self,
        farmer: FarmerResponse,
        language: str,
        text: str | None,
        transcript: str | None,
    ) -> WhatsAppWebhookResponse:
        data = farmer.model_dump()
        crop = self._extract_crop(text) or farmer.active_crop
        if crop:
            data["active_crop"] = crop
            data["active_crop_status"] = "active" if self._is_planted_text(text) else "planned"
        planted_at = self._extract_relative_or_iso_date(text)
        if planted_at:
            data["active_crop_planted_at"] = planted_at
        variety = self._extract_variety(text)
        if variety:
            data["active_crop_variety"] = variety
        farmer = store.save_farmer(FarmerResponse(**data))

        missing: list[str] = []
        if not farmer.active_crop_planted_at:
            missing.append("planting date")
        if not farmer.active_crop_variety:
            missing.append("variety")
        if missing:
            reply = phrase(
                "crop_plan_missing",
                language,
                crop=self._crop_label(farmer.active_crop or "crop", language),
                missing=", ".join(missing),
            )
        else:
            reply = phrase(
                "crop_plan_saved",
                language,
                crop=self._crop_label(farmer.active_crop or "crop", language),
                date=farmer.active_crop_planted_at,
                variety=farmer.active_crop_variety,
            )
        return WhatsAppWebhookResponse(
            intent="crop_planning",
            reply=reply,
            template_name="crop_planning",
            transcript=transcript,
            stored_context=self._stored_context(farmer),
            data_sources={"farmerProfile": "stored_crop_plan"},
        )

    def _naturalize_response(
        self,
        response: WhatsAppWebhookResponse,
        farmer_id: str,
        language: str,
        text: str,
        channel: str,
    ) -> None:
        if not response.reply or response.intent in {
            "location_update",
            "voice_message",
            "satellite_advisory",
            "general_advisory",
            "crop_diagnosis",
            "crop_planning",
            "soil_card_extraction",
        }:
            return
        farmer = store.get_farmer(farmer_id)
        if not farmer:
            return
        try:
            reply, meta = GeminiService().generate_farmer_reply(
                farmer_id=farmer_id,
                channel=channel,
                language=language,
                user_message=text,
                intent=response.intent,
                farmer_context=self._stored_context(farmer),
                recent_messages=[
                    {
                        "role": message.role.value,
                        "text": message.text,
                        "intent": message.intent,
                        "language": message.language,
                    }
                    for message in ConversationStore().recent(farmer_id, limit=8)
                ],
                data_context={
                    "channel": channel,
                    "template": response.template_name,
                    "data_sources": response.data_sources,
                    "warnings": response.service_warnings,
                    "supports_photo": channel in {"whatsapp", "app"},
                    "supports_voice_reply": channel in {"whatsapp", "app", "voice"},
                },
                draft_answer=response.reply,
            )
            response.reply = reply
            response.data_sources.update({key: value for key, value in meta.items() if value})
        except AdvisoryProviderUnavailable as exc:
            response.service_warnings.append(f"AI natural-language generation unavailable: {exc}")

    def _attach_day_start_bulletin(
        self,
        response: WhatsAppWebhookResponse,
        farmer: FarmerResponse,
        language: str,
        channel: str,
    ) -> None:
        if not response.reply or not self._is_first_farmer_message_today(farmer.id):
            return
        bulletin = self._day_start_bulletin(farmer, language, channel)
        if not bulletin:
            return
        response.reply = f"{response.reply}\n\n{bulletin}"
        response.data_sources["dayStartBulletin"] = "weather_crop_satellite_context"
        ConversationStore().log(
            ConversationLogRequest(
                farmer_id=farmer.id,
                role=ConversationRole.assistant,
                text=bulletin,
                language=language,
                channel=channel,
                intent="day_start_bulletin",
                metadata={"attached_to_reply": True},
            )
        )

    def _is_first_farmer_message_today(self, farmer_id: str) -> bool:
        today = datetime.now(UTC).date()
        farmer_messages_today = [
            message
            for message in ConversationStore().recent(farmer_id, limit=40)
            if message.role == ConversationRole.farmer and message.created_at.date() == today
        ]
        return len(farmer_messages_today) == 1

    def _day_start_bulletin(self, farmer: FarmerResponse, language: str, channel: str) -> str | None:
        parts: list[str] = []
        location = ", ".join(part for part in [farmer.village, farmer.district] if part and part != "unknown")
        heading = {
            "hi-IN": "आज की जरूरी सूचना",
            "mr-IN": "आजची महत्त्वाची सूचना",
        }.get(language, "Today’s farm alert")

        if farmer.farm.latitude is not None and farmer.farm.longitude is not None:
            try:
                weather = WeatherContextService().get_context(
                    WeatherContextRequest(latitude=farmer.farm.latitude, longitude=farmer.farm.longitude)
                )
                rainfall_3d = sum((day.rainfall_mm or 0) for day in weather.daily[:3])
                temperature = weather.current_temperature_c
                if language == "hi-IN":
                    parts.append(
                        f"मौसम: {location or 'आपके खेत'} में अगले 3 दिन करीब {rainfall_3d:.1f} mm बारिश दिख रही है"
                        f"{f', तापमान {temperature:.1f} C' if temperature is not None else ''}."
                    )
                elif language == "mr-IN":
                    parts.append(
                        f"हवामान: {location or 'तुमच्या शेतात'} पुढील 3 दिवस सुमारे {rainfall_3d:.1f} mm पाऊस दिसतो"
                        f"{f', तापमान {temperature:.1f} C' if temperature is not None else ''}."
                    )
                else:
                    parts.append(
                        f"Weather: {location or 'your farm'} may get about {rainfall_3d:.1f} mm rain in 3 days"
                        f"{f', temperature {temperature:.1f} C' if temperature is not None else ''}."
                    )
            except WeatherProviderUnavailable:
                parts.append(self._localized_missing_weather(language))
        else:
            parts.append(self._localized_location_needed(language, channel))

        if farmer.active_crop:
            crop = self._crop_label(farmer.active_crop, language)
            if language == "hi-IN":
                parts.append(f"फसल: {crop} के लिए आज खेत की नमी और पत्तियों की हालत देखें.")
            elif language == "mr-IN":
                parts.append(f"पीक: {crop} साठी आज शेतातील ओलावा आणि पानांची स्थिती तपासा.")
            else:
                parts.append(f"Crop: for {crop}, check field moisture and leaf condition today.")

        if farmer.farm.latitude is not None and farmer.farm.longitude is not None:
            try:
                signal = WeatherService()._satellite_signal(farmer)
                if signal:
                    if language == "hi-IN":
                        parts.append(f"सैटेलाइट: पानी तनाव {signal.water_stress}, NDVI {signal.ndvi}.")
                    elif language == "mr-IN":
                        parts.append(f"सॅटेलाइट: पाण्याचा ताण {signal.water_stress}, NDVI {signal.ndvi}.")
                    else:
                        parts.append(f"Satellite: water stress {signal.water_stress}, NDVI {signal.ndvi}.")
            except Exception:
                pass

        if not parts:
            return None
        return f"{heading}: " + " ".join(parts)

    def _localized_missing_weather(self, language: str) -> str:
        if language == "hi-IN":
            return "मौसम सेवा अभी उपलब्ध नहीं है; खेत में नमी देखकर सिंचाई करें."
        if language == "mr-IN":
            return "हवामान सेवा सध्या उपलब्ध नाही; शेतातील ओलावा पाहून पाणी द्या."
        return "Weather service is not available right now; check soil moisture before irrigation."

    def _localized_location_needed(self, language: str, channel: str) -> str:
        if language == "hi-IN":
            return "स्थानीय मौसम और सैटेलाइट सलाह के लिए खेत की लोकेशन या पिनकोड भेजें."
        if language == "mr-IN":
            return "स्थानिक हवामान आणि सॅटेलाइट सल्ल्यासाठी शेताची लोकेशन किंवा पिनकोड पाठवा."
        if channel == "sms":
            return "Send village or pincode once for local weather and satellite advice."
        return "Share farm location or pincode once for local weather and satellite advice."

    def _intent_with_context(self, farmer_id: str, text: str | None, intent: str) -> str:
        if self._extract_pincode(text):
            previous_intent = self._last_active_intent(farmer_id)
            return previous_intent or intent
        if intent == "crop_recommendation":
            return intent
        if self._is_crop_planning_text(text):
            return "crop_planning"
        if intent in {
            "location_update",
            "voice_message",
            "document_message",
            "crop_diagnosis",
            "greeting",
            "identity_query",
            "weather_query",
            "satellite_advisory",
        }:
            return intent
        previous_intent = self._last_active_intent(farmer_id)
        if previous_intent == "crop_recommendation" and (
            is_crop_followup_text(text) or self._is_short_confirmation(text)
        ):
            return "crop_recommendation"
        if previous_intent == "irrigation_advisory" and is_water_followup_text(text):
            return "irrigation_advisory"
        if previous_intent == "crop_planning" and self._looks_like_crop_plan_followup(text):
            return "crop_planning"
        return intent

    def _capture_profile_facts(self, farmer: FarmerResponse, text: str | None) -> None:
        if not text:
            return
        data = farmer.model_dump()
        changed = False

        if self._needs_name(farmer):
            name = self._extract_name(text)
            if name:
                data["name"] = name
                changed = True

        crop = self._extract_crop(text)
        if crop and crop != data.get("active_crop"):
            data["active_crop"] = crop
            changed = True

        water = self._extract_water_availability(text)
        if water and water != data.get("water_availability"):
            data["water_availability"] = water
            changed = True

        soil_type = self._extract_soil_type(text)
        if soil_type and soil_type != farmer.farm.soil_type:
            farm = farmer.farm.model_dump()
            farm["soil_type"] = soil_type
            data["farm"] = farm
            changed = True

        if changed:
            store.save_farmer(FarmerResponse(**data))

    def _is_crop_planning_text(self, text: str | None) -> bool:
        normalized = (text or "").lower()
        return any(
            token in normalized
            for token in [
                "planted", "sown", "sowed", "i planted", "i have planted", "planning",
                "lagaya", "boya", "perni", "लागवड", "पेरणी", "लगाया", "बोया",
            ]
        )

    def _is_planted_text(self, text: str | None) -> bool:
        normalized = (text or "").lower()
        return any(token in normalized for token in ["planted", "sown", "sowed", "lagaya", "boya", "पेरणी", "लागवड", "लगाया", "बोया"])

    def _looks_like_crop_plan_followup(self, text: str | None) -> bool:
        normalized = (text or "").lower().strip()
        if not normalized:
            return False
        return bool(self._extract_relative_or_iso_date(normalized) or self._extract_variety(normalized) or self._extract_crop(normalized))

    def _extract_relative_or_iso_date(self, text: str | None) -> str | None:
        normalized = (text or "").lower()
        today = datetime.now(UTC).date()
        month_match = re.search(
            r"\b(\d{1,2})(?:st|nd|rd|th)?\s+"
            r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|"
            r"sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
            r"(?:\s+(20\d{2}))?\b",
            normalized,
        )
        if month_match:
            months = {
                "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
                "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
                "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
                "nov": 11, "november": 11, "dec": 12, "december": 12,
            }
            try:
                return today.replace(
                    year=int(month_match.group(3) or today.year),
                    month=months[month_match.group(2)],
                    day=int(month_match.group(1)),
                ).isoformat()
            except ValueError:
                pass
        if re.search(r"\b(today|aaj|आज)\b", normalized):
            return today.isoformat()
        if re.search(r"\b(yesterday|kal|काल)\b", normalized):
            return (today.fromordinal(today.toordinal() - 1)).isoformat()
        match = re.search(r"(\d{1,2})\s*(days?|दिन|दिवस)\s*(ago|पहले|आधी)?", normalized)
        if match:
            return (today.fromordinal(today.toordinal() - int(match.group(1)))).isoformat()
        week_match = re.search(r"(\d{1,2})\s*(weeks?|हफ्ते|आठवडे)\s*(ago|पहले|आधी)?", normalized)
        if week_match:
            return (today.fromordinal(today.toordinal() - int(week_match.group(1)) * 7)).isoformat()
        iso_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", normalized)
        return iso_match.group(1) if iso_match else None

    def _extract_variety(self, text: str | None) -> str | None:
        if not text:
            return None
        match = re.search(r"(?:variety|var\.?|जात|वाण)\s*[:\-]?\s*([A-Za-z0-9 \-]{2,30})", text, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip(" .,!?:;")
            value = re.split(r"\b(?:on|planted|sown|in|at|and)\b", value, maxsplit=1, flags=re.IGNORECASE)[0].strip(" .,!?:;")
            return value or None
        return None

    def _last_active_intent(self, farmer_id: str) -> str | None:
        for message in reversed(ConversationStore().recent(farmer_id, limit=8)):
            if (
                message.role == ConversationRole.assistant
                and message.intent in {"crop_recommendation", "irrigation_advisory", "crop_diagnosis", "weather_query", "crop_planning", "satellite_advisory"}
            ):
                return message.intent
        return None

    def _is_stale_menu_reply(self, reply: str) -> bool:
        normalized = reply.lower()
        stale_tokens = ["water, crop", "water crop", "soil, rain", "use water", "सलाह के लिए water"]
        return any(token in normalized for token in stale_tokens)

    def _is_crop_detail_followup(self, text: str | None) -> bool:
        normalized = (text or "").strip().lower()
        if normalized in {"crop", "crops", "recommend crop", "which crop", "what crop", "फसल", "पीक", "પાક"}:
            return False
        if any(term in normalized for term in ["suggest", "recommend", "which crop", "what crop"]):
            return False
        return is_crop_followup_text(normalized) or self._is_short_confirmation(normalized)

    def _is_short_confirmation(self, text: str | None) -> bool:
        normalized = (text or "").strip().lower()
        return normalized in {"yes", "no", "haan", "ha", "nahi", "ho", "हो", "नाही", "हां", "नहीं", "હા", "ના"}

    def _voice_intake_response(
        self,
        farmer_id: str,
        language: str,
        text: str,
        transcript: str | None,
        payload: WhatsAppWebhookRequest | None = None,
    ) -> WhatsAppWebhookResponse:
        farmer = store.get_farmer(farmer_id)
        if not farmer:
            return WhatsAppWebhookResponse(intent="unknown", reply=phrase("sms_unknown", language))
        try:
            voice_response = VoiceService().handle_intake(
                farmer,
                payload=VoiceIntakeRequest(
                    farmer_id=farmer_id,
                    transcript=text,
                    audio_base64=payload.audio_base64 if payload else None,
                    audio_uri=payload.audio_uri if payload else None,
                    audio_mime_type=payload.audio_mime_type if payload else "audio/wav",
                    language=language,
                ),
            )
            if (
                payload
                and (payload.audio_base64 or payload.audio_uri)
                and not payload.text
                and voice_response.detected_intent == "general_advisory"
            ):
                return WhatsAppWebhookResponse(
                    intent="voice_message",
                    reply=phrase("voice_transcription_needed", language),
                    template_name="voice_transcription_needed",
                    transcript=voice_response.transcript,
                )
        except VoiceProviderUnavailable:
            return WhatsAppWebhookResponse(
                intent="voice_message",
                reply=phrase("voice_transcription_needed", language),
                template_name="voice_transcription_needed",
                transcript=transcript,
            )
        return WhatsAppWebhookResponse(
            intent=voice_response.detected_intent,
            reply=voice_response.response_text,
            template_name="voice_reply",
            transcript=transcript,
            response_audio_base64=voice_response.response_audio_base64,
            response_audio_content_type=voice_response.response_audio_content_type,
        )

    def _image_response(
        self,
        payload: WhatsAppWebhookRequest,
        farmer_id: str,
        language: str,
        text: str | None,
        transcript: str | None,
    ) -> WhatsAppWebhookResponse:
        if self._is_soil_card_text(text):
            soil_response = self._try_soil_card_image(payload, farmer_id, language)
            if soil_response:
                return soil_response
        if not text:
            soil_response = self._try_soil_card_image(payload, farmer_id, language)
            if soil_response and self._soil_card_has_values(soil_response):
                return soil_response
        return self._diagnose_crop_photo(payload, farmer_id, language, text, transcript)

    def _try_soil_card_image(
        self,
        payload: WhatsAppWebhookRequest,
        farmer_id: str,
        language: str,
    ) -> WhatsAppWebhookResponse | None:
        try:
            extraction = SoilCardVisionService().extract(
                SoilCardExtractionRequest(
                    farmer_id=farmer_id,
                    image_uri=payload.media_uri,
                    image_base64=payload.media_base64,
                    mime_type=payload.media_mime_type or "image/jpeg",
                    extracted_text=payload.text,
                    language=language,
                )
            )
        except Exception as exc:
            if self._is_soil_card_text(payload.text):
                return WhatsAppWebhookResponse(
                    intent="soil_card_extraction",
                    reply=self._soil_card_failed_reply(language),
                    template_name="soil_card_failed",
                    service_warnings=[f"Soil card extraction failed: {exc}"],
                    stored_context=self._stored_context(store.get_farmer(farmer_id)) if store.get_farmer(farmer_id) else {},
                )
            return None
        if not self._soil_card_has_values(extraction) and not self._is_soil_card_text(payload.text):
            return None
        return WhatsAppWebhookResponse(
            intent="soil_card_extraction",
            reply=self._soil_card_reply(extraction, language),
            template_name="soil_card_extracted",
            data_sources={
                "vision": extraction.source,
                "model": extraction.model,
                "soilCardPersisted": extraction.persisted,
                "confidence": extraction.confidence,
            },
            stored_context=self._stored_context(extraction.farmer) if extraction.farmer else {},
        )

    def _soil_card_has_values(self, extraction: SoilCardExtractionResponse) -> bool:
        return any(
            value is not None
            for value in [
                extraction.ph,
                extraction.ec,
                extraction.organic_carbon,
                extraction.nitrogen,
                extraction.phosphorus,
                extraction.potassium,
            ]
        ) or bool(extraction.micronutrients)

    def _is_soil_card_text(self, text: str | None) -> bool:
        normalized = (text or "").lower()
        return any(
            token in normalized
            for token in [
                "soil card",
                "soil health",
                "soil test",
                "माती पत्रिका",
                "माती आरोग्य",
                "मृदा",
                "मिट्टी कार्ड",
                "मिट्टी जांच",
                "soil report",
            ]
        )

    def _soil_card_reply(self, extraction: SoilCardExtractionResponse, language: str) -> str:
        values = []
        if extraction.ph is not None:
            values.append(f"pH {extraction.ph}")
        if extraction.organic_carbon is not None:
            values.append(f"OC {extraction.organic_carbon}")
        if extraction.nitrogen is not None:
            values.append(f"N {extraction.nitrogen}")
        if extraction.phosphorus is not None:
            values.append(f"P {extraction.phosphorus}")
        if extraction.potassium is not None:
            values.append(f"K {extraction.potassium}")
        summary = ", ".join(values) if values else "values need manual review"
        if language == "mr-IN":
            return f"माती आरोग्य पत्रिकेतून माहिती वाचली: {summary}. ही माहिती तुमच्या शेताच्या प्रोफाइलमध्ये साठवली आहे. पुढील पीक आणि खत सल्ल्यासाठी मी हे वापरेन."
        if language == "hi-IN":
            return f"मिट्टी कार्ड से जानकारी पढ़ी: {summary}. यह जानकारी आपके खेत प्रोफाइल में सेव हो गई है. आगे फसल और खाद सलाह में मैं इसे उपयोग करूंगा."
        return f"I read the soil card values: {summary}. I saved them to your farm profile and will use them for crop and fertilizer advice."

    def _soil_card_failed_reply(self, language: str) -> str:
        if language == "mr-IN":
            return "माती आरोग्य पत्रिका स्पष्ट वाचता आली नाही. कृपया संपूर्ण कार्डाचा सरळ आणि स्पष्ट फोटो पाठवा."
        if language == "hi-IN":
            return "मिट्टी कार्ड साफ पढ़ा नहीं गया. कृपया पूरे कार्ड की सीधी और साफ फोटो भेजें."
        return "I could not read the soil card clearly. Please send a straight, clear photo of the full card."

    def _diagnose_crop_photo(
        self,
        payload: WhatsAppWebhookRequest,
        farmer_id: str,
        language: str,
        text: str | None,
        transcript: str | None,
    ) -> WhatsAppWebhookResponse:
        farmer = store.get_farmer(farmer_id)
        if not farmer:
            return WhatsAppWebhookResponse(intent="unknown", reply=phrase("sms_unknown", language))

        crop = self._extract_crop(text) or "crop"
        try:
            diagnosis = VisionOcrService().diagnose_crop_health(
                farmer,
                DiagnosisRequest(
                    farmer_id=farmer_id,
                    crop=crop,
                    symptoms_text=text,
                    voice_transcript=transcript,
                    photo_uri=payload.media_uri,
                    image_base64=payload.media_base64,
                    mime_type=payload.media_mime_type or "image/jpeg",
                    language=language,
                ),
            )
            ticket = ExpertService().create_ticket(
                farmer,
                DiagnosisRequest(farmer_id=farmer_id, crop=crop),
                diagnosis,
            )
            store.save_ticket(ticket)
            issue, action = self._localize_diagnosis(diagnosis.likely_issue, diagnosis.immediate_action, language)
            reply = phrase(
                "diagnosis_result",
                language,
                issue=issue,
                action=action,
                ticket=ticket.id,
            )
            return WhatsAppWebhookResponse(
                intent="crop_diagnosis",
                reply=reply,
                template_name="crop_diagnosis_result",
                should_escalate=diagnosis.needs_expert_followup,
                transcript=transcript,
                data_sources={"vision": diagnosis.source or "vision_ocr", "expertTicket": ticket.id},
                stored_context=self._stored_context(farmer),
            )
        except VisionProviderUnavailable:
            return WhatsAppWebhookResponse(
                intent="crop_diagnosis",
                reply=phrase("sms_photo", language),
                template_name="crop_photo_followup",
                should_escalate=True,
                transcript=transcript,
            )

    def _transcribe_voice(self, payload: WhatsAppWebhookRequest, language: str) -> str | None:
        if not payload.audio_uri and not payload.audio_base64:
            return None
        try:
            transcription = VoiceService().transcribe(
                VoiceTranscribeRequest(
                    audio_uri=payload.audio_uri,
                    audio_base64=payload.audio_base64,
                    language=language,
                    content_type=payload.audio_mime_type,
                    audio_encoding=self._audio_encoding_for_content_type(payload.audio_mime_type),
                )
            )
            return transcription.transcript
        except VoiceProviderUnavailable:
            return None

    def _audio_encoding_for_content_type(self, content_type: str | None) -> str:
        normalized = (content_type or "").split(";", 1)[0].strip().lower()
        if normalized in {"audio/ogg", "application/ogg"}:
            return "OGG_OPUS"
        if normalized in {"audio/webm", "video/webm"}:
            return "WEBM_OPUS"
        if normalized in {"audio/mpeg", "audio/mp3"}:
            return "MP3"
        if normalized in {"audio/wav", "audio/x-wav", "audio/wave"}:
            return "LINEAR16"
        return "AUTO"

    def _speak_reply(self, farmer_id: str, reply: str, language: str):
        try:
            return VoiceService().speak(VoiceSpeakRequest(farmer_id=farmer_id, text=reply, language=language))
        except VoiceProviderUnavailable as exc:
            return None

    def _attach_audio(self, farmer_id: str, response: WhatsAppWebhookResponse, language: str) -> None:
        if not response.reply or response.response_audio_base64:
            return
        response_audio = self._speak_reply(farmer_id, response.reply, language)
        if response_audio:
            response.response_audio_base64 = response_audio.audio_base64
            response.response_audio_content_type = response_audio.content_type
        else:
            response.service_warnings.append("TTS provider unavailable; text response was sent without voice audio.")

    def _should_skip_voice_attachment(self, response: WhatsAppWebhookResponse, channel: str) -> bool:
        return channel == "whatsapp" and response.intent in {
            "general_advisory",
            "crop_planning",
            "soil_card_extraction",
            "location_update",
        }

    def _detect_language(self, text: str | None) -> str | None:
        if not text or not settings.enable_google_integrations:
            return None
        try:
            detection = TranslationService().detect_language(DetectLanguageRequest(text=text))
            return detection.language
        except TranslationProviderUnavailable:
            return None

    def _requested_language(self, language: str | None) -> str | None:
        if language and language != "auto":
            return language
        return None

    def _location_from_text(self, text: str | None) -> LocationResolution | None:
        if not text:
            return None
        pincode = self._extract_pincode(text)
        should_resolve = bool(pincode) or any(
            token in text.lower()
            for token in ["near ", "village", "pincode", "pin code", "gaon", "gaav", "taluka", "district", "पास", "गाव", "जवळ", "जिला"]
        )
        if not should_resolve:
            return None
        try:
            return GeocodingService().resolve_text(pincode or text)
        except GeocodingProviderUnavailable:
            if pincode:
                return LocationResolution(source="pincode_unresolved", pincode=pincode)
            return None

    def _extract_pincode(self, text: str | None) -> str | None:
        if not text:
            return None
        match = re.search(r"\b([1-9][0-9]{5})\b", text)
        return match.group(1) if match else None

    def _extract_name(self, text: str) -> str | None:
        normalized = text.strip()
        lowered = normalized.lower()
        if not normalized or len(normalized) > 60:
            return None
        if lowered in {"hi", "hello", "hey", "namaste", "namaskar"} or any(term in lowered for term in ["weather", "crop", "water", "pani", "mausam", "photo", "location", "recommend", "fasal", "batao", "please", "tell", "फसल", "पीक", "मौसम", "पाणी", "बताओ", "सांगा", "नमस्ते", "नमस्कार"]):
            return None
        match = re.search(r"(?:my name is|i am|मेरा नाम|माझे नाव|माझं नाव)\s+(.+)", normalized, flags=re.IGNORECASE)
        if match:
            normalized = match.group(1).strip()
        words = normalized.split()
        if 1 <= len(words) <= 4 and all(len(word) <= 24 for word in words):
            return " ".join(word.strip(".,!?") for word in words).strip()
        return None

    def _extract_water_availability(self, text: str | None) -> WaterAvailability | None:
        normalized = (text or "").lower()
        if any(token in normalized for token in ["low water", "less water", "कमी पाणी", "कम पानी", "थोडे पाणी"]):
            return WaterAvailability.low
        if any(token in normalized for token in ["high water", "enough water", "जास्त पाणी", "ज्यादा पानी", "भरपूर पाणी"]):
            return WaterAvailability.high
        if any(token in normalized for token in ["medium water", "normal water", "मध्यम पाणी", "मध्यम पानी"]):
            return WaterAvailability.medium
        return None

    def _extract_soil_type(self, text: str | None) -> str | None:
        normalized = (text or "").lower()
        if any(token in normalized for token in ["black soil", "काली मिट्टी", "काळी माती", "black cotton"]):
            return "black"
        if any(token in normalized for token in ["red soil", "लाल मिट्टी", "लाल माती"]):
            return "red"
        if any(token in normalized for token in ["sandy soil", "रेतीली", "वालुकामय"]):
            return "sandy"
        return None

    def _needs_name(self, farmer: FarmerResponse) -> bool:
        return farmer.name.strip().lower() in {"", "farmer", "किसान", "शेतकरी", "unknown"}

    def _public_context(self, farmer: FarmerResponse, crop: str | None):
        if farmer.district in {"", "unknown", None} or farmer.state in {"", "unknown", None}:
            return None
        try:
            return BigQueryPublicDataService().build_context(
                GovernmentDataContextRequest(
                    state=farmer.state,
                    district=farmer.district,
                    crop=crop,
                    month=datetime.now(UTC).month,
                )
            )
        except Exception:
            return None

    def _has_location_context(self, farmer: FarmerResponse) -> bool:
        return (
            farmer.farm.latitude is not None
            and farmer.farm.longitude is not None
        ) or (farmer.district not in {"", "unknown", None} and farmer.state not in {"", "unknown", None})

    def _location_saved_reply(self, language: str, resolution: LocationResolution) -> str:
        return phrase(
            "location_saved_detailed",
            language,
            village=resolution.village or "-",
            taluka=resolution.taluka or "-",
            district=resolution.district or "-",
            state=resolution.state or "-",
            pincode=resolution.pincode or "-",
        )

    def _location_label(self, farmer: FarmerResponse) -> str:
        parts = [farmer.village if farmer.village != "unknown" else None, farmer.taluka, farmer.district if farmer.district != "unknown" else None, farmer.state if farmer.state != "unknown" else None]
        return ", ".join(part for part in parts if part) or "your farm"

    def _stored_context(self, farmer: FarmerResponse) -> dict[str, str | float | int | bool | None]:
        return {
            "name": farmer.name,
            "language": farmer.language,
            "village": None if farmer.village == "unknown" else farmer.village,
            "taluka": farmer.taluka,
            "district": None if farmer.district == "unknown" else farmer.district,
            "state": None if farmer.state == "unknown" else farmer.state,
            "pincode": farmer.pincode,
            "activeCrop": farmer.active_crop,
            "activeCropPlantedAt": farmer.active_crop_planted_at,
            "activeCropVariety": farmer.active_crop_variety,
            "activeCropStatus": farmer.active_crop_status,
            "waterAvailability": farmer.water_availability.value if farmer.water_availability else None,
            "latitude": farmer.farm.latitude,
            "longitude": farmer.farm.longitude,
            "soilType": None if farmer.farm.soil_type == "unknown" else farmer.farm.soil_type,
        }

    def _open_ticket_status(self, farmer_id: str, language: str) -> str | None:
        tickets = [ticket for ticket in store.list_tickets(farmer_id) if ticket.status not in {"resolved", "closed"}]
        if not tickets:
            return None
        latest = tickets[-1]
        return phrase("open_ticket_status", language, ticket=latest.id, status=latest.status, issue=latest.issue)

    def _provider_warnings(self, statuses) -> list[str]:
        return [f"{status.provider.value} failed: {status.error}" for status in statuses if status.attempted and not status.success and status.error]

    def _join_sources(self, sources: list[str | None]) -> str:
        cleaned = [source for source in sources if source]
        return ", ".join(cleaned) if cleaned else "stored farmer data"

    def _source_summary(self, sources: dict[str, object], fallback: str | None) -> str:
        names = [
            str(sources.get("rainfallSource") or fallback or ""),
            str(sources.get("groundwaterSource") or ""),
            str(sources.get("soil") or ""),
            str(sources.get("satellite") or ""),
        ]
        return self._join_sources([name for name in names if name and name != "None"])

    def _crop_label(self, crop: str, language: str) -> str:
        labels = {
            "hi-IN": {"sorghum": "ज्वार", "pearl_millet": "बाजरा", "cotton": "कपास", "soybean": "सोयाबीन", "maize": "मक्का", "groundnut": "मूंगफली", "pigeonpea": "अरहर"},
            "mr-IN": {"sorghum": "ज्वारी", "pearl_millet": "बाजरी", "cotton": "कापूस", "soybean": "सोयाबीन", "maize": "मका", "groundnut": "भुईमूग", "pigeonpea": "तूर"},
        }
        return labels.get(language, {}).get(crop, crop.replace("_", " "))

    def _translate_reason(self, reason: str, language: str) -> str:
        if language == "hi-IN":
            return (
                reason.replace("Fits kharif season.", "यह खरीफ मौसम के लिए अनुकूल है.")
                .replace("Soil type is suitable.", "मिट्टी का प्रकार अनुकूल है.")
                .replace("Expected rainfall matches crop need.", "अपेक्षित बारिश फसल की जरूरत से मेल खाती है.")
            )
        if language == "mr-IN":
            return (
                reason.replace("Fits kharif season.", "हे खरीप हंगामासाठी योग्य आहे.")
                .replace("Soil type is suitable.", "मातीचा प्रकार अनुकूल आहे.")
                .replace("Expected rainfall matches crop need.", "अपेक्षित पाऊस पिकाच्या गरजेशी जुळतो.")
            )
        return reason

    def _localize_diagnosis(self, issue: str, action: str, language: str) -> tuple[str, str]:
        if language == "hi-IN":
            issue_map = {
                "Possible fungal leaf disease": "पत्तियों पर फफूंद/धब्बे की समस्या हो सकती है",
                "Possible nutrient deficiency": "पोषक तत्वों की कमी हो सकती है",
                "Possible sucking pest or leaf curl complex": "रस चूसने वाले कीट या पत्ती मुड़ने की समस्या हो सकती है",
                "General crop stress": "फसल पर सामान्य तनाव दिख रहा है",
            }
            action_map = {
                "Remove infected leaves and consult RSK before spraying.": "संक्रमित पत्तियां हटाएं, हवा का प्रवाह रखें और छिड़काव से पहले कृषि केंद्र/विशेषज्ञ से सलाह लें।",
                "Check soil test and avoid excess nitrogen until moisture is adequate.": "मिट्टी जांच देखें और नमी ठीक होने तक ज्यादा नाइट्रोजन न दें।",
                "Scout leaf underside, use yellow sticky traps, and request expert validation.": "पत्तियों के नीचे जांच करें, पीले स्टिकी ट्रैप लगाएं और विशेषज्ञ से पुष्टि कराएं।",
                "Capture a clear leaf and whole-plant photo for expert review.": "विशेषज्ञ जांच के लिए पत्ती और पूरे पौधे की साफ फोटो भेजें।",
            }
            return issue_map.get(issue, issue), action_map.get(action, action)
        if language == "mr-IN":
            issue_map = {
                "Possible fungal leaf disease": "पानांवर बुरशी/डागाची समस्या असू शकते",
                "Possible nutrient deficiency": "अन्नद्रव्यांची कमतरता असू शकते",
                "Possible sucking pest or leaf curl complex": "रसशोषक किड किंवा पान वाकण्याची समस्या असू शकते",
                "General crop stress": "पिकावर सामान्य ताण दिसत आहे",
            }
            action_map = {
                "Remove infected leaves and consult RSK before spraying.": "बाधित पाने काढा, हवा खेळती ठेवा आणि फवारणीपूर्वी कृषी केंद्र/तज्ञांचा सल्ला घ्या.",
                "Check soil test and avoid excess nitrogen until moisture is adequate.": "माती चाचणी तपासा आणि ओलावा योग्य होईपर्यंत जास्त नायट्रोजन देऊ नका.",
                "Scout leaf underside, use yellow sticky traps, and request expert validation.": "पानांच्या खालची बाजू तपासा, पिवळे चिकट सापळे लावा आणि तज्ञांकडून खात्री करून घ्या.",
                "Capture a clear leaf and whole-plant photo for expert review.": "तज्ञ तपासणीसाठी पानाचा आणि पूर्ण रोपाचा स्पष्ट फोटो पाठवा.",
            }
            return issue_map.get(issue, issue), action_map.get(action, action)
        return issue, action

    def _send_whatsapp_reply(
        self,
        phone: str,
        reply: str,
        template_name: str | None,
        media_url: str | None = None,
    ) -> tuple[str | None, str]:
        return "twilio", "reply_returned_to_twilio"

    def _log_farmer_message(
        self,
        farmer_id: str,
        text: str,
        language: str,
        intent: str,
        payload: WhatsAppWebhookRequest,
        channel: str,
    ) -> None:
        ConversationStore().log(
            ConversationLogRequest(
                farmer_id=farmer_id,
                role=ConversationRole.farmer,
                text=text,
                language=language,
                channel=channel,
                intent=intent,
                metadata={
                    "message_id": payload.message_id,
                    "media_type": payload.media_type,
                    "has_media": bool(payload.media_uri or payload.media_base64),
                    "has_audio": bool(payload.audio_uri or payload.audio_base64),
                    "has_location": payload.latitude is not None and payload.longitude is not None,
                },
            )
        )

    def _log_assistant_message(
        self,
        farmer_id: str,
        reply: str,
        language: str,
        intent: str,
        response: WhatsAppWebhookResponse,
        channel: str,
    ) -> None:
        ConversationStore().log(
            ConversationLogRequest(
                farmer_id=farmer_id,
                role=ConversationRole.assistant,
                text=reply,
                language=language,
                channel=channel,
                intent=intent,
                metadata={
                    "template_name": response.template_name,
                    "delivery_status": response.delivery_status,
                    "should_escalate": response.should_escalate,
                    "has_media_url": bool(response.media_url),
                },
            )
        )

    def _message_summary(self, payload: WhatsAppWebhookRequest) -> str:
        if payload.latitude is not None and payload.longitude is not None:
            return f"Location shared: {payload.latitude},{payload.longitude}"
        if payload.audio_uri or payload.audio_base64:
            return "Voice message received"
        if payload.media_uri or payload.media_base64:
            return f"{payload.media_type or 'media'} received"
        return "WhatsApp message received"

    def _extract_crop(self, text: str | None) -> str | None:
        if not text:
            return None
        normalized = text.lower()
        crop_aliases = {
            "sorghum": ["jowar", "sorghum", "ज्वार", "ज्वारी"],
            "pearl_millet": ["bajra", "millet", "बाजरा", "बाजरी"],
            "cotton": ["cotton", "कपास", "कापूस"],
            "soybean": ["soybean", "सोयाबीन"],
            "maize": ["maize", "corn", "मक्का", "मका"],
            "groundnut": ["groundnut", "peanut", "मूंगफली", "भुईमूग"],
            "tomato": ["tomato", "टमाटर", "टोमॅटो"],
            "chilli": ["chilli", "chili", "मिर्च", "मिरची"],
            "paddy": ["paddy", "rice", "धान", "तांदूळ"],
        }
        for crop, aliases in crop_aliases.items():
            if any(alias in normalized for alias in aliases):
                return crop
        return None

    def _display_name(self, name: str, language: str) -> str:
        if name.strip().lower() == "farmer":
            return phrase("farmer_default_name", language)
        return name
