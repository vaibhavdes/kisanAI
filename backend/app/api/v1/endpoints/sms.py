from fastapi import APIRouter

from app.models.schemas import ChannelReceiptRequest, ChannelReceiptResponse, SmsWebhookRequest, SmsWebhookResponse
from app.services.channel_receipt_service import ChannelReceiptService
from app.services.sms_service import SmsService

router = APIRouter()


@router.post("/webhook", response_model=SmsWebhookResponse)
def sms_webhook(payload: SmsWebhookRequest) -> SmsWebhookResponse:
    return SmsService().handle_message(payload)


@router.post("/receipt", response_model=ChannelReceiptResponse)
def sms_receipt(payload: ChannelReceiptRequest) -> ChannelReceiptResponse:
    return ChannelReceiptService().save_receipt(payload, channel="sms")
