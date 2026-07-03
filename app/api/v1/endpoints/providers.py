from fastapi import APIRouter, HTTPException

from app.models.schemas import ProviderConfigResponse, ProviderConfigUpdate
from app.services.provider_config_service import ProviderConfigService

router = APIRouter()


@router.get("/config", response_model=ProviderConfigResponse)
def get_provider_config() -> ProviderConfigResponse:
    return ProviderConfigService().get_config()


@router.patch("/config", response_model=ProviderConfigResponse)
def update_provider_config(payload: ProviderConfigUpdate) -> ProviderConfigResponse:
    try:
        return ProviderConfigService().update_config(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
