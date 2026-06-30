from fastapi import APIRouter

from app.models.schemas import VoiceCallWebhookRequest, VoiceCallWebhookResponse
from app.services.call_service import CallService

router = APIRouter()


@router.post("/webhook", response_model=VoiceCallWebhookResponse)
def voice_call_webhook(payload: VoiceCallWebhookRequest) -> VoiceCallWebhookResponse:
    return CallService().handle_call(payload)

