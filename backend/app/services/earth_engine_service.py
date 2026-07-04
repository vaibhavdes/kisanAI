from datetime import date, timedelta

from pydantic import BaseModel

from app.core.config import settings
from app.models.schemas import FarmCoordinate, SatelliteHistoryPoint, SatelliteSignalResponse


class NdviSnapshot(BaseModel):
    ndvi: float
    source: str
    note: str


class EarthEngineService:
    def get_ndvi(self, latitude: float, longitude: float) -> NdviSnapshot:
        signal = self.get_farm_signal(latitude=latitude, longitude=longitude, history_periods=1)
        if signal.ndvi is None:
            raise RuntimeError("Earth Engine did not return NDVI for this location and date range")
        return NdviSnapshot(
            ndvi=signal.ndvi,
            source=signal.source,
            note=signal.note,
        )

    def get_farm_signal(
        self,
        latitude: float,
        longitude: float,
        polygon: list[FarmCoordinate] | None = None,
        buffer_m: int = 250,
        days: int = 90,
        history_periods: int = 3,
        farmer_id: str | None = None,
    ) -> SatelliteSignalResponse:
        import ee

        ee.Initialize(project=settings.google_cloud_project)
        end = date.today()
        start = end - timedelta(days=days)
        geometry, geometry_type = self._geometry(ee, latitude, longitude, polygon, buffer_m)
        collection = self._collection(ee, geometry, start.isoformat(), end.isoformat())
        summary = self._mean_indices(ee, collection.median(), geometry)
        ndvi = self._rounded(summary.get("NDVI"))
        ndwi = self._rounded(summary.get("NDWI"))
        ndmi = self._rounded(summary.get("NDMI"))
        evi = self._rounded(summary.get("EVI"))
        ndre = self._rounded(summary.get("NDRE"))

        return SatelliteSignalResponse(
            farmer_id=farmer_id,
            latitude=latitude,
            longitude=longitude,
            geometry_type=geometry_type,
            buffer_m=buffer_m if geometry_type == "point_buffer" else None,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            source="earth_engine_sentinel_2",
            ndvi=ndvi,
            ndwi=ndwi,
            ndmi=ndmi,
            evi=evi,
            ndre=ndre,
            water_stress=self._water_stress(ndvi, ndwi, ndmi),
            vegetation_status=self._vegetation_status(ndvi),
            moisture_status=self._moisture_status(ndmi),
            chlorophyll_status=self._chlorophyll_status(ndre),
            history=self._history(ee, geometry, start, end, history_periods),
            note=(
                f"Sentinel-2 median NDVI/NDWI/NDMI/EVI/NDRE for {geometry_type} "
                f"from {start.isoformat()} to {end.isoformat()}."
            ),
        )

    def _geometry(
        self,
        ee,
        latitude: float,
        longitude: float,
        polygon: list[FarmCoordinate] | None,
        buffer_m: int,
    ):
        if polygon and len(polygon) >= 3:
            coordinates = [[point.longitude, point.latitude] for point in polygon]
            if coordinates[0] != coordinates[-1]:
                coordinates.append(coordinates[0])
            return ee.Geometry.Polygon([coordinates]), "polygon"
        return ee.Geometry.Point([longitude, latitude]).buffer(buffer_m), "point_buffer"

    def _collection(self, ee, geometry, start: str, end: str):
        return (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(geometry)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 35))
            .map(self._add_indices)
            .select(["NDVI", "NDWI", "NDMI", "EVI", "NDRE"])
        )

    def _add_indices(self, image):
        ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
        ndwi = image.normalizedDifference(["B3", "B8"]).rename("NDWI")
        ndmi = image.normalizedDifference(["B8", "B11"]).rename("NDMI")
        ndre = image.normalizedDifference(["B8", "B5"]).rename("NDRE")
        evi = image.expression(
            "2.5 * ((nir - red) / (nir + 6 * red - 7.5 * blue + 1))",
            {
                "nir": image.select("B8").divide(10000),
                "red": image.select("B4").divide(10000),
                "blue": image.select("B2").divide(10000),
            },
        ).rename("EVI")
        return image.addBands([ndvi, ndwi, ndmi, evi, ndre])

    def _mean_indices(self, ee, image, geometry) -> dict:
        values = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=10,
            maxPixels=1_000_000,
        ).getInfo()
        return values or {}

    def _history(
        self,
        ee,
        geometry,
        start: date,
        end: date,
        periods: int,
    ) -> list[SatelliteHistoryPoint]:
        total_days = max(1, (end - start).days)
        period_days = max(1, total_days // periods)
        points: list[SatelliteHistoryPoint] = []
        cursor = start

        while cursor < end and len(points) < periods:
            period_end = min(end, cursor + timedelta(days=period_days))
            collection = self._collection(ee, geometry, cursor.isoformat(), period_end.isoformat())
            values = self._mean_indices(ee, collection.median(), geometry)
            ndvi = self._rounded(values.get("NDVI"))
            ndwi = self._rounded(values.get("NDWI"))
            ndmi = self._rounded(values.get("NDMI"))
            evi = self._rounded(values.get("EVI"))
            ndre = self._rounded(values.get("NDRE"))
            points.append(
                SatelliteHistoryPoint(
                    start_date=cursor.isoformat(),
                    end_date=period_end.isoformat(),
                    ndvi=ndvi,
                    ndwi=ndwi,
                    ndmi=ndmi,
                    evi=evi,
                    ndre=ndre,
                    water_stress=self._water_stress(ndvi, ndwi, ndmi),
                )
            )
            cursor = period_end

        return points

    def _rounded(self, value) -> float | None:
        if value is None:
            return None
        return round(float(value), 3)

    def _water_stress(self, ndvi: float | None, ndwi: float | None, ndmi: float | None = None) -> str:
        if ndvi is None and ndwi is None and ndmi is None:
            return "unknown"
        if ndmi is not None and ndmi < -0.1:
            return "high"
        if ndwi is not None and ndwi < -0.15:
            return "high"
        if ndmi is not None and ndmi < 0.1:
            return "medium"
        if ndwi is not None and ndwi < 0:
            return "medium"
        if ndvi is not None and ndvi < 0.25:
            return "medium"
        return "low"

    def _vegetation_status(self, ndvi: float | None) -> str:
        if ndvi is None:
            return "unknown"
        if ndvi < 0.25:
            return "poor"
        if ndvi < 0.45:
            return "moderate"
        return "healthy"

    def _moisture_status(self, ndmi: float | None) -> str:
        if ndmi is None:
            return "unknown"
        if ndmi < -0.1:
            return "very_dry"
        if ndmi < 0.1:
            return "dry"
        if ndmi < 0.3:
            return "adequate"
        return "moist"

    def _chlorophyll_status(self, ndre: float | None) -> str:
        if ndre is None:
            return "unknown"
        if ndre < 0.18:
            return "low"
        if ndre < 0.32:
            return "medium"
        return "good"
