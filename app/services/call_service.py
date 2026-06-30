from app.models.schemas import VoiceCallWebhookRequest, VoiceCallWebhookResponse
from app.services.channel_intent import detect_farmer_intent
from app.utils.language import phrase


class CallService:
    def handle_call(self, payload: VoiceCallWebhookRequest) -> VoiceCallWebhookResponse:
        text = payload.transcript or self._intent_from_digit(payload.dtmf_digit)
        intent = detect_farmer_intent(text)

        if intent == "irrigation_advisory":
            reply = phrase("sms_water", payload.language)
            next_action = "collect_crop_and_pincode"
        elif intent == "crop_diagnosis":
            reply = phrase("sms_photo", payload.language)
            next_action = "send_photo_link_or_transfer_to_expert"
        elif intent == "crop_recommendation":
            reply = phrase("sms_crop", payload.language)
            next_action = "collect_soil_rain_water_inputs"
        else:
            reply = phrase("sms_unknown", payload.language)
            next_action = "repeat_menu"

        return VoiceCallWebhookResponse(
            spoken_reply=reply,
            intent=intent,
            next_action=next_action,
            should_escalate=intent == "crop_diagnosis",
        )

    def _intent_from_digit(self, digit: str | None) -> str:
        return {
            "1": "water",
            "2": "crop",
            "3": "photo",
        }.get(digit or "", "")
