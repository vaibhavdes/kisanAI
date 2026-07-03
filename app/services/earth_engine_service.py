from datetime import date, timedelta

from app.core.config import settings
from pydantic import BaseModel


class NdviSnapshot(BaseModel):
    ndvi: float
    source: str
    note: str


class EarthEngineService:
    def get_ndvi(self, latitude: float, longitude: float) -> NdviSnapshot:
        import ee

        ee.Initialize(project=settings.google_cloud_project)
        point = ee.Geometry.Point([longitude, latitude])
        start = (date.today() - timedelta(days=90)).isoformat()
        end = date.today().isoformat()

        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(point)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 35))
            .map(self._add_ndvi)
            .select("NDVI")
        )
        value = collection.median().reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point.buffer(250),
            scale=10,
            maxPixels=1_000_000,
        ).get("NDVI")
        ndvi = value.getInfo()
        if ndvi is None:
            raise RuntimeError("Earth Engine did not return NDVI for this location and date range")

        return NdviSnapshot(
            ndvi=round(float(ndvi), 3),
            source="earth_engine_sentinel_2",
            note=f"Sentinel-2 median NDVI for 250m buffer from {start} to {end}.",
        )

    def _add_ndvi(self, image):
        return image.addBands(image.normalizedDifference(["B8", "B4"]).rename("NDVI"))
