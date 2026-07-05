from fastapi import APIRouter, HTTPException

from fastapi import Query

from app.models.schemas import ProviderConfigResponse, ProviderConfigUpdate, ServiceAuditLogResponse
from app.services.provider_config_service import ProviderConfigService
from app.services.service_audit_log_service import ServiceAuditLogService

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


@router.get("/audit", response_model=ServiceAuditLogResponse)
def service_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    farmer_id: str | None = None,
) -> ServiceAuditLogResponse:
    return ServiceAuditLogResponse(logs=ServiceAuditLogService().list(limit=limit, farmer_id=farmer_id))
