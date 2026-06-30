from app.models.schemas import WhatsAppWebhookRequest, WhatsAppWebhookResponse
from app.services.channel_intent import detect_farmer_intent
from app.utils.language import phrase


class WhatsAppService:
    def handle_message(self, payload: WhatsAppWebhookRequest) -> WhatsAppWebhookResponse:
        intent = detect_farmer_intent(payload.text, payload.media_uri)

        if intent == "irrigation_advisory":
            return WhatsAppWebhookResponse(
                intent=intent,
                reply=phrase("sms_water", payload.language),
                template_name="irrigation_intake",
            )
        if intent == "crop_diagnosis":
            return WhatsAppWebhookResponse(
                intent=intent,
                reply=phrase("sms_photo", payload.language),
                template_name="crop_photo_followup",
                should_escalate=bool(payload.media_uri),
            )
        if intent == "crop_recommendation":
            return WhatsAppWebhookResponse(
                intent=intent,
                reply=phrase("sms_crop", payload.language),
                template_name="crop_recommendation_intake",
            )

        return WhatsAppWebhookResponse(
            intent=intent,
            reply=phrase("sms_unknown", payload.language),
            template_name="main_menu",
        )

