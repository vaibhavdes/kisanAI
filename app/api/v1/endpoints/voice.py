from fastapi import APIRouter, HTTPException

from app.models.schemas import VoiceIntakeRequest, VoiceIntakeResponse
from app.repositories.store import store
from app.services.voice_service import VoiceService

router = APIRouter()


@router.post("/intake", response_model=VoiceIntakeResponse)
def voice_intake(payload: VoiceIntakeRequest) -> VoiceIntakeResponse:
    farmer = store.get_farmer(payload.farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return VoiceService().handle_intake(farmer, payload)
