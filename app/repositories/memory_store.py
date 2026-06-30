from app.models.schemas import ExpertTicket, FarmerCreate, FarmerResponse


class MemoryStore:
    def __init__(self) -> None:
        self.farmers: dict[str, FarmerResponse] = {}
        self.tickets: list[ExpertTicket] = []

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

    def reset(self) -> None:
        self.farmers.clear()
        self.tickets.clear()


store = MemoryStore()

