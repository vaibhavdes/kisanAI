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
    RiskLevel,
    ScheduledAlertKind,
)
from app.repositories.store import store
from app.services.alert_delivery_service import AlertDeliveryService
from app.services.alert_priority_policy import AlertPriorityPolicy
from app.services.conversation_store import ConversationStore
from app.services.earth_engine_service import EarthEngineService
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
        default_key_prefix = "daily-dry-spell" if payload.kind == ScheduledAlertKind.weather else "daily-satellite"
        run_key = payload.idempotency_key or f"{default_key_prefix}:{run_date}:{payload.crop}"
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
        config = store.get_alert_schedule_config()
        if payload.kind == ScheduledAlertKind.weather:
            if not config.weather_enabled:
                return ProactiveAlertFarmerResult(farmer_id=farmer.id, generated=False, skipped_reason="weather_alerts_disabled")
            if payload.respect_frequency and not self._is_frequency_due(run_date, config.weather_frequency_days):
                return ProactiveAlertFarmerResult(farmer_id=farmer.id, generated=False, skipped_reason="weather_frequency_not_due")
            return self._process_weather_farmer(farmer, payload, run_date, run_key)

        if not config.satellite_enabled:
            return ProactiveAlertFarmerResult(farmer_id=farmer.id, generated=False, skipped_reason="satellite_alerts_disabled")
        if payload.respect_frequency and not self._is_frequency_due(run_date, config.satellite_frequency_days):
            return ProactiveAlertFarmerResult(farmer_id=farmer.id, generated=False, skipped_reason="satellite_frequency_not_due")
        return self._process_satellite_farmer(farmer, payload, run_date, run_key)

    def _process_weather_farmer(
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
            crop = self._crop_for_alert(farmer, payload.crop)
            advisory = WeatherService().build_dry_spell_advisory(
                farmer,
                DrySpellAdvisoryRequest(
                    farmer_id=farmer.id,
                    crop=crop,
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
        alert_plan = AlertPlan(
            priority=alert_plan.priority,
            channels=["whatsapp", "voice_call", "sms"],
            reason=f"Morning weather alert for {crop}; WhatsApp plus Authkey voice and SMS when configured.",
            call_required=True,
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

        message = self._weather_message(farmer, crop, advisory.advisory, advisory.fertilizer_note)
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
                requires_whatsapp_template=True,
            ),
        )
        self._log_alert(farmer.id, farmer.language, message, alert_plan)
        store.save_alert_run_record(
            AlertRunRecord(
                key=alert_key,
                farmer_id=farmer.id,
                crop=crop,
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

    def _process_satellite_farmer(
        self,
        farmer: FarmerResponse,
        payload: ProactiveAlertRunRequest,
        run_date: str,
        run_key: str,
    ) -> ProactiveAlertFarmerResult:
        if farmer.farm.latitude is None or farmer.farm.longitude is None:
            return ProactiveAlertFarmerResult(
                farmer_id=farmer.id,
                generated=False,
                skipped_reason="farm_location_required",
            )
        try:
            signal = EarthEngineService().get_farm_signal(
                farmer_id=farmer.id,
                latitude=farmer.farm.latitude,
                longitude=farmer.farm.longitude,
                history_periods=3,
            )
        except Exception as exc:
            return ProactiveAlertFarmerResult(
                farmer_id=farmer.id,
                generated=False,
                skipped_reason=f"satellite_unavailable: {exc}",
            )

        priority = AlertPriority.high if signal.water_stress == "high" else AlertPriority.medium if signal.water_stress == "medium" else AlertPriority.low
        if PRIORITY_RANK[priority] < PRIORITY_RANK[payload.min_priority]:
            return ProactiveAlertFarmerResult(
                farmer_id=farmer.id,
                generated=False,
                skipped_reason=f"priority_below_{payload.min_priority.value}",
                risk_level=self._risk_from_satellite(signal.water_stress),
                priority=priority,
            )
        crop = self._crop_for_alert(farmer, payload.crop)
        alert_plan = AlertPlan(
            priority=priority,
            channels=["whatsapp"],
            reason="Satellite farm health update is WhatsApp-only because it may include Earth Engine visual context.",
            call_required=False,
        )
        message = self._satellite_message(farmer, crop, signal)
        alert_key = self._alert_key(run_key, farmer.id, self._risk_from_satellite(signal.water_stress), priority)
        if payload.dedupe and store.get_alert_run_record(alert_key):
            return ProactiveAlertFarmerResult(
                farmer_id=farmer.id,
                generated=False,
                skipped_reason="duplicate_alert",
                risk_level=self._risk_from_satellite(signal.water_stress),
                priority=priority,
                advisory=message,
            )
        delivery = AlertDeliveryService().deliver(
            farmer,
            AlertDeliveryRequest(
                farmer_id=farmer.id,
                message=message,
                alert_plan=alert_plan,
                language=farmer.language,
                requires_whatsapp_template=True,
            ),
        )
        self._log_alert(farmer.id, farmer.language, message, alert_plan, intent="satellite_farm_health_alert")
        store.save_alert_run_record(
            AlertRunRecord(
                key=alert_key,
                farmer_id=farmer.id,
                crop=crop,
                run_date=run_date,
                risk_level=self._risk_from_satellite(signal.water_stress),
                priority=priority,
                message=message,
                delivery_status=delivery.overall_status,
            )
        )
        return ProactiveAlertFarmerResult(
            farmer_id=farmer.id,
            generated=True,
            risk_level=self._risk_from_satellite(signal.water_stress),
            priority=priority,
            advisory=message,
            delivery=delivery,
        )

    def _weather_message(self, farmer: FarmerResponse, crop: str, advisory: str, fertilizer_note: str) -> str:
        location = ", ".join(part for part in [farmer.village, farmer.taluka, farmer.district] if part and part != "unknown")
        prefix = f"Good morning {farmer.name}. Weather alert"
        if location:
            prefix += f" for {location}"
        prefix += f" and {crop} advisory: "
        if fertilizer_note and fertilizer_note not in advisory:
            return f"{prefix}{advisory} {fertilizer_note}"
        return f"{prefix}{advisory}"

    def _satellite_message(self, farmer: FarmerResponse, crop: str, signal) -> str:
        location = ", ".join(part for part in [farmer.village, farmer.district] if part and part != "unknown")
        action = "Keep normal monitoring."
        if signal.water_stress == "high":
            action = "Check soil moisture today and irrigate if the root zone is dry."
        elif signal.water_stress == "medium":
            action = "Inspect the field within 24 hours and avoid moisture stress."
        if signal.chlorophyll_status == "low":
            action += " Leaf color/chlorophyll signal is low, so ask an expert before nitrogen correction."
        return (
            f"Satellite update for {crop}"
            f"{f' at {location}' if location else ''}: NDVI {signal.ndvi}, NDWI {signal.ndwi}, NDMI {signal.ndmi}. "
            f"Water stress is {signal.water_stress}, vegetation is {signal.vegetation_status}, chlorophyll is {signal.chlorophyll_status}. "
            f"{action} Source: {signal.source}."
        )

    def _crop_for_alert(self, farmer: FarmerResponse, requested_crop: str) -> str:
        if requested_crop and requested_crop != "crop":
            return requested_crop
        return farmer.active_crop or "crop"

    def _risk_from_satellite(self, water_stress: str) -> RiskLevel:
        if water_stress == "high":
            return RiskLevel.high
        if water_stress == "medium":
            return RiskLevel.medium
        return RiskLevel.low

    def _is_frequency_due(self, run_date: str, frequency_days: int) -> bool:
        if frequency_days <= 1:
            return True
        try:
            parsed = date.fromisoformat(run_date)
        except ValueError:
            return True
        return parsed.toordinal() % frequency_days == 0

    def _alert_key(
        self,
        run_key: str,
        farmer_id: str,
        risk_level,
        priority: AlertPriority,
    ) -> str:
        safe_run_key = run_key.replace("/", "_")
        return f"{safe_run_key}:{farmer_id}:{risk_level.value}:{priority.value}"

    def _log_alert(
        self,
        farmer_id: str,
        language: str,
        message: str,
        alert_plan: AlertPlan,
        *,
        intent: str = "daily_weather_crop_alert",
    ) -> None:
        ConversationStore().log(
            ConversationLogRequest(
                farmer_id=farmer_id,
                role=ConversationRole.assistant,
                text=message,
                language=language,
                channel="proactive_alert",
                intent=intent,
                metadata={
                    "priority": alert_plan.priority.value,
                    "channels": ",".join(alert_plan.channels),
                    "reason": alert_plan.reason,
                },
            )
        )
