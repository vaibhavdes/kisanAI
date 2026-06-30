from app.models.schemas import (
    DrySpellAdvisoryRequest,
    DrySpellAdvisoryResponse,
    FarmerResponse,
    RiskLevel,
)
from app.utils.language import phrase


class WeatherService:
    def build_dry_spell_advisory(
        self,
        farmer: FarmerResponse,
        payload: DrySpellAdvisoryRequest,
    ) -> DrySpellAdvisoryResponse:
        dry_days = sum(1 for rain in payload.rainfall_forecast_mm[:7] if rain < 2)
        moisture = payload.soil_moisture
        temp = payload.temperature_c

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

        return DrySpellAdvisoryResponse(
            farmer_id=farmer.id,
            crop=payload.crop,
            risk_level=risk,
            dry_days=dry_days,
            irrigation_mm=irrigation_mm,
            advisory=advisory,
            fertilizer_note=fertilizer_note,
            alert_channels=["voice", "sms"],
        )
