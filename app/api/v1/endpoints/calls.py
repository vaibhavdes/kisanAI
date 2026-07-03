from fastapi import APIRouter

from app.models.schemas import ChannelReceiptRequest, ChannelReceiptResponse, VoiceCallWebhookRequest, VoiceCallWebhookResponse
from app.services.channel_receipt_service import ChannelReceiptService
from app.services.call_service import CallService

router = APIRouter()


@router.post("/webhook", response_model=VoiceCallWebhookResponse)
def voice_call_webhook(payload: VoiceCallWebhookRequest) -> VoiceCallWebhookResponse:
    return CallService().handle_call(payload)


@router.post("/receipt", response_model=ChannelReceiptResponse)
def voice_call_receipt(payload: ChannelReceiptRequest) -> ChannelReceiptResponse:
    return ChannelReceiptService().save_receipt(payload, channel="voice_call")
