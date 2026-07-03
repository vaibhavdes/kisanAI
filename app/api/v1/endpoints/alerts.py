from fastapi import APIRouter, HTTPException

from app.models.schemas import AlertDeliveryRequest, AlertDeliveryResponse
from app.repositories.store import store
from app.services.alert_delivery_service import AlertDeliveryService

router = APIRouter()


@router.post("/deliver", response_model=AlertDeliveryResponse)
def deliver_alert(payload: AlertDeliveryRequest) -> AlertDeliveryResponse:
    farmer = store.get_farmer(payload.farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return AlertDeliveryService().deliver(farmer, payload)
