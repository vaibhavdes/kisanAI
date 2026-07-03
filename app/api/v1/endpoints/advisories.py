from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    CropStageAdvisoryRequest,
    CropStageAdvisoryResponse,
    DrySpellAdvisoryRequest,
    DrySpellAdvisoryResponse,
)
from app.repositories.store import store
from app.services.crop_stage_advisory_service import CropStageAdvisoryService
from app.services.weather_service import WeatherService
from app.services.weather_context_service import WeatherProviderUnavailable

router = APIRouter()


@router.post("/dry-spell", response_model=DrySpellAdvisoryResponse)
def dry_spell_advisory(payload: DrySpellAdvisoryRequest) -> DrySpellAdvisoryResponse:
    farmer = store.get_farmer(payload.farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    try:
        return WeatherService().build_dry_spell_advisory(farmer, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except WeatherProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/crop-stage", response_model=CropStageAdvisoryResponse)
def crop_stage_advisory(payload: CropStageAdvisoryRequest) -> CropStageAdvisoryResponse:
    farmer = store.get_farmer(payload.farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return CropStageAdvisoryService().build_advisory(farmer, payload)
