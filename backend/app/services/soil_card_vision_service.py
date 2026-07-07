import re

from app.models.schemas import FarmerResponse, SoilCardExtractionRequest, SoilCardExtractionResponse
from app.repositories.store import store
from app.services.vision_ocr_service import VisionOcrService


class SoilCardVisionService:
    def extract(self, payload: SoilCardExtractionRequest) -> SoilCardExtractionResponse:
        if (payload.image_uri or payload.image_base64) and not payload.extracted_text:
            response = VisionOcrService().extract_soil_card(payload)
            return self._persist_if_requested(payload, response)

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

        response = SoilCardExtractionResponse(
            source="text_parser",
            confidence=confidence,
            needs_manual_review=confidence < 0.7,
            raw_text=text,
            **parsed,
        )
        return self._persist_if_requested(payload, response)

    def _persist_if_requested(
        self,
        payload: SoilCardExtractionRequest,
        response: SoilCardExtractionResponse,
    ) -> SoilCardExtractionResponse:
        if not payload.farmer_id:
            return response
        farmer = store.get_farmer(payload.farmer_id)
        if farmer is None:
            return response
        updated = self._apply_to_farmer(farmer, response)
        saved = store.save_farmer(updated)
        data = response.model_dump()
        data["persisted"] = True
        data["farmer"] = saved
        return SoilCardExtractionResponse(**data)

    def _apply_to_farmer(
        self,
        farmer: FarmerResponse,
        response: SoilCardExtractionResponse,
    ) -> FarmerResponse:
        data = farmer.model_dump()
        farm = farmer.farm.model_dump()
        if response.ph is not None:
            farm["soil_ph"] = response.ph
        if response.ec is not None:
            farm["soil_ec"] = response.ec
        if response.organic_carbon is not None:
            farm["organic_carbon"] = response.organic_carbon
        if response.nitrogen is not None:
            farm["soil_nitrogen"] = response.nitrogen
        if response.phosphorus is not None:
            farm["soil_phosphorus"] = response.phosphorus
        if response.potassium is not None:
            farm["soil_potassium"] = response.potassium
        if farm.get("soil_type") in {None, "unknown"}:
            farm["soil_type"] = self._soil_type_from_text(response.raw_text) or "unknown"
        data["farm"] = farm
        return FarmerResponse(**data)

    def _soil_type_from_text(self, text: str | None) -> str | None:
        normalized = (text or "").lower()
        for soil_type in ["black", "red", "sandy", "clay", "alluvial"]:
            if soil_type in normalized:
                return soil_type
        return None

    def _number_after(self, text: str, label_pattern: str) -> float | None:
        match = re.search(label_pattern + r"[^0-9]{0,12}([0-9]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
        return float(match.groups()[-1]) if match else None

    def _value_after(self, text: str, label_pattern: str) -> str | float | None:
        number = self._number_after(text, label_pattern)
        if number is not None:
            return number
        match = re.search(label_pattern + r"[^a-z]{0,12}(low|medium|high)", text, re.IGNORECASE)
        return match.groups()[-1].lower() if match else None
