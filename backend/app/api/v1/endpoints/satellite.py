from fastapi import APIRouter, HTTPException

from app.models.schemas import SatelliteSignalRequest, SatelliteSignalResponse
from app.repositories.store import store
from app.services.earth_engine_service import EarthEngineService

router = APIRouter()


@router.post("/farm-signal", response_model=SatelliteSignalResponse)
def farm_signal(payload: SatelliteSignalRequest) -> SatelliteSignalResponse:
    latitude = payload.latitude
    longitude = payload.longitude
    farmer_id = payload.farmer_id

    if farmer_id:
        farmer = store.get_farmer(farmer_id)
        if farmer is None:
            raise HTTPException(status_code=404, detail="Farmer not found")
        latitude = latitude if latitude is not None else farmer.farm.latitude
        longitude = longitude if longitude is not None else farmer.farm.longitude

    if latitude is None or longitude is None:
        raise HTTPException(status_code=422, detail="Farm latitude and longitude are required")

    try:
        return EarthEngineService().get_farm_signal(
            farmer_id=farmer_id,
            latitude=latitude,
            longitude=longitude,
            polygon=payload.polygon,
            buffer_m=payload.buffer_m,
            days=payload.days,
            history_periods=payload.history_periods,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Earth Engine satellite signal unavailable: {exc}") from exc
