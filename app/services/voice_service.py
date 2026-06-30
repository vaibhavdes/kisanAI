from app.models.schemas import FarmerResponse, VoiceIntakeRequest, VoiceIntakeResponse
from app.utils.language import language_name, phrase


class VoiceService:
    def handle_intake(self, farmer: FarmerResponse, payload: VoiceIntakeRequest) -> VoiceIntakeResponse:
        language = payload.language or farmer.language
        transcript = payload.transcript or "farmer asks for irrigation advice"
        intent = self._detect_intent(transcript)
        response = self._response_for_intent(intent, farmer.name, language)
        return VoiceIntakeResponse(
            transcript=transcript,
            detected_intent=intent,
            response_text=response,
            response_language=language,
            audio_url=f"demo://tts/{language_name(language).lower()}",
        )

    def _detect_intent(self, transcript: str) -> str:
        text = transcript.lower()
        if any(word in text for word in ["water", "irrigation", "pani", "dry"]):
            return "irrigation_advisory"
        if any(word in text for word in ["disease", "photo", "leaf", "spot"]):
            return "crop_diagnosis"
        if any(word in text for word in ["crop", "sow", "plant"]):
            return "crop_recommendation"
        return "general_advisory"

    def _response_for_intent(self, intent: str, name: str, language: str) -> str:
        if intent == "irrigation_advisory":
            return phrase("irrigation_response", language, name=name)
        if intent == "crop_diagnosis":
            return phrase("diagnosis_response", language, name=name)
        if intent == "crop_recommendation":
            return phrase("crop_response", language, name=name)
        return phrase("general_response", language, name=name, language=language_name(language))
