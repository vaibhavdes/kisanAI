import base64
import json
from binascii import Error as BinasciiError
from typing import Any

import requests

from app.core.config import settings
from app.models.schemas import (
    DiagnosisRequest,
    DiagnosisResult,
    FarmerResponse,
    ProviderFeature,
    ProviderName,
    RiskLevel,
    SoilCardExtractionRequest,
    SoilCardExtractionResponse,
)
from app.repositories.store import store


class VisionProviderUnavailable(RuntimeError):
    pass


class VisionOcrService:
    def diagnose_crop_health(
        self,
        farmer: FarmerResponse,
        payload: DiagnosisRequest,
    ) -> DiagnosisResult:
        if not settings.enable_google_integrations:
            return self._fallback_diagnosis(payload, source="text_heuristic_google_disabled")

        image = self._load_optional_image(payload.image_base64, payload.photo_uri)
        if image is None:
            return self._fallback_diagnosis(payload, source="text_heuristic")

        errors: list[str] = []
        for provider in self._provider_order():
            try:
                data, model = self._generate_json(
                    provider=provider,
                    prompt=self._crop_diagnosis_prompt(farmer, payload),
                    image=image,
                    mime_type=payload.mime_type,
                )
                return DiagnosisResult(
                    crop=payload.crop,
                    likely_issue=str(data.get("likely_issue") or "Crop stress needing review"),
                    confidence=self._bounded_float(data.get("confidence"), default=0.7),
                    severity=self._risk_from_text(str(data.get("severity") or "medium")),
                    immediate_action=str(
                        data.get("immediate_action")
                        or "Capture another clear photo and ask an expert before spraying."
                    ),
                    needs_expert_followup=bool(data.get("needs_expert_followup", True)),
                    source=provider.value,
                    model=model,
                )
            except Exception as exc:
                errors.append(f"{provider.value}:{exc.__class__.__name__}:{exc}")

        if payload.symptoms_text or payload.voice_transcript:
            return self._fallback_diagnosis(
                payload,
                source=f"text_heuristic_after_vision_error:{'; '.join(errors)}",
            )
        raise VisionProviderUnavailable("; ".join(errors) or "No vision provider is configured.")

    def extract_soil_card(self, payload: SoilCardExtractionRequest) -> SoilCardExtractionResponse:
        image = self._load_optional_image(payload.image_base64, payload.image_uri)
        if image is None:
            raise VisionProviderUnavailable("image_base64 or image_uri is required for soil-card vision.")

        errors: list[str] = []
        for provider in self._provider_order():
            try:
                data, model = self._generate_json(
                    provider=provider,
                    prompt=self._soil_card_prompt(payload),
                    image=image,
                    mime_type=payload.mime_type,
                )
                return SoilCardExtractionResponse(
                    source=provider.value,
                    model=model,
                    ph=self._optional_float(data.get("ph")),
                    ec=self._optional_float(data.get("ec")),
                    organic_carbon=self._optional_float(data.get("organic_carbon")),
                    nitrogen=self._nutrient_value(data.get("nitrogen")),
                    phosphorus=self._nutrient_value(data.get("phosphorus")),
                    potassium=self._nutrient_value(data.get("potassium")),
                    micronutrients=self._micronutrients(data.get("micronutrients")),
                    confidence=self._bounded_float(data.get("confidence"), default=0.75),
                    needs_manual_review=bool(data.get("needs_manual_review", False)),
                    raw_text=data.get("raw_text"),
                )
            except Exception as exc:
                errors.append(f"{provider.value}:{exc.__class__.__name__}:{exc}")
        raise VisionProviderUnavailable("; ".join(errors) or "No vision provider is configured.")

    def _generate_json(
        self,
        *,
        provider: ProviderName,
        prompt: str,
        image: bytes,
        mime_type: str,
    ) -> tuple[dict[str, Any], str]:
        from google import genai
        from google.genai import types

        if provider == ProviderName.vertex_ai_vision:
            if not settings.google_cloud_project:
                raise VisionProviderUnavailable("GOOGLE_CLOUD_PROJECT is required for Vertex AI Vision.")
            client = genai.Client(
                vertexai=True,
                project=settings.google_cloud_project,
                location=settings.google_cloud_location,
            )
            model = settings.vertex_ai_model
        elif provider == ProviderName.gemini_vision:
            if not settings.gemini_api_key:
                raise VisionProviderUnavailable("GEMINI_API_KEY is required for Gemini Vision fallback.")
            client = genai.Client(api_key=settings.gemini_api_key)
            model = settings.gemini_model
        else:
            raise VisionProviderUnavailable(f"{provider.value} is not a vision provider.")

        response = client.models.generate_content(
            model=model,
            contents=[
                prompt,
                types.Part.from_bytes(data=image, mime_type=mime_type),
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        text = (response.text or "").strip()
        if not text:
            raise VisionProviderUnavailable(f"{provider.value} returned empty vision response.")
        return self._parse_json_response(text), model

    def _crop_diagnosis_prompt(self, farmer: FarmerResponse, payload: DiagnosisRequest) -> str:
        return f"""
You are KISAN-AI crop health vision assistant for small farmers.

Return only JSON with keys:
likely_issue, confidence, severity, immediate_action, needs_expert_followup.

Use severity as one of: low, medium, high, critical.
Keep immediate_action short, practical, and safe. Do not prescribe restricted chemicals.
If unsure, set needs_expert_followup true.

Farmer language: {payload.language or farmer.language}
Location: {farmer.village}, {farmer.district}, {farmer.state}
Crop: {payload.crop}
Symptoms text: {payload.symptoms_text or ""}
Voice transcript: {payload.voice_transcript or ""}
"""

    def _soil_card_prompt(self, payload: SoilCardExtractionRequest) -> str:
        return f"""
You are KISAN-AI soil card OCR assistant.

Extract soil test values from the image. Return only JSON with keys:
ph, ec, organic_carbon, nitrogen, phosphorus, potassium, micronutrients,
confidence, needs_manual_review, raw_text.

Use numbers where visible. For nitrogen/phosphorus/potassium, use number if visible,
otherwise low/medium/high if that is what the card shows. micronutrients must be an object.
If a value is not visible, return null. Farmer language: {payload.language}.
"""

    def _load_optional_image(self, image_base64: str | None, image_uri: str | None) -> bytes | None:
        if image_base64:
            try:
                return base64.b64decode(image_base64, validate=True)
            except (BinasciiError, ValueError) as exc:
                raise VisionProviderUnavailable("Invalid image_base64 payload.") from exc
        if not image_uri:
            return None
        if image_uri.startswith("gs://"):
            return self._load_gcs_image(image_uri)
        if image_uri.startswith(("http://", "https://")):
            try:
                response = requests.get(image_uri, auth=self._twilio_media_auth(image_uri), timeout=30)
                response.raise_for_status()
                return response.content
            except requests.RequestException as exc:
                raise VisionProviderUnavailable(f"Image media download failed: {exc}") from exc
        raise VisionProviderUnavailable("Only base64, gs://, http://, and https:// image inputs are supported.")

    def _twilio_media_auth(self, uri: str) -> tuple[str, str] | None:
        if "api.twilio.com" not in uri:
            return None
        if not settings.twilio_account_sid or not settings.twilio_auth_token:
            return None
        return settings.twilio_account_sid, settings.twilio_auth_token

    def _load_gcs_image(self, image_uri: str) -> bytes:
        from google.cloud import storage

        bucket_name, blob_name = image_uri.removeprefix("gs://").split("/", 1)
        bucket = storage.Client(project=settings.google_cloud_project).bucket(bucket_name)
        return bucket.blob(blob_name).download_as_bytes()

    def _provider_order(self) -> list[ProviderName]:
        route = store.get_provider_route(ProviderFeature.vision_ocr)
        if not route.enabled:
            return []

        providers = [route.primary]
        if route.allow_fallback and route.secondary:
            providers.append(route.secondary)
        return providers

    def _parse_json_response(self, text: str) -> dict[str, Any]:
        cleaned = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise VisionProviderUnavailable("Vision provider returned non-object JSON.")
        return parsed

    def _fallback_diagnosis(self, payload: DiagnosisRequest, *, source: str) -> DiagnosisResult:
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

        issue, action = self._localized_fallback(issue, action, payload.language)

        return DiagnosisResult(
            crop=payload.crop,
            likely_issue=issue,
            confidence=confidence,
            severity=severity,
            immediate_action=action,
            needs_expert_followup=True,
            source=source,
        )

    def _localized_fallback(self, issue: str, action: str, language: str | None) -> tuple[str, str]:
        if language == "mr-IN":
            translations = {
                "Possible sucking pest or leaf curl complex": "रसशोषक किड किंवा लीफ कर्लचा संभव",
                "Scout leaf underside, use yellow sticky traps, and request expert validation.": "पानांच्या खालची बाजू तपासा, पिवळे चिकट सापळे वापरा आणि तज्ञांकडून खात्री करून घ्या.",
                "Possible nutrient deficiency": "अन्नद्रव्य कमतरतेचा संभव",
                "Check soil test and avoid excess nitrogen until moisture is adequate.": "माती परीक्षण तपासा आणि ओलावा पुरेसा होईपर्यंत जास्त नायट्रोजन टाळा.",
                "Possible fungal leaf disease": "बुरशीजन्य पान रोगाचा संभव",
                "Remove infected leaves and consult RSK before spraying.": "बाधित पाने काढा आणि फवारणीपूर्वी RSK/तज्ञांचा सल्ला घ्या.",
                "General crop stress": "पिकावर सर्वसाधारण ताण दिसतो",
                "Capture a clear leaf and whole-plant photo for expert review.": "तज्ञ तपासणीसाठी पानाचा आणि संपूर्ण झाडाचा स्पष्ट फोटो पाठवा.",
            }
            return translations.get(issue, issue), translations.get(action, action)
        if language == "hi-IN":
            translations = {
                "Possible sucking pest or leaf curl complex": "रस चूसने वाले कीट या लीफ कर्ल की संभावना",
                "Scout leaf underside, use yellow sticky traps, and request expert validation.": "पत्ते के नीचे जांचें, पीले चिपचिपे ट्रैप लगाएं और विशेषज्ञ से पुष्टि करें।",
                "Possible nutrient deficiency": "पोषक तत्व की कमी की संभावना",
                "Check soil test and avoid excess nitrogen until moisture is adequate.": "मिट्टी जांच देखें और नमी पर्याप्त होने तक अधिक नाइट्रोजन से बचें।",
                "Possible fungal leaf disease": "फफूंदजनित पत्ती रोग की संभावना",
                "Remove infected leaves and consult RSK before spraying.": "संक्रमित पत्ते हटाएं और छिड़काव से पहले RSK/विशेषज्ञ से सलाह लें।",
                "General crop stress": "फसल पर सामान्य तनाव दिख रहा है",
                "Capture a clear leaf and whole-plant photo for expert review.": "विशेषज्ञ जांच के लिए पत्ती और पूरे पौधे की साफ फोटो भेजें।",
            }
            return translations.get(issue, issue), translations.get(action, action)
        return issue, action

    def _risk_from_text(self, value: str) -> RiskLevel:
        normalized = value.lower()
        if "critical" in normalized:
            return RiskLevel.critical
        if "high" in normalized:
            return RiskLevel.high
        if "low" in normalized:
            return RiskLevel.low
        return RiskLevel.medium

    def _bounded_float(self, value: object, *, default: float) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = default
        return max(0.0, min(1.0, number))

    def _optional_float(self, value: object) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _nutrient_value(self, value: object) -> str | float | None:
        number = self._optional_float(value)
        if number is not None:
            return number
        if value is None:
            return None
        text = str(value).lower()
        return text if text in {"low", "medium", "high"} else str(value)

    def _micronutrients(self, value: object) -> dict[str, str | float]:
        if not isinstance(value, dict):
            return {}
        result: dict[str, str | float] = {}
        for key, item in value.items():
            parsed = self._optional_float(item)
            result[str(key)] = parsed if parsed is not None else str(item)
        return result
