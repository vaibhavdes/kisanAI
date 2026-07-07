from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    VoiceIntakeRequest,
    VoiceIntakeResponse,
    VoiceSpeakRequest,
    VoiceSpeakResponse,
    VoiceTranscribeRequest,
    VoiceTranscribeResponse,
)
from app.repositories.store import store
from app.services.voice_service import VoiceProviderUnavailable, VoiceService

router = APIRouter()


@router.post("/intake", response_model=VoiceIntakeResponse)
def voice_intake(payload: VoiceIntakeRequest) -> VoiceIntakeResponse:
    farmer = store.get_farmer(payload.farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    try:
        return VoiceService().handle_intake(farmer, payload)
    except VoiceProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/transcribe", response_model=VoiceTranscribeResponse)
def transcribe_voice(payload: VoiceTranscribeRequest) -> VoiceTranscribeResponse:
    try:
        return VoiceService().transcribe(payload)
    except VoiceProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/speak", response_model=VoiceSpeakResponse)
def speak_voice(payload: VoiceSpeakRequest) -> VoiceSpeakResponse:
    try:
        return VoiceService().speak(payload)
    except VoiceProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
