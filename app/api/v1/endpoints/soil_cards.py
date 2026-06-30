from fastapi import APIRouter

from app.models.schemas import SoilCardExtractionRequest, SoilCardExtractionResponse
from app.services.soil_card_vision_service import SoilCardVisionService

router = APIRouter()


@router.post("/extract", response_model=SoilCardExtractionResponse)
def extract_soil_card(payload: SoilCardExtractionRequest) -> SoilCardExtractionResponse:
    return SoilCardVisionService().extract(payload)

