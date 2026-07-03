from typing import Any

from app.core.config import settings
from app.models.schemas import DataSignal, GovernmentDataContextRequest, GovernmentDataContextResponse
from app.services.government_data_service import GovernmentDataService


class BigQueryPublicDataService:
    def __init__(self, client: Any | None = None) -> None:
        if client is None:
            from google.cloud import bigquery

            client = bigquery.Client(project=settings.google_cloud_project)
        self.client = client

    def build_context(self, payload: GovernmentDataContextRequest) -> GovernmentDataContextResponse:
        rainfall = self._rainfall_normal(payload)
        groundwater = self._groundwater(payload)
        soil = self._soil_health(payload)
        crop_history = self._crop_history(payload)
        agromet = self._agromet(payload)
        signals = {
            "rainfall_normal": rainfall,
            "groundwater": groundwater,
            "soil_health": soil,
            "crop_history": crop_history,
            "agromet_advisory": agromet,
        }
        return GovernmentDataContextResponse(
            state=payload.state,
            district=payload.district,
            crop=payload.crop,
            rainfall_normal=rainfall,
            groundwater=groundwater,
            soil_health=soil,
            crop_history=crop_history,
            agromet_advisory=agromet,
            recommended_datasets=GovernmentDataService().list_sources(),
            missing_sources=[name for name, signal in signals.items() if not signal.available],
        )

    def _rainfall_normal(self, payload: GovernmentDataContextRequest) -> DataSignal:
        if payload.month is None:
            return self._missing("district_rainfall_normals", "Month is required for rainfall normal lookup.")
        rows = self._query(
            """
            SELECT normal_rainfall_mm, source_name
            FROM `{project}.{dataset}.district_rainfall_normals`
            WHERE LOWER(state) = LOWER(@state)
              AND LOWER(district) = LOWER(@district)
              AND month = @month
            ORDER BY ingested_at DESC
            LIMIT 1
            """,
            payload,
            extra={"month": payload.month},
        )
        if not rows:
            return self._missing("district_rainfall_normals", "No rainfall normal found for district/month.")
        row = rows[0]
        return DataSignal(
            available=True,
            source=str(row.get("source_name") or "district_rainfall_normals"),
            value=self._float(row.get("normal_rainfall_mm")),
            unit="mm",
            note="Historical district monthly rainfall normal.",
            metadata={"month": payload.month},
        )

    def _groundwater(self, payload: GovernmentDataContextRequest) -> DataSignal:
        rows = self._query(
            """
            SELECT groundwater_depth_m, category, source_name, observation_date
            FROM `{project}.{dataset}.district_groundwater_level`
            WHERE LOWER(state) = LOWER(@state)
              AND LOWER(district) = LOWER(@district)
            ORDER BY observation_date DESC NULLS LAST, ingested_at DESC
            LIMIT 1
            """,
            payload,
        )
        if not rows:
            return self._missing("district_groundwater_level", "No groundwater level found for district.")
        row = rows[0]
        category = row.get("category")
        return DataSignal(
            available=True,
            source=str(row.get("source_name") or "district_groundwater_level"),
            value=self._float(row.get("groundwater_depth_m")),
            unit="m",
            note=f"Latest groundwater depth. Category: {category}" if category else "Latest groundwater depth.",
            metadata={
                "groundwater_depth_m": self._float(row.get("groundwater_depth_m")),
                "category": str(category) if category else None,
            },
        )

    def _soil_health(self, payload: GovernmentDataContextRequest) -> DataSignal:
        rows = self._query(
            """
            SELECT ph, organic_carbon, nitrogen, phosphorus, potassium, source_name
            FROM `{project}.{dataset}.soil_health_summary`
            WHERE LOWER(state) = LOWER(@state)
              AND LOWER(district) = LOWER(@district)
            ORDER BY ingested_at DESC
            LIMIT 1
            """,
            payload,
        )
        if not rows:
            return self._missing("soil_health_summary", "No soil-health baseline found for district.")
        row = rows[0]
        summary = (
            f"pH {row.get('ph')}, organic carbon {row.get('organic_carbon')}, "
            f"N {row.get('nitrogen')}, P {row.get('phosphorus')}, K {row.get('potassium')}"
        )
        return DataSignal(
            available=True,
            source=str(row.get("source_name") or "soil_health_summary"),
            value=summary,
            note="District soil-health baseline.",
            metadata={
                "ph": self._float(row.get("ph")),
                "organic_carbon": self._float(row.get("organic_carbon")),
                "nitrogen": str(row.get("nitrogen")) if row.get("nitrogen") is not None else None,
                "phosphorus": str(row.get("phosphorus")) if row.get("phosphorus") is not None else None,
                "potassium": str(row.get("potassium")) if row.get("potassium") is not None else None,
            },
        )

    def _crop_history(self, payload: GovernmentDataContextRequest) -> DataSignal:
        if not payload.crop:
            return self._missing("crop_production_history", "Crop is required for crop history lookup.")
        rows = self._query(
            """
            SELECT yield_kg_per_hectare, crop_year, source_name
            FROM `{project}.{dataset}.crop_production_history`
            WHERE LOWER(state) = LOWER(@state)
              AND (district IS NULL OR LOWER(district) = LOWER(@district))
              AND LOWER(crop) = LOWER(@crop)
              AND (@season IS NULL OR season IS NULL OR LOWER(season) = LOWER(@season))
            ORDER BY crop_year DESC
            LIMIT 1
            """,
            payload,
        )
        if not rows:
            return self._missing("crop_production_history", "No crop production/yield history found.")
        row = rows[0]
        return DataSignal(
            available=True,
            source=str(row.get("source_name") or "crop_production_history"),
            value=self._float(row.get("yield_kg_per_hectare")),
            unit="kg/ha",
            note=f"Latest available yield history year: {row.get('crop_year')}.",
            metadata={"crop_year": self._int(row.get("crop_year"))},
        )

    def _agromet(self, payload: GovernmentDataContextRequest) -> DataSignal:
        rows = self._query(
            """
            SELECT advisory_text, source_name, bulletin_date
            FROM `{project}.{dataset}.agromet_advisory`
            WHERE LOWER(state) = LOWER(@state)
              AND (district IS NULL OR LOWER(district) = LOWER(@district))
              AND (@crop IS NULL OR crop IS NULL OR LOWER(crop) = LOWER(@crop))
            ORDER BY bulletin_date DESC
            LIMIT 1
            """,
            payload,
        )
        if not rows:
            return self._missing("agromet_advisory", "No IMD agromet advisory found for district/crop.")
        row = rows[0]
        return DataSignal(
            available=True,
            source=str(row.get("source_name") or "agromet_advisory"),
            value=str(row.get("advisory_text") or "")[:500],
            note=f"Latest agromet bulletin date: {row.get('bulletin_date')}.",
        )

    def _query(
        self,
        sql: str,
        payload: GovernmentDataContextRequest,
        *,
        extra: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        from google.cloud import bigquery

        params: list[Any] = [
            bigquery.ScalarQueryParameter("state", "STRING", payload.state),
            bigquery.ScalarQueryParameter("district", "STRING", payload.district),
            bigquery.ScalarQueryParameter("crop", "STRING", payload.crop),
            bigquery.ScalarQueryParameter("season", "STRING", payload.season),
        ]
        for key, value in (extra or {}).items():
            param_type = "INT64" if isinstance(value, int) else "STRING"
            params.append(bigquery.ScalarQueryParameter(key, param_type, value))

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        query = sql.format(project=settings.google_cloud_project, dataset=settings.bigquery_public_dataset)
        return [dict(row.items()) for row in self.client.query(query, job_config=job_config).result()]

    def _missing(self, source: str, note: str) -> DataSignal:
        return DataSignal(available=False, source=source, note=note)

    def _float(self, value: Any) -> float | None:
        return float(value) if value is not None else None

    def _int(self, value: Any) -> int | None:
        return int(value) if value is not None else None
