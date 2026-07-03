from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    AlertDeliveryRequest,
    AlertDeliveryResponse,
    ProactiveAlertRunRequest,
    ProactiveAlertRunResponse,
)
from app.repositories.store import store
from app.services.alert_delivery_service import AlertDeliveryService
from app.services.proactive_alert_service import ProactiveAlertService

router = APIRouter()


@router.post("/deliver", response_model=AlertDeliveryResponse)
def deliver_alert(payload: AlertDeliveryRequest) -> AlertDeliveryResponse:
    farmer = store.get_farmer(payload.farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return AlertDeliveryService().deliver(farmer, payload)


@router.post("/run-daily", response_model=ProactiveAlertRunResponse)
def run_daily_alerts(payload: ProactiveAlertRunRequest) -> ProactiveAlertRunResponse:
    return ProactiveAlertService().run_daily(payload)
