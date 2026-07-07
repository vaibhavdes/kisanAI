import base64
import json

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    AlertDeliveryRequest,
    AlertDeliveryResponse,
    AlertScheduleConfig,
    AlertScheduleConfigUpdate,
    PubSubPushRequest,
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


@router.get("/schedule", response_model=AlertScheduleConfig)
def get_alert_schedule() -> AlertScheduleConfig:
    return store.get_alert_schedule_config()


@router.patch("/schedule", response_model=AlertScheduleConfig)
def update_alert_schedule(payload: AlertScheduleConfigUpdate) -> AlertScheduleConfig:
    config = store.get_alert_schedule_config()
    data = config.model_dump()
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            data[field] = value
    return store.save_alert_schedule_config(AlertScheduleConfig(**data))


@router.post("/run-daily/pubsub", response_model=ProactiveAlertRunResponse)
def run_daily_alerts_from_pubsub(payload: PubSubPushRequest) -> ProactiveAlertRunResponse:
    data = _decode_pubsub_payload(payload)
    request = ProactiveAlertRunRequest(**data)
    if payload.message.messageId and not request.idempotency_key:
        request.idempotency_key = f"pubsub:{payload.message.messageId}"
    return ProactiveAlertService().run_daily(request)


def _decode_pubsub_payload(payload: PubSubPushRequest) -> dict:
    if not payload.message.data:
        return {}
    try:
        decoded = base64.b64decode(payload.message.data).decode("utf-8")
        return json.loads(decoded) if decoded else {}
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid Pub/Sub payload: {exc}") from exc
