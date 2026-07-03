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
from app.services.channel_intent import detect_farmer_intent
from app.services.conversation_store import ConversationStore
from app.services.expert_service import ExpertService
from app.services.providers.authkey_client import AuthkeyClient
from app.services.translation_service import TranslationProviderUnavailable, TranslationService
from app.services.vision_ocr_service import VisionOcrService, VisionProviderUnavailable
from app.services.voice_service import VoiceProviderUnavailable, VoiceService
from app.utils.language import phrase


class WhatsAppService:
    def handle_message(self, payload: WhatsAppWebhookRequest) -> WhatsAppWebhookResponse:
        detected_language = self._detect_language(payload.text) or payload.language
        identity = store.identify_farmer(
            FarmerIdentifyRequest(
                phone=payload.from_phone,
                channel="whatsapp",
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

        self._log_farmer_message(farmer.id, text or self._message_summary(payload), detected_language, intent, payload)
        response = self._build_response(payload, farmer.id, detected_language, text, transcript, intent)
        response.farmer_id = farmer.id
        response.detected_language = detected_language
        response.missing_fields = identity.missing_fields

        if settings.enable_google_integrations and response.reply:
            response_audio = self._speak_reply(farmer.id, response.reply, detected_language)
            if response_audio:
                response.response_audio_base64 = response_audio.audio_base64
                response.response_audio_content_type = response_audio.content_type

        response.outbound_provider, response.delivery_status = self._send_whatsapp_reply(
            payload.from_phone,
            response.reply,
            response.template_name,
        )
        self._log_assistant_message(farmer.id, response.reply, detected_language, response.intent, response)
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
            return self._voice_intake_response(farmer_id, language, text or "", transcript)

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
            return self._voice_intake_response(farmer_id, language, text or "water advice", transcript)

        if intent == "crop_recommendation":
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

    def _voice_intake_response(
        self,
        farmer_id: str,
        language: str,
        text: str,
        transcript: str | None,
    ) -> WhatsAppWebhookResponse:
        farmer = store.get_farmer(farmer_id)
        if not farmer:
            return WhatsAppWebhookResponse(intent="unknown", reply=phrase("sms_unknown", language))
        voice_response = VoiceService().handle_intake(
            farmer,
            payload=VoiceIntakeRequest(farmer_id=farmer_id, transcript=text, language=language),
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
            reply = f"{diagnosis.likely_issue}. {diagnosis.immediate_action} Ticket: {ticket.id}"
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

    def _detect_language(self, text: str | None) -> str | None:
        if not text or not settings.enable_google_integrations:
            return None
        try:
            detection = TranslationService().detect_language(DetectLanguageRequest(text=text))
            return detection.language
        except TranslationProviderUnavailable:
            return None

    def _send_whatsapp_reply(self, phone: str, reply: str, template_name: str | None) -> tuple[str | None, str]:
        if not settings.authkey_api_key:
            return None, "skipped_no_authkey"
        if not settings.authkey_whatsapp_template_id:
            return "authkey", "skipped_no_template"

        result = AuthkeyClient(settings.authkey_api_key).send_whatsapp_template_get(
            mobile=phone,
            country_code=settings.authkey_test_country_code,
            template_id=settings.authkey_whatsapp_template_id,
            body_values={"message": reply, "template": template_name or "reply"},
            dry_run=not settings.authkey_send_enabled,
        )
        if result.dry_run:
            return result.provider, "dry_run"
        return result.provider, "sent" if result.sent else "failed"

    def _log_farmer_message(
        self,
        farmer_id: str,
        text: str,
        language: str,
        intent: str,
        payload: WhatsAppWebhookRequest,
    ) -> None:
        ConversationStore().log(
            ConversationLogRequest(
                farmer_id=farmer_id,
                role=ConversationRole.farmer,
                text=text,
                language=language,
                channel="whatsapp",
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
    ) -> None:
        ConversationStore().log(
            ConversationLogRequest(
                farmer_id=farmer_id,
                role=ConversationRole.assistant,
                text=reply,
                language=language,
                channel="whatsapp",
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
