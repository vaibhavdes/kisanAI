from fastapi import APIRouter, HTTPException

from app.models.schemas import SensorReading, SensorReadingCreate, SensorReadingResponse
from app.repositories.store import store
from app.services.sensor_service import SensorService

router = APIRouter()


@router.post("/readings", response_model=SensorReadingResponse)
def create_sensor_reading(payload: SensorReadingCreate) -> SensorReadingResponse:
    try:
        return SensorService().save_reading(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/readings/{farmer_id}", response_model=list[SensorReading])
def list_sensor_readings(farmer_id: str, limit: int = 20) -> list[SensorReading]:
    return store.list_sensor_readings(farmer_id, limit=limit)


@router.get("/latest/{farmer_id}", response_model=SensorReading | None)
def latest_sensor_reading(farmer_id: str, sensor_id: str | None = None) -> SensorReading | None:
    return store.latest_sensor_reading(farmer_id, sensor_id=sensor_id)
