from typing import Any

from fastapi import APIRouter

from app.services.dialogflow_service import DialogflowService

router = APIRouter()


@router.post("/webhook")
def dialogflow_webhook(payload: dict[str, Any]) -> dict[str, Any]:
    return DialogflowService().handle_webhook(payload)
