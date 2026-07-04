from fastapi import APIRouter, HTTPException

from app.models.schemas import WeatherContextRequest, WeatherContextResponse
from app.services.weather_context_service import WeatherContextService, WeatherProviderUnavailable

router = APIRouter()


@router.post("/context", response_model=WeatherContextResponse)
def weather_context(payload: WeatherContextRequest) -> WeatherContextResponse:
    try:
        return WeatherContextService().get_context(payload)
    except WeatherProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
