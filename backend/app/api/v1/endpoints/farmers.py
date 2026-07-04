from fastapi import APIRouter

from app.models.schemas import FarmerCreate, FarmerIdentifyRequest, FarmerIdentifyResponse, FarmerResponse
from app.repositories.store import store

router = APIRouter()


@router.post("", response_model=FarmerResponse)
def create_farmer(payload: FarmerCreate) -> FarmerResponse:
    return store.create_farmer(payload)


@router.get("", response_model=list[FarmerResponse])
def list_farmers(limit: int = 100) -> list[FarmerResponse]:
    return store.list_farmers(limit=limit)


@router.post("/identify", response_model=FarmerIdentifyResponse)
def identify_farmer(payload: FarmerIdentifyRequest) -> FarmerIdentifyResponse:
    return store.identify_farmer(payload)
