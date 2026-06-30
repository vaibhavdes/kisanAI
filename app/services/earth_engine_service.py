from pydantic import BaseModel


class NdviSnapshot(BaseModel):
    ndvi: float
    source: str
    note: str


class EarthEngineService:
    def get_demo_ndvi(self, latitude: float, longitude: float) -> NdviSnapshot:
        # Deterministic demo value; replace with Earth Engine polygon/time-series query.
        normalized = (abs(latitude * 31.0 + longitude * 17.0) % 35) / 100
        ndvi = round(0.25 + normalized, 2)
        return NdviSnapshot(
            ndvi=ndvi,
            source="demo",
            note="Replace with Google Earth Engine Sentinel/Landsat NDVI.",
        )

