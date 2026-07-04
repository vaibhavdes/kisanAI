from fastapi import APIRouter, Query

from app.models.schemas import ConversationLogRequest, ConversationLogResponse, ConversationMessage
from app.services.conversation_store import ConversationStore

router = APIRouter()


@router.post("/log", response_model=ConversationLogResponse)
def log_conversation(payload: ConversationLogRequest) -> ConversationLogResponse:
    return ConversationStore().log(payload)


@router.get("/{farmer_id}", response_model=list[ConversationMessage])
def recent_conversation(
    farmer_id: str,
    limit: int = Query(default=20, ge=1, le=100),
) -> list[ConversationMessage]:
    return ConversationStore().recent(farmer_id, limit=limit)
