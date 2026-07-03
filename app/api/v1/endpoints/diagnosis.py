from fastapi import APIRouter, HTTPException

from app.models.schemas import DiagnosisRequest, DiagnosisResponse
from app.repositories.store import store
from app.services.expert_service import ExpertService
from app.services.vision_ocr_service import VisionOcrService, VisionProviderUnavailable

router = APIRouter()


@router.post("/log", response_model=DiagnosisResponse)
def log_diagnosis(payload: DiagnosisRequest) -> DiagnosisResponse:
    farmer = store.get_farmer(payload.farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    try:
        diagnosis = VisionOcrService().diagnose_crop_health(farmer, payload)
    except VisionProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    ticket = ExpertService().create_ticket(farmer, payload, diagnosis)
    store.save_ticket(ticket)
    return DiagnosisResponse(**diagnosis.model_dump(), expert_ticket=ticket)
