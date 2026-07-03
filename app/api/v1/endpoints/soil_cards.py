from fastapi import APIRouter, HTTPException

from app.models.schemas import SoilCardExtractionRequest, SoilCardExtractionResponse
from app.services.soil_card_vision_service import SoilCardVisionService
from app.services.vision_ocr_service import VisionProviderUnavailable

router = APIRouter()


@router.post("/extract", response_model=SoilCardExtractionResponse)
def extract_soil_card(payload: SoilCardExtractionRequest) -> SoilCardExtractionResponse:
    try:
        return SoilCardVisionService().extract(payload)
    except VisionProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
