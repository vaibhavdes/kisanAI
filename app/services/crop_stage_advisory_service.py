from app.core.config import settings
from app.models.schemas import (
    AdvisoryTestRequest,
    CropStage,
    CropStageAdvisoryRequest,
    CropStageAdvisoryResponse,
    FarmerResponse,
    RiskLevel,
)
from app.services.alert_priority_policy import AlertPriorityPolicy
from app.services.gemini_service import AdvisoryProviderUnavailable, GeminiService


class CropStageAdvisoryService:
    def build_advisory(
        self,
        farmer: FarmerResponse,
        payload: CropStageAdvisoryRequest,
    ) -> CropStageAdvisoryResponse:
        dry_days = sum(1 for rain in payload.rainfall_forecast_mm[:7] if rain < 2)
        risk = self._risk_for_stage(payload, dry_days)
        actions = self._actions_for_stage(payload, dry_days, risk)
        advice = f"{payload.crop} is in {payload.stage.value} stage. " + " ".join(actions[:2])
        ai_source = None
        ai_model = None
        if settings.enable_google_integrations:
            try:
                ai_response = GeminiService().generate_test_advisory(
                    AdvisoryTestRequest(
                        farmer_name=farmer.name,
                        language=farmer.language,
                        crop=payload.crop,
                        crop_stage=payload.stage.value,
                        location=f"{farmer.village}, {farmer.district}, {farmer.state}",
                        weather_summary=(
                            f"{dry_days} dry days forecast. Wind {payload.wind_speed_kmph} kmph. "
                            f"Humidity {payload.humidity_percent}%. Risk {risk.value}."
                        ),
                        rainfall_forecast_mm=sum(payload.rainfall_forecast_mm[:7]),
                        soil_moisture=payload.soil_moisture,
                    )
                )
                advice = ai_response.advisory_text
                if ai_response.recommended_actions:
                    actions = ai_response.recommended_actions
                ai_source = ai_response.source
                ai_model = ai_response.model
            except AdvisoryProviderUnavailable:
                pass
        alert_plan = AlertPriorityPolicy().build_plan(
            risk,
            reason=f"{payload.stage.value} stage advisory risk is {risk.value}.",
        )

        return CropStageAdvisoryResponse(
            farmer_id=farmer.id,
            crop=payload.crop,
            stage=payload.stage,
            risk_level=risk,
            advice=advice,
            actions=actions,
            alert_plan=alert_plan,
            data_used={
                "dryDays": dry_days,
                "windSpeedKmph": payload.wind_speed_kmph,
                "humidityPercent": payload.humidity_percent,
                "soilMoisture": payload.soil_moisture,
                "diseaseRisk": payload.disease_risk.value if payload.disease_risk else None,
            },
            ai_source=ai_source,
            ai_model=ai_model,
        )

    def _risk_for_stage(self, payload: CropStageAdvisoryRequest, dry_days: int) -> RiskLevel:
        if payload.disease_risk in {RiskLevel.high, RiskLevel.critical}:
            return payload.disease_risk
        if payload.stage == CropStage.flowering and dry_days >= 4:
            return RiskLevel.high
        if payload.stage == CropStage.germination and payload.soil_moisture is not None:
            if payload.soil_moisture < 0.18:
                return RiskLevel.high
        if payload.wind_speed_kmph is not None and payload.wind_speed_kmph > 28:
            return RiskLevel.medium
        if payload.humidity_percent is not None and payload.humidity_percent > 85:
            return RiskLevel.medium
        if dry_days >= 3:
            return RiskLevel.medium
        return RiskLevel.low

    def _actions_for_stage(
        self,
        payload: CropStageAdvisoryRequest,
        dry_days: int,
        risk: RiskLevel,
    ) -> list[str]:
        actions_by_stage = {
            CropStage.sowing: [
                "Confirm rainfall window before sowing.",
                "Treat seed and avoid sowing immediately before heavy rain.",
            ],
            CropStage.germination: [
                "Keep top soil moist; avoid waterlogging.",
                "Check patchy germination and re-sow gaps early.",
            ],
            CropStage.vegetative: [
                "Schedule nutrient application only when soil has enough moisture.",
                "Scout leaves for pest and nutrient stress.",
            ],
            CropStage.flowering: [
                "Avoid moisture stress because flowering stage is sensitive.",
                "Avoid spraying during high wind or expected rain.",
            ],
            CropStage.harvesting: [
                "Harvest before expected rainfall if crop is mature.",
                "Keep produce dry and plan transport/storage.",
            ],
            CropStage.post_harvest: [
                "Record yield and losses for next season planning.",
                "Use residue and soil test results to plan the next crop.",
            ],
        }
        actions = list(actions_by_stage[payload.stage])
        if dry_days >= 4:
            actions.append("Dry-spell risk is high; prioritize irrigation check.")
        if payload.humidity_percent is not None and payload.humidity_percent > 85:
            actions.append("High humidity increases disease risk; scout crop closely.")
        if risk in {RiskLevel.high, RiskLevel.critical}:
            actions.append("Escalate to expert if symptoms are visible.")
        return actions
