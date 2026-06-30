from fastapi import APIRouter

from app.models.schemas import ExpertTicket
from app.repositories.memory_store import store

router = APIRouter()


@router.get("/tickets/{farmer_id}", response_model=list[ExpertTicket])
def tickets_for_farmer(farmer_id: str) -> list[ExpertTicket]:
    return store.list_tickets(farmer_id)

