from fastapi import APIRouter, HTTPException

from app.models.schemas import LiveTokenRequest, LiveTokenResponse
from app.services.live_call_service import LiveCallService

router = APIRouter()


@router.post("/token", response_model=LiveTokenResponse)
def create_live_token(payload: LiveTokenRequest) -> LiveTokenResponse:
    try:
        return LiveCallService().create_token(payload)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Gemini Live token unavailable: {exc}") from exc
