from app.models.schemas import (
    DatasetReference,
    GovernmentDataContextRequest,
    GovernmentDataContextResponse,
)


class GovernmentDataService:
    def list_sources(self) -> list[DatasetReference]:
        return [
            DatasetReference(
                name="data.gov.in Agriculture datasets",
                provider="Open Government Data Platform India",
                url="https://www.data.gov.in/sector/agriculture",
                use_case="Crop production, irrigation, agriculture statistics and state datasets.",
            ),
            DatasetReference(
                name="data.gov.in APIs",
                provider="Open Government Data Platform India",
                url="https://www.data.gov.in/apis",
                use_case="API access to public datasets using API key and resource IDs.",
            ),
            DatasetReference(
                name="IMD API Management Platform",
                provider="India Meteorological Department",
                url="https://api.imd.gov.in/",
                use_case="Forecasts, warnings, rainfall observations and bulletins.",
            ),
            DatasetReference(
                name="IMD Agromet Advisory Services",
                provider="India Meteorological Department",
                url="https://mausam.imd.gov.in/responsive/agromet_adv_ser_state_current.php",
                use_case="District/state agromet advisory context for crop-stage guidance.",
            ),
            DatasetReference(
                name="IMD Data Service Portal",
                provider="India Meteorological Department",
                url="https://dsp.imdpune.gov.in/",
                use_case="Historical rainfall and weather data for crop suitability.",
            ),
            DatasetReference(
                name="Soil Health Card Portal",
                provider="Department of Agriculture and Farmers Welfare",
                url="https://soilhealth.dac.gov.in/",
                use_case="Soil-card image upload and future soil-test data integration.",
            ),
            DatasetReference(
                name="India-WRIS",
                provider="Water Resources Information System",
                url="https://indiawris.gov.in/wris/",
                use_case="Water resources and groundwater context for crop water-risk scoring.",
            ),
            DatasetReference(
                name="Agmarknet",
                provider="Directorate of Marketing and Inspection",
                url="https://agmarknet.gov.in/",
                use_case="Mandi price and arrival data for optional profitability layer.",
            ),
        ]

    def build_context(self, payload: GovernmentDataContextRequest) -> GovernmentDataContextResponse:
        crop_text = f" for {payload.crop}" if payload.crop else ""
        season_text = f" during {payload.season}" if payload.season else ""
        return GovernmentDataContextResponse(
            state=payload.state,
            district=payload.district,
            crop=payload.crop,
            rainfall_signal=(
                f"Use IMD historical rainfall normals and 5-day forecast for {payload.district}{season_text}."
            ),
            groundwater_signal=(
                f"Use India-WRIS/groundwater datasets to classify water stress in {payload.district}."
            ),
            crop_history_signal=(
                f"Use APY/crop production datasets to compare historical yield{crop_text} in this region."
            ),
            recommended_datasets=self.list_sources(),
        )

