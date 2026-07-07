from datetime import UTC, datetime

from app.models.schemas import RiskLevel, SensorReading, SensorReadingCreate, SensorReadingResponse
from app.repositories.store import store


class SensorService:
    def save_reading(self, payload: SensorReadingCreate) -> SensorReadingResponse:
        farmer = store.get_farmer(payload.farmer_id)
        if farmer is None:
            raise ValueError("Farmer not found")

        risk = self.classify_soil_moisture(payload.readings.soil_moisture)
        reading = SensorReading(
            farmer_id=payload.farmer_id,
            sensor_id=payload.sensor_id,
            source=payload.source,
            device_type=payload.device_type,
            timestamp=payload.timestamp or datetime.now(UTC),
            latitude=payload.latitude if payload.latitude is not None else farmer.farm.latitude,
            longitude=payload.longitude if payload.longitude is not None else farmer.farm.longitude,
            readings=payload.readings,
            soil_moisture_risk=risk,
        )
        store.save_sensor_reading(reading)
        return SensorReadingResponse(
            saved=True,
            reading=reading,
            advisory_hint=self._advisory_hint(risk),
        )

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

    def latest_for_farmer(self, farmer_id: str, sensor_id: str | None = None) -> SensorReading | None:
        return store.latest_sensor_reading(farmer_id, sensor_id=sensor_id)

    def _advisory_hint(self, risk: RiskLevel) -> str:
        if risk == RiskLevel.critical:
            return "Sensor soil moisture is critically low; irrigation should be checked immediately."
        if risk == RiskLevel.high:
            return "Sensor soil moisture is low; combine this with weather and crop stage for irrigation advice."
        if risk == RiskLevel.medium:
            return "Sensor soil moisture is moderate; keep monitoring before irrigation."
        return "Sensor soil moisture is adequate; avoid unnecessary irrigation."
