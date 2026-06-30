from app.core.config import settings
from app.models.schemas import DiagnosisRequest, DiagnosisResult, FarmerResponse, RiskLevel


class GeminiService:
    def diagnose_crop_health(
        self,
        farmer: FarmerResponse,
        payload: DiagnosisRequest,
    ) -> DiagnosisResult:
        if settings.enable_google_integrations and settings.gemini_api_key:
            # Production path: call Gemini multimodal or Vertex AI Vision with photo_uri and symptoms.
            # Keep response shape identical to this fallback.
            return self._fallback_diagnosis(payload)

        return self._fallback_diagnosis(payload)

    def _fallback_diagnosis(self, payload: DiagnosisRequest) -> DiagnosisResult:
        text = " ".join(
            item.lower()
            for item in [payload.symptoms_text, payload.voice_transcript, payload.photo_uri]
            if item
        )

        if any(token in text for token in ["curl", "whitefly", "white insects", "leaf curl"]):
            issue = "Possible sucking pest or leaf curl complex"
            action = "Scout leaf underside, use yellow sticky traps, and request expert validation."
            severity = RiskLevel.high
            confidence = 0.78
        elif any(token in text for token in ["yellow", "nitrogen", "pale"]):
            issue = "Possible nutrient deficiency"
            action = "Check soil test and avoid excess nitrogen until moisture is adequate."
            severity = RiskLevel.medium
            confidence = 0.66
        elif any(token in text for token in ["spot", "fungus", "blight"]):
            issue = "Possible fungal leaf disease"
            action = "Remove infected leaves and consult RSK before spraying."
            severity = RiskLevel.high
            confidence = 0.72
        else:
            issue = "General crop stress"
            action = "Capture a clear leaf and whole-plant photo for expert review."
            severity = RiskLevel.medium
            confidence = 0.55

        return DiagnosisResult(
            crop=payload.crop,
            likely_issue=issue,
            confidence=confidence,
            severity=severity,
            immediate_action=action,
            needs_expert_followup=True,
        )
