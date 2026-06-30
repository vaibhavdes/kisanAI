from app.models.schemas import SmsWebhookRequest, SmsWebhookResponse
from app.utils.language import phrase


class SmsService:
    def handle_message(self, payload: SmsWebhookRequest) -> SmsWebhookResponse:
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
