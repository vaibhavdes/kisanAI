from fastapi import APIRouter

from app.models.schemas import WhatsAppWebhookRequest, WhatsAppWebhookResponse
from app.services.whatsapp_service import WhatsAppService

router = APIRouter()


@router.post("/message", response_model=WhatsAppWebhookResponse)
def app_chat_message(payload: WhatsAppWebhookRequest) -> WhatsAppWebhookResponse:
    return WhatsAppService().handle_message(payload, channel="app", send_outbound=False)
