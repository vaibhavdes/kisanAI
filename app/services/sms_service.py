from app.models.schemas import SmsWebhookRequest, SmsWebhookResponse
from app.services.dialogflow_channel_service import DialogflowChannelService, DialogflowChannelUnavailable
from app.utils.language import phrase


class SmsService:
    def handle_message(self, payload: SmsWebhookRequest) -> SmsWebhookResponse:
        dialogflow_response = self._dialogflow_response(payload)
        if dialogflow_response:
            return dialogflow_response

        text = payload.text.strip().lower()
        if text.startswith("water") or "pani" in text:
            return SmsWebhookResponse(
                intent="irrigation_advisory",
                reply=phrase("sms_water", payload.language),
            )
        if text.startswith("photo") or "disease" in text:
            return SmsWebhookResponse(
                intent="crop_diagnosis",
                reply=phrase("sms_photo", payload.language),
                should_escalate=True,
            )
        if text.startswith("crop"):
            return SmsWebhookResponse(
                intent="crop_recommendation",
                reply=phrase("sms_crop", payload.language),
            )
        return SmsWebhookResponse(
            intent="unknown",
            reply=phrase("sms_unknown", payload.language),
        )

    def _dialogflow_response(self, payload: SmsWebhookRequest) -> SmsWebhookResponse | None:
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
        return SmsWebhookResponse(
            intent=result.intent,
            reply=result.reply,
            should_escalate=result.intent == "crop_diagnosis",
        )
