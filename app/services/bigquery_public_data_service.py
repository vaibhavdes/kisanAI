from typing import Any

from app.core.config import settings
from app.models.schemas import DataSignal, GovernmentDataContextRequest, GovernmentDataContextResponse
from app.services.government_data_service import GovernmentDataService
from app.services.imd_region_mapping import maharashtra_imd_subdivision_for_district


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
        dryspell = self._dryspell(payload)
        heavy_rainfall = self._heavy_rainfall(payload)
        signals = {
            "rainfall_normal": rainfall,
            "groundwater": groundwater,
            "soil_health": soil,
            "crop_history": crop_history,
            "agromet_advisory": agromet,
        }
        if payload.state.lower() == "maharashtra":
            signals["dryspell_history"] = dryspell
            signals["heavy_rainfall_history"] = heavy_rainfall
        return GovernmentDataContextResponse(
            state=payload.state,
            district=payload.district,
            crop=payload.crop,
            rainfall_normal=rainfall,
            groundwater=groundwater,
            soil_health=soil,
            crop_history=crop_history,
            agromet_advisory=agromet,
            dryspell_history=dryspell,
            heavy_rainfall_history=heavy_rainfall,
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
            subdivision_signal = self._subdivision_rainfall_normal(payload)
            if subdivision_signal.available:
                return subdivision_signal
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

    def _subdivision_rainfall_normal(self, payload: GovernmentDataContextRequest) -> DataSignal:
        if payload.month is None or payload.state.lower() != "maharashtra":
            return self._missing("subdivision_rainfall_history", "Subdivision rainfall fallback not applicable.")
        subdivision = maharashtra_imd_subdivision_for_district(payload.district)
        if not subdivision:
            return self._missing("subdivision_rainfall_history", "No IMD subdivision mapping for district.")
        rows = self._query(
            """
            SELECT AVG(rainfall_mm) AS normal_rainfall_mm,
                   COUNT(rainfall_mm) AS sample_count,
                   MAX(year) AS latest_year,
                   ANY_VALUE(source_name) AS source_name
            FROM `{project}.{dataset}.subdivision_rainfall_history`
            WHERE LOWER(subdivision) = LOWER(@subdivision)
              AND month = @month
              AND rainfall_mm IS NOT NULL
            """,
            payload,
            extra={"month": payload.month, "subdivision": subdivision},
        )
        if not rows or rows[0].get("normal_rainfall_mm") is None:
            return self._missing("subdivision_rainfall_history", "No subdivision rainfall history found.")
        row = rows[0]
        return DataSignal(
            available=True,
            source=str(row.get("source_name") or "subdivision_rainfall_history"),
            value=self._float(row.get("normal_rainfall_mm")),
            unit="mm",
            note=f"IMD subdivision monthly rainfall normal fallback for {subdivision}.",
            metadata={
                "month": payload.month,
                "subdivision": subdivision,
                "sample_count": self._int(row.get("sample_count")),
                "latest_year": self._int(row.get("latest_year")),
            },
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

    def _dryspell(self, payload: GovernmentDataContextRequest) -> DataSignal:
        if payload.state.lower() != "maharashtra":
            return self._missing("maharashtra_dryspell_events", "Maharashtra-only dry-spell source.")
        rows = self._query(
            """
            SELECT start_date, end_date, duration_days, taluka, source_name
            FROM `{project}.{dataset}.maharashtra_dryspell_events`
            WHERE LOWER(state) = LOWER(@state)
              AND LOWER(district) = LOWER(@district)
            ORDER BY season_year DESC, start_date DESC
            LIMIT 5
            """,
            payload,
        )
        if not rows:
            return self._missing("maharashtra_dryspell_events", "No tehsil dry-spell event found for district.")
        latest = rows[0]
        return DataSignal(
            available=True,
            source=str(latest.get("source_name") or "maharashtra_dryspell_events"),
            value=len(rows),
            unit="events",
            note=(
                f"Latest dry spell: {latest.get('taluka')} "
                f"{latest.get('start_date')} to {latest.get('end_date')}."
            ),
            metadata={
                "latest_duration_days": self._int(latest.get("duration_days")),
                "latest_start_date": str(latest.get("start_date")),
                "latest_end_date": str(latest.get("end_date")),
            },
        )

    def _heavy_rainfall(self, payload: GovernmentDataContextRequest) -> DataSignal:
        if payload.state.lower() != "maharashtra":
            return self._missing("maharashtra_heavy_rainfall_events", "Maharashtra-only heavy-rain source.")
        rows = self._query(
            """
            SELECT event_date, rainfall_mm, taluka, source_name
            FROM `{project}.{dataset}.maharashtra_heavy_rainfall_events`
            WHERE LOWER(state) = LOWER(@state)
              AND LOWER(district) = LOWER(@district)
            ORDER BY season_year DESC, event_date DESC
            LIMIT 5
            """,
            payload,
        )
        if not rows:
            return self._missing("maharashtra_heavy_rainfall_events", "No tehsil heavy-rain event found for district.")
        latest = rows[0]
        return DataSignal(
            available=True,
            source=str(latest.get("source_name") or "maharashtra_heavy_rainfall_events"),
            value=self._float(latest.get("rainfall_mm")),
            unit="mm",
            note=f"Latest heavy rainfall: {latest.get('taluka')} on {latest.get('event_date')}.",
            metadata={
                "event_count": len(rows),
                "latest_event_date": str(latest.get("event_date")),
            },
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
