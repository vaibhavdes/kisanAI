from app.models.schemas import ConversationLogRequest, ConversationLogResponse, ConversationMessage
from app.repositories.store import store


class ConversationStore:
    def log(self, payload: ConversationLogRequest) -> ConversationLogResponse:
        message = ConversationMessage(**payload.model_dump())
        store.save_conversation_message(message)
        return ConversationLogResponse(saved=True, message=message)

    def recent(self, farmer_id: str, limit: int = 20) -> list[ConversationMessage]:
        return store.list_conversation_messages(farmer_id, limit=limit)
