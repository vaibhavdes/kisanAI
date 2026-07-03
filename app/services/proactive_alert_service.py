from datetime import date

from app.models.schemas import (
    AlertDeliveryRequest,
    AlertPlan,
    AlertPriority,
    AlertRunRecord,
    ConversationLogRequest,
    ConversationRole,
    DrySpellAdvisoryRequest,
    FarmerResponse,
    ProactiveAlertFarmerResult,
    ProactiveAlertRunRequest,
    ProactiveAlertRunResponse,
)
from app.repositories.store import store
from app.services.alert_delivery_service import AlertDeliveryService
from app.services.alert_priority_policy import AlertPriorityPolicy
from app.services.conversation_store import ConversationStore
from app.services.weather_context_service import WeatherProviderUnavailable
from app.services.weather_service import WeatherService


PRIORITY_RANK = {
    AlertPriority.low: 1,
    AlertPriority.medium: 2,
    AlertPriority.high: 3,
    AlertPriority.urgent: 4,
}


class ProactiveAlertService:
    def run_daily(self, payload: ProactiveAlertRunRequest) -> ProactiveAlertRunResponse:
        farmers = self._farmers_for_run(payload)
        run_date = payload.run_date or date.today().isoformat()
        run_key = payload.idempotency_key or f"daily-dry-spell:{run_date}:{payload.crop}"
        results = [self._process_farmer(farmer, payload, run_date, run_key) for farmer in farmers]
        return ProactiveAlertRunResponse(
            processed=len(results),
            generated=sum(1 for result in results if result.generated),
            skipped=sum(1 for result in results if not result.generated),
            delivered=sum(1 for result in results if result.delivery and result.delivery.overall_status in {"sent", "dry_run"}),
            run_date=run_date,
            idempotency_key=run_key,
            results=results,
        )

    def _farmers_for_run(self, payload: ProactiveAlertRunRequest) -> list[FarmerResponse]:
        if payload.farmer_ids:
            farmers = [store.get_farmer(farmer_id) for farmer_id in payload.farmer_ids[: payload.max_farmers]]
            return [farmer for farmer in farmers if farmer is not None]
        return store.list_farmers(limit=payload.max_farmers)

    def _process_farmer(
        self,
        farmer: FarmerResponse,
        payload: ProactiveAlertRunRequest,
        run_date: str,
        run_key: str,
    ) -> ProactiveAlertFarmerResult:
        if not payload.rainfall_forecast_mm and (farmer.farm.latitude is None or farmer.farm.longitude is None):
            return ProactiveAlertFarmerResult(
                farmer_id=farmer.id,
                generated=False,
                skipped_reason="farm_location_required",
            )

        try:
            advisory = WeatherService().build_dry_spell_advisory(
                farmer,
                DrySpellAdvisoryRequest(
                    farmer_id=farmer.id,
                    crop=payload.crop,
                    rainfall_forecast_mm=payload.rainfall_forecast_mm,
                    soil_moisture=payload.soil_moisture,
                    temperature_c=payload.temperature_c,
                ),
            )
        except (ValueError, WeatherProviderUnavailable) as exc:
            return ProactiveAlertFarmerResult(
                farmer_id=farmer.id,
                generated=False,
                skipped_reason=str(exc),
            )

        alert_plan = AlertPriorityPolicy().build_plan(
            advisory.risk_level,
            reason=f"Daily dry-spell risk is {advisory.risk_level.value}.",
        )
        if PRIORITY_RANK[alert_plan.priority] < PRIORITY_RANK[payload.min_priority]:
            return ProactiveAlertFarmerResult(
                farmer_id=farmer.id,
                generated=False,
                skipped_reason=f"priority_below_{payload.min_priority.value}",
                risk_level=advisory.risk_level,
                priority=alert_plan.priority,
                advisory=advisory.advisory,
            )

        message = self._message(advisory.advisory, advisory.fertilizer_note)
        alert_key = self._alert_key(run_key, farmer.id, advisory.risk_level, alert_plan.priority)
        if payload.dedupe and store.get_alert_run_record(alert_key):
            return ProactiveAlertFarmerResult(
                farmer_id=farmer.id,
                generated=False,
                skipped_reason="duplicate_alert",
                risk_level=advisory.risk_level,
                priority=alert_plan.priority,
                advisory=message,
            )

        delivery = AlertDeliveryService().deliver(
            farmer,
            AlertDeliveryRequest(
                farmer_id=farmer.id,
                message=message,
                alert_plan=alert_plan,
                language=farmer.language,
            ),
        )
        self._log_alert(farmer.id, farmer.language, message, alert_plan)
        store.save_alert_run_record(
            AlertRunRecord(
                key=alert_key,
                farmer_id=farmer.id,
                crop=payload.crop,
                run_date=run_date,
                risk_level=advisory.risk_level,
                priority=alert_plan.priority,
                message=message,
                delivery_status=delivery.overall_status,
            )
        )
        return ProactiveAlertFarmerResult(
            farmer_id=farmer.id,
            generated=True,
            risk_level=advisory.risk_level,
            priority=alert_plan.priority,
            advisory=message,
            delivery=delivery,
        )

    def _message(self, advisory: str, fertilizer_note: str) -> str:
        if fertilizer_note and fertilizer_note not in advisory:
            return f"{advisory} {fertilizer_note}"
        return advisory

    def _alert_key(
        self,
        run_key: str,
        farmer_id: str,
        risk_level,
        priority: AlertPriority,
    ) -> str:
        safe_run_key = run_key.replace("/", "_")
        return f"{safe_run_key}:{farmer_id}:{risk_level.value}:{priority.value}"

    def _log_alert(self, farmer_id: str, language: str, message: str, alert_plan: AlertPlan) -> None:
        ConversationStore().log(
            ConversationLogRequest(
                farmer_id=farmer_id,
                role=ConversationRole.assistant,
                text=message,
                language=language,
                channel="proactive_alert",
                intent="daily_dry_spell_alert",
                metadata={
                    "priority": alert_plan.priority.value,
                    "channels": ",".join(alert_plan.channels),
                    "reason": alert_plan.reason,
                },
            )
        )
