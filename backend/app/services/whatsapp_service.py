from app.core.config import settings
from app.models.schemas import (
    ConversationLogRequest,
    ConversationRole,
    DiagnosisRequest,
    FarmerIdentifyRequest,
    DetectLanguageRequest,
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
from app.services.translation_service import TranslationProviderUnavailable, TranslationService
from app.services.vision_ocr_service import VisionOcrService, VisionProviderUnavailable
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
        detected_language = self._detect_language(payload.text) or self._fallback_language(payload.language)
        identity = store.identify_farmer(
            FarmerIdentifyRequest(
                phone=payload.from_phone,
                channel=channel,
                language=detected_language,
                latitude=payload.latitude,
                longitude=payload.longitude,
            )
        )
        farmer = identity.farmer

        transcript = self._transcribe_voice(payload, detected_language)
        text = transcript or payload.text
        intent = detect_farmer_intent(
            text,
            payload.media_uri,
            media_type=payload.media_type,
            has_location=payload.latitude is not None and payload.longitude is not None,
        )
        intent = self._intent_with_context(farmer.id, text, intent)

        dialogflow_response = self._dialogflow_response(payload, farmer.id, detected_language, text, transcript, intent)
        if dialogflow_response:
            dialogflow_response.farmer_id = farmer.id
            dialogflow_response.detected_language = detected_language
            dialogflow_response.missing_fields = identity.missing_fields
            self._log_farmer_message(
                farmer.id,
                text or self._message_summary(payload),
                detected_language,
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
            self._attach_audio(farmer.id, dialogflow_response, detected_language)
            self._log_assistant_message(
                farmer.id,
                dialogflow_response.reply,
                detected_language,
                dialogflow_response.intent,
                dialogflow_response,
                channel,
            )
            return dialogflow_response

        self._log_farmer_message(farmer.id, text or self._message_summary(payload), detected_language, intent, payload, channel)
        response = self._build_response(payload, farmer.id, detected_language, text, transcript, intent)
        response.farmer_id = farmer.id
        response.detected_language = detected_language
        response.missing_fields = identity.missing_fields

        self._attach_audio(farmer.id, response, detected_language)

        if send_outbound:
            response.outbound_provider, response.delivery_status = self._send_whatsapp_reply(
                payload.from_phone,
                response.reply,
                response.template_name,
            )
        else:
            response.delivery_status = "app_response"
        self._log_assistant_message(farmer.id, response.reply, detected_language, response.intent, response, channel)
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
        if intent == "location_update":
            return WhatsAppWebhookResponse(
                intent=intent,
                reply=phrase("sms_location_saved", language),
                template_name="location_saved",
                transcript=transcript,
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
            farmer = store.get_farmer(farmer_id)
            name = self._display_name(farmer.name if farmer else "Farmer", language)
            return WhatsAppWebhookResponse(
                intent="general_advisory",
                reply=phrase("general_response", language, name=name),
                template_name="friendly_start",
                transcript=transcript,
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
            return WhatsAppWebhookResponse(
                intent=intent,
                reply=phrase("weather_response", language),
                template_name="weather_intake",
                transcript=transcript,
            )

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
            return self._voice_intake_response(farmer_id, language, text or "water advice", transcript, payload)

        if intent == "crop_recommendation":
            if self._is_crop_detail_followup(text):
                return WhatsAppWebhookResponse(
                    intent=intent,
                    reply=phrase("crop_followup_ack", language),
                    template_name="crop_followup",
                    transcript=transcript,
                )
            return WhatsAppWebhookResponse(
                intent=intent,
                reply=phrase("sms_crop", language),
                template_name="crop_recommendation_intake",
                transcript=transcript,
            )

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

    def _intent_with_context(self, farmer_id: str, text: str | None, intent: str) -> str:
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
            ticket_label = "तिकीट" if language == "mr-IN" else "टिकट" if language == "hi-IN" else "Ticket"
            reply = f"{diagnosis.likely_issue}. {diagnosis.immediate_action} {ticket_label}: {ticket.id}"
            return WhatsAppWebhookResponse(
                intent="crop_diagnosis",
                reply=reply,
                template_name="crop_diagnosis_result",
                should_escalate=diagnosis.needs_expert_followup,
                transcript=transcript,
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
        except VoiceProviderUnavailable:
            return None

    def _attach_audio(self, farmer_id: str, response: WhatsAppWebhookResponse, language: str) -> None:
        if not response.reply or response.response_audio_base64:
            return
        response_audio = self._speak_reply(farmer_id, response.reply, language)
        if response_audio:
            response.response_audio_base64 = response_audio.audio_base64
            response.response_audio_content_type = response_audio.content_type

    def _detect_language(self, text: str | None) -> str | None:
        if not text or not settings.enable_google_integrations:
            return None
        try:
            detection = TranslationService().detect_language(DetectLanguageRequest(text=text))
            return detection.language
        except TranslationProviderUnavailable:
            return None

    def _fallback_language(self, language: str | None) -> str:
        if language and language != "auto":
            return language
        return settings.default_language

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
        for crop in ["cotton", "chilli", "maize", "paddy", "tomato", "groundnut", "millet"]:
            if crop in normalized:
                return crop
        return None

    def _display_name(self, name: str, language: str) -> str:
        if name.strip().lower() == "farmer":
            return phrase("farmer_default_name", language)
        return name
