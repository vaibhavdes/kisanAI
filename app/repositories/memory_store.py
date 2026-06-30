from app.models.schemas import ConversationMessage, ExpertTicket, FarmerCreate, FarmerResponse


class MemoryStore:
    def __init__(self) -> None:
        self.farmers: dict[str, FarmerResponse] = {}
        self.tickets: list[ExpertTicket] = []
        self.conversations: list[ConversationMessage] = []

    def create_farmer(self, payload: FarmerCreate) -> FarmerResponse:
        farmer = FarmerResponse(**payload.model_dump())
        self.farmers[farmer.id] = farmer
        return farmer

    def get_farmer(self, farmer_id: str) -> FarmerResponse | None:
        return self.farmers.get(farmer_id)

    def save_ticket(self, ticket: ExpertTicket) -> ExpertTicket:
        self.tickets.append(ticket)
        return ticket

    def list_tickets(self, farmer_id: str) -> list[ExpertTicket]:
        return [ticket for ticket in self.tickets if ticket.farmer_id == farmer_id]

    def save_conversation_message(self, message: ConversationMessage) -> ConversationMessage:
        self.conversations.append(message)
        return message

    def list_conversation_messages(self, farmer_id: str, limit: int = 20) -> list[ConversationMessage]:
        messages = [message for message in self.conversations if message.farmer_id == farmer_id]
        return messages[-limit:]

    def reset(self) -> None:
        self.farmers.clear()
        self.tickets.clear()
        self.conversations.clear()


store = MemoryStore()
