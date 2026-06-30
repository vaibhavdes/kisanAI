from fastapi import APIRouter, HTTPException

from app.models.schemas import DiagnosisRequest, DiagnosisResponse
from app.repositories.memory_store import store
from app.services.expert_service import ExpertService
from app.services.gemini_service import GeminiService

router = APIRouter()


@router.post("/log", response_model=DiagnosisResponse)
def log_diagnosis(payload: DiagnosisRequest) -> DiagnosisResponse:
    farmer = store.get_farmer(payload.farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    diagnosis = GeminiService().diagnose_crop_health(farmer, payload)
    ticket = ExpertService().create_ticket(farmer, payload, diagnosis)
    store.save_ticket(ticket)
    return DiagnosisResponse(**diagnosis.model_dump(), expert_ticket=ticket)

