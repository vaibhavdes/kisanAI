from app.models.schemas import (
    DrySpellAdvisoryRequest,
    DrySpellAdvisoryResponse,
    FarmerResponse,
    RiskLevel,
    WeatherContextRequest,
)
from app.services.alert_priority_policy import AlertPriorityPolicy
from app.services.weather_context_service import WeatherContextService
from app.utils.language import phrase


class WeatherService:
    def build_dry_spell_advisory(
        self,
        farmer: FarmerResponse,
        payload: DrySpellAdvisoryRequest,
    ) -> DrySpellAdvisoryResponse:
        rainfall_forecast = payload.rainfall_forecast_mm
        temperature_c = payload.temperature_c
        weather_source = None
        weather_fallback_used = False
        if not rainfall_forecast:
            if farmer.farm.latitude is None or farmer.farm.longitude is None:
                raise ValueError("Farm location is required when rainfall forecast is not provided")
            weather = WeatherContextService().get_context(
                WeatherContextRequest(latitude=farmer.farm.latitude, longitude=farmer.farm.longitude)
            )
            rainfall_forecast = [day.rainfall_mm or 0 for day in weather.daily[:7]]
            temperature_c = weather.current_temperature_c
            weather_source = weather.source.value
            weather_fallback_used = weather.fallback_used

        dry_days = sum(1 for rain in rainfall_forecast[:7] if rain < 2)
        moisture = payload.soil_moisture
        temp = temperature_c

        if dry_days >= 6 or (moisture is not None and moisture < 0.14):
            risk = RiskLevel.critical
            irrigation_mm = 25
        elif dry_days >= 4 or (moisture is not None and moisture < 0.20):
            risk = RiskLevel.high
            irrigation_mm = 18
        elif dry_days >= 2 or (temp is not None and temp >= 35):
            risk = RiskLevel.medium
            irrigation_mm = 10
        else:
            risk = RiskLevel.low
            irrigation_mm = 0

        if irrigation_mm:
            advisory = phrase(
                "dry_spell_irrigate",
                farmer.language,
                risk=risk.value,
                mm=irrigation_mm,
                crop=payload.crop,
            )
        else:
            advisory = phrase("dry_spell_wait", farmer.language)

        fertilizer_note = (
            "Avoid heavy fertilizer during moisture stress; apply after light irrigation."
            if risk in {RiskLevel.high, RiskLevel.critical}
            else "Fertilizer application can continue if soil is moist."
        )

        alert_plan = AlertPriorityPolicy().build_plan(
            risk,
            reason=f"Dry-spell risk is {risk.value} with {dry_days} dry forecast days.",
        )

        return DrySpellAdvisoryResponse(
            farmer_id=farmer.id,
            crop=payload.crop,
            risk_level=risk,
            dry_days=dry_days,
            irrigation_mm=irrigation_mm,
            advisory=advisory,
            fertilizer_note=fertilizer_note,
            alert_channels=alert_plan.channels,
            weather_source=weather_source,
            weather_fallback_used=weather_fallback_used,
        )
