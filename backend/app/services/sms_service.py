from app.models.schemas import SmsWebhookRequest, SmsWebhookResponse
from app.services.channel_intent import detect_farmer_intent
from app.services.dialogflow_channel_service import DialogflowChannelService, DialogflowChannelUnavailable
from app.utils.language import phrase


class SmsService:
    def handle_message(self, payload: SmsWebhookRequest) -> SmsWebhookResponse:
        intent = detect_farmer_intent(payload.text)
        dialogflow_response = self._dialogflow_response(payload, intent)
        if dialogflow_response:
            return dialogflow_response

        if intent in {"greeting", "general_advisory"}:
            return SmsWebhookResponse(
                intent="general_advisory",
                reply=phrase(
                    "general_response",
                    payload.language,
                    name=phrase("farmer_default_name", payload.language),
                ),
            )
        if intent == "identity_query":
            return SmsWebhookResponse(
                intent=intent,
                reply=phrase("identity_response", payload.language, name=phrase("farmer_default_name", payload.language)),
            )
        if intent == "weather_query":
            return SmsWebhookResponse(intent=intent, reply=phrase("weather_response", payload.language))
        if intent == "irrigation_advisory":
            return SmsWebhookResponse(
                intent="irrigation_advisory",
                reply=phrase("sms_water", payload.language),
            )
        if intent == "crop_diagnosis":
            return SmsWebhookResponse(
                intent="crop_diagnosis",
                reply=phrase("sms_photo", payload.language),
                should_escalate=True,
            )
        if intent == "crop_recommendation":
            return SmsWebhookResponse(
                intent="crop_recommendation",
                reply=phrase("sms_crop", payload.language),
            )
        return SmsWebhookResponse(
            intent="unknown",
            reply=phrase("sms_unknown", payload.language),
        )

    def _dialogflow_response(self, payload: SmsWebhookRequest, local_intent: str) -> SmsWebhookResponse | None:
        if local_intent in {"greeting", "identity_query", "weather_query", "unknown"}:
            return None
        try:
            result = DialogflowChannelService().route_text(
                text=payload.text,
                language=payload.language,
                session_id=f"sms-{payload.from_phone}",
                parameters={
                    "phone": payload.from_phone,
                    "from_phone": payload.from_phone,
                    "language": payload.language,
                    "text": payload.text,
                },
            )
        except DialogflowChannelUnavailable:
            return None
        if not result.reply:
            return None
        if _is_stale_menu_reply(result.reply):
            return None
        if local_intent not in {"general_advisory", "unknown"} and result.intent != local_intent:
            return None
        return SmsWebhookResponse(
            intent=result.intent,
            reply=result.reply,
            should_escalate=result.intent == "crop_diagnosis",
        )


def _is_stale_menu_reply(reply: str) -> bool:
    normalized = reply.lower()
    stale_tokens = ["water, crop", "water crop", "soil, rain", "use water", "सलाह के लिए water"]
    return any(token in normalized for token in stale_tokens)
