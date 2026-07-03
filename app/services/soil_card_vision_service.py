import re

from app.models.schemas import SoilCardExtractionRequest, SoilCardExtractionResponse
from app.services.vision_ocr_service import VisionOcrService


class SoilCardVisionService:
    def extract(self, payload: SoilCardExtractionRequest) -> SoilCardExtractionResponse:
        if (payload.image_uri or payload.image_base64) and not payload.extracted_text:
            return VisionOcrService().extract_soil_card(payload)

        text = payload.extracted_text or ""
        parsed = {
            "ph": self._number_after(text, r"\bph\b"),
            "ec": self._number_after(text, r"\bec\b"),
            "organic_carbon": self._number_after(text, r"(organic carbon|oc)"),
            "nitrogen": self._value_after(text, r"(nitrogen|available n|\bn\b)"),
            "phosphorus": self._value_after(text, r"(phosphorus|available p|\bp\b)"),
            "potassium": self._value_after(text, r"(potassium|available k|\bk\b)"),
        }
        found_count = sum(value is not None for value in parsed.values())
        confidence = min(0.9, 0.25 + found_count * 0.12)

        return SoilCardExtractionResponse(
            source="text_parser",
            confidence=confidence,
            needs_manual_review=confidence < 0.7,
            raw_text=text,
            **parsed,
        )

    def _number_after(self, text: str, label_pattern: str) -> float | None:
        match = re.search(label_pattern + r"[^0-9]{0,12}([0-9]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
        return float(match.groups()[-1]) if match else None

    def _value_after(self, text: str, label_pattern: str) -> str | float | None:
        number = self._number_after(text, label_pattern)
        if number is not None:
            return number
        match = re.search(label_pattern + r"[^a-z]{0,12}(low|medium|high)", text, re.IGNORECASE)
        return match.groups()[-1].lower() if match else None
