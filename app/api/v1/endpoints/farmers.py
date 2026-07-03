from fastapi import APIRouter

from app.models.schemas import FarmerCreate, FarmerIdentifyRequest, FarmerIdentifyResponse, FarmerResponse
from app.repositories.store import store

router = APIRouter()


@router.post("", response_model=FarmerResponse)
def create_farmer(payload: FarmerCreate) -> FarmerResponse:
    return store.create_farmer(payload)


@router.post("/identify", response_model=FarmerIdentifyResponse)
def identify_farmer(payload: FarmerIdentifyRequest) -> FarmerIdentifyResponse:
    return store.identify_farmer(payload)
