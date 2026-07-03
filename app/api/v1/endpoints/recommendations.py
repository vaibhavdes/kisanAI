from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from app.models.schemas import CropRecommendationRequest, CropRecommendationResponse, GovernmentDataContextRequest
from app.repositories.store import store
from app.services.bigquery_public_data_service import BigQueryPublicDataService
from app.services.earth_engine_service import EarthEngineService
from app.services.recommendation_engine import RecommendationEngine

router = APIRouter()


@router.post("/crop", response_model=CropRecommendationResponse)
def recommend_crop(payload: CropRecommendationRequest) -> CropRecommendationResponse:
    farmer = store.get_farmer(payload.farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    ndvi = payload.ndvi
    satellite_source = "request" if payload.ndvi is not None else None
    satellite_note = None
    if ndvi is None and farmer.farm.latitude is not None and farmer.farm.longitude is not None:
        try:
            snapshot = EarthEngineService().get_ndvi(farmer.farm.latitude, farmer.farm.longitude)
            ndvi = snapshot.ndvi
            satellite_source = snapshot.source
            satellite_note = snapshot.note
        except Exception as exc:
            satellite_note = f"Earth Engine NDVI unavailable: {exc}"

    public_context = None
    public_context_error = None
    if _needs_public_context(payload, farmer):
        try:
            public_context = BigQueryPublicDataService().build_context(
                GovernmentDataContextRequest(
                    state=farmer.state,
                    district=farmer.district,
                    season=payload.season,
                    month=payload.month or datetime.now(UTC).month,
                )
            )
        except Exception as exc:
            public_context_error = str(exc)

    try:
        return RecommendationEngine().recommend(
            farmer=farmer,
            payload=payload,
            ndvi=ndvi,
            public_context=public_context,
            satellite_source=satellite_source,
            satellite_note=satellite_note,
            public_context_error=public_context_error,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _needs_public_context(payload: CropRecommendationRequest, farmer) -> bool:
    return (
        payload.expected_rainfall_mm is None
        or farmer.farm.groundwater_depth_m is None
        or farmer.farm.soil_ph is None
        or farmer.farm.soil_type == "unknown"
    )
