from fastapi import APIRouter, HTTPException

from app.models.schemas import ExpertTicket, ExpertTicketUpdateRequest
from app.repositories.store import store
from app.services.expert_service import ExpertService

router = APIRouter()


@router.get("/tickets/{farmer_id}", response_model=list[ExpertTicket])
def tickets_for_farmer(farmer_id: str) -> list[ExpertTicket]:
    return store.list_tickets(farmer_id)


@router.get("/ticket/{ticket_id}", response_model=ExpertTicket)
def ticket_detail(ticket_id: str) -> ExpertTicket:
    ticket = store.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Expert ticket not found")
    return ticket


@router.patch("/ticket/{ticket_id}", response_model=ExpertTicket)
def update_ticket(ticket_id: str, payload: ExpertTicketUpdateRequest) -> ExpertTicket:
    ticket = store.get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Expert ticket not found")
    return ExpertService().update_ticket(ticket, payload)
