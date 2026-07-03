from fastapi import APIRouter

from app.models.schemas import ChannelReceiptRequest, ChannelReceiptResponse, WhatsAppWebhookRequest, WhatsAppWebhookResponse
from app.services.channel_receipt_service import ChannelReceiptService
from app.services.whatsapp_service import WhatsAppService

router = APIRouter()


@router.post("/webhook", response_model=WhatsAppWebhookResponse)
def whatsapp_webhook(payload: WhatsAppWebhookRequest) -> WhatsAppWebhookResponse:
    return WhatsAppService().handle_message(payload)


@router.post("/receipt", response_model=ChannelReceiptResponse)
def whatsapp_receipt(payload: ChannelReceiptRequest) -> ChannelReceiptResponse:
    return ChannelReceiptService().save_receipt(payload, channel="whatsapp")
