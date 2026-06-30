from fastapi import APIRouter

from app.models.schemas import FarmerCreate, FarmerResponse
from app.repositories.memory_store import store

router = APIRouter()


@router.post("", response_model=FarmerResponse)
def create_farmer(payload: FarmerCreate) -> FarmerResponse:
    return store.create_farmer(payload)

