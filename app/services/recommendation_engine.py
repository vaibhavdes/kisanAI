from app.models.domain import CROP_PROFILES, WATER_RANK, CropProfile
from app.models.schemas import (
    CropRecommendationRequest,
    CropRecommendationResponse,
    CropScore,
    FarmerResponse,
    GovernmentDataContextResponse,
)


class RecommendationEngine:
    def recommend(
        self,
        farmer: FarmerResponse,
        payload: CropRecommendationRequest,
        ndvi: float | None,
        public_context: GovernmentDataContextResponse | None = None,
        satellite_source: str | None = None,
        satellite_note: str | None = None,
        public_context_error: str | None = None,
    ) -> CropRecommendationResponse:
        rainfall_mm = self._rainfall_mm(payload, public_context)
        if rainfall_mm is None:
            raise ValueError("expected_rainfall_mm is required when district rainfall normal is unavailable.")

        soil_ph = self._soil_ph(farmer, public_context)
        groundwater_depth_m = self._groundwater_depth_m(farmer, public_context)

        scores = [
            self._score_crop(
                crop=crop,
                farmer=farmer,
                payload=payload,
                ndvi=ndvi,
                rainfall_mm=rainfall_mm,
                soil_ph=soil_ph,
                groundwater_depth_m=groundwater_depth_m,
            )
            for crop in CROP_PROFILES
        ]
        top_scores = sorted(scores, key=lambda item: item.score, reverse=True)[:3]

        return CropRecommendationResponse(
            farmer_id=farmer.id,
            language=farmer.language,
            recommendations=top_scores,
            data_sources={
                "soil": self._soil_source(farmer, public_context),
                "soilPh": soil_ph,
                "rainfall": rainfall_mm,
                "rainfallSource": "request" if payload.expected_rainfall_mm is not None else self._signal_source(public_context, "rainfall_normal"),
                "groundwaterDepthM": groundwater_depth_m,
                "groundwaterSource": "farmer_profile"
                if farmer.farm.groundwater_depth_m is not None
                else self._signal_source(public_context, "groundwater"),
                "ndvi": ndvi,
                "satellite": satellite_source or ("request" if payload.ndvi is not None else None),
                "satelliteNote": satellite_note,
                "publicContextMissing": ",".join(public_context.missing_sources) if public_context else None,
                "publicContextError": public_context_error,
            },
        )

    def _score_crop(
        self,
        crop: CropProfile,
        farmer: FarmerResponse,
        payload: CropRecommendationRequest,
        ndvi: float | None,
        rainfall_mm: float,
        soil_ph: float | None,
        groundwater_depth_m: float | None,
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

        if soil_ph is not None:
            if crop.ph_min <= soil_ph <= crop.ph_max:
                score += 10
                reasons.append("Soil pH is in safe range.")
            else:
                score -= 8
                reasons.append("Soil pH needs correction before this crop.")

        if crop.rainfall_min_mm <= rainfall_mm <= crop.rainfall_max_mm:
            score += 15
            reasons.append("Expected rainfall matches crop need.")
        elif rainfall_mm < crop.rainfall_min_mm:
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

        if groundwater_depth_m is not None and groundwater_depth_m > 30:
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

    def _rainfall_mm(
        self,
        payload: CropRecommendationRequest,
        public_context: GovernmentDataContextResponse | None,
    ) -> float | None:
        if payload.expected_rainfall_mm is not None:
            return payload.expected_rainfall_mm
        if public_context and public_context.rainfall_normal.available:
            return self._float(public_context.rainfall_normal.value)
        return None

    def _soil_ph(
        self,
        farmer: FarmerResponse,
        public_context: GovernmentDataContextResponse | None,
    ) -> float | None:
        if farmer.farm.soil_ph is not None:
            return farmer.farm.soil_ph
        if public_context and public_context.soil_health.available:
            return self._float(public_context.soil_health.metadata.get("ph"))
        return None

    def _groundwater_depth_m(
        self,
        farmer: FarmerResponse,
        public_context: GovernmentDataContextResponse | None,
    ) -> float | None:
        if farmer.farm.groundwater_depth_m is not None:
            return farmer.farm.groundwater_depth_m
        if public_context and public_context.groundwater.available:
            return self._float(public_context.groundwater.value)
        return None

    def _soil_source(
        self,
        farmer: FarmerResponse,
        public_context: GovernmentDataContextResponse | None,
    ) -> str | None:
        if farmer.farm.soil_type != "unknown" or farmer.farm.soil_ph is not None:
            return "farmer_profile"
        return self._signal_source(public_context, "soil_health")

    def _signal_source(self, public_context: GovernmentDataContextResponse | None, signal_name: str) -> str | None:
        if not public_context:
            return None
        signal = getattr(public_context, signal_name)
        return signal.source if signal.available else None

    def _float(self, value: str | float | int | None) -> float | None:
        if value is None:
            return None
        return float(value)
