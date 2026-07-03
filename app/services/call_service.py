from app.models.schemas import VoiceCallWebhookRequest, VoiceCallWebhookResponse
from app.services.channel_intent import detect_farmer_intent
from app.services.dialogflow_channel_service import DialogflowChannelService, DialogflowChannelUnavailable
from app.utils.language import phrase


class CallService:
    def handle_call(self, payload: VoiceCallWebhookRequest) -> VoiceCallWebhookResponse:
        text = payload.transcript or self._intent_from_digit(payload.dtmf_digit)
        dialogflow_response = self._dialogflow_response(payload, text)
        if dialogflow_response:
            return dialogflow_response

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

    def _dialogflow_response(
        self,
        payload: VoiceCallWebhookRequest,
        text: str,
    ) -> VoiceCallWebhookResponse | None:
        if not text:
            return None
        try:
            result = DialogflowChannelService().route_text(
                text=text,
                language=payload.language,
                session_id=f"call-{payload.call_id}",
                parameters={
                    "phone": payload.from_phone,
                    "from_phone": payload.from_phone,
                    "call_id": payload.call_id,
                    "language": payload.language,
                    "text": text,
                },
            )
        except DialogflowChannelUnavailable:
            return None
        if not result.reply:
            return None
        return VoiceCallWebhookResponse(
            spoken_reply=result.reply,
            intent=result.intent,
            next_action=self._next_action_for_intent(result.intent),
            should_escalate=result.intent == "crop_diagnosis",
        )

    def _next_action_for_intent(self, intent: str) -> str:
        return {
            "irrigation_advisory": "collect_crop_and_pincode",
            "crop_diagnosis": "send_photo_link_or_transfer_to_expert",
            "crop_recommendation": "collect_soil_rain_water_inputs",
            "location_update": "confirm_location",
        }.get(intent, "repeat_menu")
