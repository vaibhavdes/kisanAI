from fastapi import APIRouter

from app.models.schemas import SmsWebhookRequest, SmsWebhookResponse
from app.services.sms_service import SmsService

router = APIRouter()


@router.post("/webhook", response_model=SmsWebhookResponse)
def sms_webhook(payload: SmsWebhookRequest) -> SmsWebhookResponse:
    return SmsService().handle_message(payload)

