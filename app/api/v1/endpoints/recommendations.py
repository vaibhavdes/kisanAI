from fastapi import APIRouter, HTTPException

from app.models.schemas import CropRecommendationRequest, CropRecommendationResponse
from app.repositories.store import store
from app.services.earth_engine_service import EarthEngineService
from app.services.recommendation_engine import RecommendationEngine

router = APIRouter()


@router.post("/crop", response_model=CropRecommendationResponse)
def recommend_crop(payload: CropRecommendationRequest) -> CropRecommendationResponse:
    farmer = store.get_farmer(payload.farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    ndvi = payload.ndvi
    if ndvi is None and farmer.farm.latitude is not None and farmer.farm.longitude is not None:
        ndvi = EarthEngineService().get_ndvi(farmer.farm.latitude, farmer.farm.longitude).ndvi

    return RecommendationEngine().recommend(farmer=farmer, payload=payload, ndvi=ndvi)
