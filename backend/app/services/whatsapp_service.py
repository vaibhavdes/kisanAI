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
from app.services.expert_service import ExpertService
from app.services.geocoding_service import GeocodingProviderUnavailable, GeocodingService, LocationResolution
from app.services.bigquery_public_data_service import BigQueryPublicDataService
from app.services.recommendation_engine import RecommendationEngine
from app.services.translation_service import TranslationProviderUnavailable, TranslationService
from app.services.vision_ocr_service import VisionOcrService, VisionProviderUnavailable
from app.services.weather_context_service import WeatherContextService, WeatherProviderUnavailable
from app.services.weather_service import WeatherService
from app.services.voice_service import VoiceProviderUnavailable, VoiceService
from app.utils.language import phrase


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
        detected_language = self._detect_language(payload.text) if not requested_language else None
        response_language = requested_language or (existing_farmer.language if existing_farmer else None) or detected_language or settings.default_language
        identity = store.identify_farmer(
            FarmerIdentifyRequest(
                phone=payload.from_phone,
                channel=channel,
                language=response_language if (existing_farmer is None or requested_language) else None,
                latitude=payload.latitude,
                longitude=payload.longitude,
            )
        )
        farmer = identity.farmer
        if farmer.language != response_language:
            farmer = store.save_farmer(farmer.model_copy(update={"language": response_language}))

        transcript = self._transcribe_voice(payload, response_language)
        text = transcript or payload.text
        intent = detect_farmer_intent(
            text,
            payload.media_uri,
            media_type=payload.media_type,
            has_location=payload.latitude is not None and payload.longitude is not None,
        )
        intent = self._intent_with_context(farmer.id, text, intent)

        dialogflow_response = self._dialogflow_response(payload, farmer.id, response_language, text, transcript, intent)
        if dialogflow_response:
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
        response = self._build_response(payload, farmer.id, response_language, text, transcript, intent)
        response.farmer_id = farmer.id
        response.detected_language = response_language
        response.missing_fields = identity.missing_fields

        self._attach_audio(farmer.id, response, response_language)

        if send_outbound:
            response.outbound_provider, response.delivery_status = self._send_whatsapp_reply(
                payload.from_phone,
                response.reply,
                response.template_name,
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
    ) -> WhatsAppWebhookResponse:
        farmer = store.get_farmer(farmer_id)
        if not farmer:
            return WhatsAppWebhookResponse(intent="unknown", reply=phrase("sms_unknown", language))

        self._capture_profile_facts(farmer, text)
        farmer = store.get_farmer(farmer_id) or farmer

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

        if intent == "crop_diagnosis":
            if payload.media_uri or payload.media_base64:
                return self._diagnose_crop_photo(payload, farmer_id, language, text, transcript)
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
            recommendation = RecommendationEngine().recommend(
                farmer=farmer,
                payload=CropRecommendationRequest(
                    farmer_id=farmer.id,
                    expected_rainfall_mm=expected_rainfall,
                    water_availability=farmer.water_availability or WaterAvailability.medium,
                ),
                ndvi=None,
                public_context=public_context,
                public_context_error=None if public_context else "BigQuery context unavailable",
            )
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

    def _intent_with_context(self, farmer_id: str, text: str | None, intent: str) -> str:
        if self._extract_pincode(text):
            previous_intent = self._last_active_intent(farmer_id)
            return previous_intent or intent
        if intent in {
            "location_update",
            "voice_message",
            "document_message",
            "crop_diagnosis",
            "greeting",
            "identity_query",
            "weather_query",
        }:
            return intent
        previous_intent = self._last_active_intent(farmer_id)
        if previous_intent == "crop_recommendation" and (
            is_crop_followup_text(text) or self._is_short_confirmation(text)
        ):
            return "crop_recommendation"
        if previous_intent == "irrigation_advisory" and is_water_followup_text(text):
            return "irrigation_advisory"
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

    def _last_active_intent(self, farmer_id: str) -> str | None:
        for message in reversed(ConversationStore().recent(farmer_id, limit=8)):
            if (
                message.role == ConversationRole.assistant
                and message.intent in {"crop_recommendation", "irrigation_advisory", "crop_diagnosis", "weather_query"}
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
                    audio_encoding="AUTO",
                )
            )
            return transcription.transcript
        except VoiceProviderUnavailable:
            return None

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

    def _send_whatsapp_reply(self, phone: str, reply: str, template_name: str | None) -> tuple[str | None, str]:
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
