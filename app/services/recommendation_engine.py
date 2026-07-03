from app.models.domain import CROP_PROFILES, WATER_RANK, CropProfile
from app.models.schemas import (
    CropRecommendationRequest,
    CropRecommendationResponse,
    CropScore,
    FarmerResponse,
)


class RecommendationEngine:
    def recommend(
        self,
        farmer: FarmerResponse,
        payload: CropRecommendationRequest,
        ndvi: float | None,
    ) -> CropRecommendationResponse:
        scores = [self._score_crop(crop, farmer, payload, ndvi) for crop in CROP_PROFILES]
        top_scores = sorted(scores, key=lambda item: item.score, reverse=True)[:3]

        return CropRecommendationResponse(
            farmer_id=farmer.id,
            language=farmer.language,
            recommendations=top_scores,
            data_sources={
                "soil": "farmer_profile",
                "rainfall": payload.expected_rainfall_mm,
                "groundwaterDepthM": farmer.farm.groundwater_depth_m,
                "ndvi": ndvi,
                "satellite": "earth_engine_or_request_context" if ndvi is not None else None,
            },
        )

    def _score_crop(
        self,
        crop: CropProfile,
        farmer: FarmerResponse,
        payload: CropRecommendationRequest,
        ndvi: float | None,
    ) -> CropScore:
        score = 30
        reasons: list[str] = []

        if payload.season.lower() in crop.seasons:
            score += 15
            reasons.append(f"Fits {payload.season} season.")
        else:
            score -= 15
            reasons.append(f"Not ideal for {payload.season} season.")

        soil_type = farmer.farm.soil_type.lower()
        if soil_type in crop.soil_types or soil_type == "unknown":
            score += 15
            soil_fit = "good"
            reasons.append("Soil type is suitable.")
        else:
            score -= 10
            soil_fit = "weak"
            reasons.append("Soil type is less suitable.")

        if farmer.farm.soil_ph is not None:
            if crop.ph_min <= farmer.farm.soil_ph <= crop.ph_max:
                score += 10
                reasons.append("Soil pH is in safe range.")
            else:
                score -= 8
                reasons.append("Soil pH needs correction before this crop.")

        if crop.rainfall_min_mm <= payload.expected_rainfall_mm <= crop.rainfall_max_mm:
            score += 15
            reasons.append("Expected rainfall matches crop need.")
        elif payload.expected_rainfall_mm < crop.rainfall_min_mm:
            score -= 12
            reasons.append("Rainfall may be insufficient.")
        else:
            score -= 5
            reasons.append("Excess rainfall risk should be managed.")

        available_rank = WATER_RANK[payload.water_availability.value]
        need_rank = WATER_RANK[crop.water_need]
        if available_rank >= need_rank:
            score += 10
            water_fit = "safe"
        else:
            score -= 18
            water_fit = "risky"
            reasons.append("Water availability is below crop requirement.")

        if farmer.farm.groundwater_depth_m is not None and farmer.farm.groundwater_depth_m > 30:
            if crop.water_need == "high":
                score -= 15
                reasons.append("Deep groundwater makes high-water crop risky.")
            elif crop.water_need == "low":
                score += 6
                reasons.append("Low-water crop is safer with deep groundwater.")

        if ndvi is not None:
            if ndvi < 0.25:
                score -= 5
                reasons.append("Low NDVI indicates the field needs basic preparation.")
            elif ndvi > 0.55:
                score += 4
                reasons.append("Good vegetation signal near field area.")

        final_score = max(0, min(100, score))
        return CropScore(
            crop=crop.name,
            score=final_score,
            water_fit=water_fit,
            soil_fit=soil_fit,
            reasons=reasons[:4],
            next_action=f"{crop.notes} Verify soil, water availability, and local agronomy advice before sowing.",
        )
