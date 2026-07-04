from app.models.schemas import RiskLevel


class SensorService:
    def classify_soil_moisture(self, moisture: float | None) -> RiskLevel:
        if moisture is None:
            return RiskLevel.medium
        if moisture < 0.14:
            return RiskLevel.critical
        if moisture < 0.20:
            return RiskLevel.high
        if moisture < 0.28:
            return RiskLevel.medium
        return RiskLevel.low

