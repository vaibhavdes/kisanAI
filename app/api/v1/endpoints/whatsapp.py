from fastapi import APIRouter

from app.models.schemas import WhatsAppWebhookRequest, WhatsAppWebhookResponse
from app.services.whatsapp_service import WhatsAppService

router = APIRouter()


@router.post("/webhook", response_model=WhatsAppWebhookResponse)
def whatsapp_webhook(payload: WhatsAppWebhookRequest) -> WhatsAppWebhookResponse:
    return WhatsAppService().handle_message(payload)

