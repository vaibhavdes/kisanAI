from time import perf_counter
from typing import Any

from app.models.schemas import ServiceAuditLog
from app.repositories.store import store


MAX_BODY_VALUE_LENGTH = 800


class ServiceAuditLogService:
    def record(
        self,
        *,
        service: str,
        operation: str,
        provider: str | None,
        success: bool,
        farmer_id: str | None = None,
        channel: str | None = None,
        status_code: int | None = None,
        duration_ms: int | None = None,
        request_body: dict[str, Any] | None = None,
        response_body: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> ServiceAuditLog:
        return store.save_service_audit_log(
            ServiceAuditLog(
                farmer_id=farmer_id,
                channel=channel,
                service=service,
                operation=operation,
                provider=provider,
                status_code=status_code,
                success=success,
                duration_ms=duration_ms,
                request_body=self._clean(request_body),
                response_body=self._clean(response_body),
                error=str(error)[:MAX_BODY_VALUE_LENGTH] if error else None,
            )
        )

    def list(self, *, limit: int = 100, farmer_id: str | None = None) -> list[ServiceAuditLog]:
        return store.list_service_audit_logs(limit=limit, farmer_id=farmer_id)

    def start(self) -> float:
        return perf_counter()

    def elapsed_ms(self, start: float) -> int:
        return max(0, round((perf_counter() - start) * 1000))

    def _clean(self, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if not value:
            return None
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if item is None:
                cleaned[key] = None
            elif isinstance(item, (int, float, bool)):
                cleaned[key] = item
            elif isinstance(item, list):
                cleaned[key] = item[:8]
            elif isinstance(item, dict):
                cleaned[key] = {str(k): str(v)[:160] for k, v in list(item.items())[:20]}
            else:
                cleaned[key] = str(item)[:MAX_BODY_VALUE_LENGTH]
        return cleaned
