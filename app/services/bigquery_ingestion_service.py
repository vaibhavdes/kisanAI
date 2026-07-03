import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.config import settings


@dataclass(frozen=True)
class ColumnSpec:
    name: str
    kind: str = "STRING"
    required: bool = False


@dataclass(frozen=True)
class PublicDataSpec:
    source_key: str
    table: str
    columns: tuple[ColumnSpec, ...]


@dataclass(frozen=True)
class PublicDataIngestionResult:
    run_id: str
    source_key: str
    table_id: str
    records_loaded: int
    status: str
    error_message: str | None = None


PUBLIC_DATA_SPECS: dict[str, PublicDataSpec] = {
    "rainfall_daily": PublicDataSpec(
        source_key="rainfall_daily",
        table="district_rainfall_daily",
        columns=(
            ColumnSpec("state", required=True),
            ColumnSpec("district", required=True),
            ColumnSpec("observation_date", "DATE", required=True),
            ColumnSpec("rainfall_mm", "FLOAT"),
        ),
    ),
    "rainfall_normals": PublicDataSpec(
        source_key="rainfall_normals",
        table="district_rainfall_normals",
        columns=(
            ColumnSpec("state", required=True),
            ColumnSpec("district", required=True),
            ColumnSpec("month", "INT", required=True),
            ColumnSpec("normal_rainfall_mm", "FLOAT"),
        ),
    ),
    "groundwater_level": PublicDataSpec(
        source_key="groundwater_level",
        table="district_groundwater_level",
        columns=(
            ColumnSpec("state", required=True),
            ColumnSpec("district", required=True),
            ColumnSpec("block"),
            ColumnSpec("observation_date", "DATE"),
            ColumnSpec("groundwater_depth_m", "FLOAT"),
            ColumnSpec("category"),
        ),
    ),
    "soil_health_summary": PublicDataSpec(
        source_key="soil_health_summary",
        table="soil_health_summary",
        columns=(
            ColumnSpec("state", required=True),
            ColumnSpec("district", required=True),
            ColumnSpec("block"),
            ColumnSpec("village"),
            ColumnSpec("soil_type"),
            ColumnSpec("ph", "FLOAT"),
            ColumnSpec("organic_carbon", "FLOAT"),
            ColumnSpec("nitrogen"),
            ColumnSpec("phosphorus"),
            ColumnSpec("potassium"),
            ColumnSpec("micronutrients", "JSON"),
        ),
    ),
    "crop_production_history": PublicDataSpec(
        source_key="crop_production_history",
        table="crop_production_history",
        columns=(
            ColumnSpec("state", required=True),
            ColumnSpec("district"),
            ColumnSpec("crop", required=True),
            ColumnSpec("season"),
            ColumnSpec("crop_year", "INT", required=True),
            ColumnSpec("area_hectare", "FLOAT"),
            ColumnSpec("production_tonne", "FLOAT"),
            ColumnSpec("yield_kg_per_hectare", "FLOAT"),
        ),
    ),
    "agromet_advisory": PublicDataSpec(
        source_key="agromet_advisory",
        table="agromet_advisory",
        columns=(
            ColumnSpec("state", required=True),
            ColumnSpec("district"),
            ColumnSpec("bulletin_date", "DATE", required=True),
            ColumnSpec("language"),
            ColumnSpec("crop"),
            ColumnSpec("advisory_text", required=True),
            ColumnSpec("risk_tags", "ARRAY"),
        ),
    ),
}


class PublicDataIngestionService:
    def __init__(self, client: Any | None = None) -> None:
        if client is None:
            from google.cloud import bigquery

            client = bigquery.Client(project=settings.google_cloud_project)
        self.client = client

    def ingest_csv(
        self,
        *,
        source_key: str,
        csv_path: str | Path,
        source_name: str,
        source_url: str | None = None,
        source_file_uri: str | None = None,
    ) -> PublicDataIngestionResult:
        spec = self._spec(source_key)
        run_id = f"ingest_{uuid4().hex[:12]}"
        started_at = datetime.now(UTC)
        table_id = self._table_id(spec.table)
        file_path = Path(csv_path)
        file_uri = source_file_uri or str(file_path)
        self._record_run(
            run_id=run_id,
            source_name=source_name,
            source_url=source_url,
            source_file_uri=file_uri,
            status="running",
            records_loaded=0,
            started_at=started_at,
            finished_at=None,
            error_message=None,
        )
        try:
            rows = self._read_rows(file_path, spec, source_name, source_url, file_uri)
            if rows:
                self._load_rows(table_id, rows)
            self._record_run(
                run_id=run_id,
                source_name=source_name,
                source_url=source_url,
                source_file_uri=file_uri,
                status="success",
                records_loaded=len(rows),
                started_at=started_at,
                finished_at=datetime.now(UTC),
                error_message=None,
            )
            return PublicDataIngestionResult(
                run_id=run_id,
                source_key=source_key,
                table_id=table_id,
                records_loaded=len(rows),
                status="success",
            )
        except Exception as exc:
            self._record_run(
                run_id=run_id,
                source_name=source_name,
                source_url=source_url,
                source_file_uri=file_uri,
                status="failed",
                records_loaded=0,
                started_at=started_at,
                finished_at=datetime.now(UTC),
                error_message=str(exc),
            )
            raise

    def _read_rows(
        self,
        file_path: Path,
        spec: PublicDataSpec,
        source_name: str,
        source_url: str | None,
        source_file_uri: str,
    ) -> list[dict[str, Any]]:
        ingested_at = datetime.now(UTC).isoformat()
        rows: list[dict[str, Any]] = []
        with file_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            self._validate_header(reader.fieldnames or [], spec)
            for line_number, raw in enumerate(reader, start=2):
                row = self._normalize_row(raw, spec, line_number)
                row.update(
                    {
                        "source_name": source_name,
                        "source_url": source_url,
                        "source_file_uri": source_file_uri,
                        "ingested_at": ingested_at,
                    }
                )
                rows.append(row)
        return rows

    def _validate_header(self, headers: list[str], spec: PublicDataSpec) -> None:
        header_set = {header.strip() for header in headers}
        missing = [column.name for column in spec.columns if column.required and column.name not in header_set]
        if missing:
            raise ValueError(f"{spec.source_key} CSV missing required columns: {', '.join(missing)}")

    def _normalize_row(self, raw: dict[str, str | None], spec: PublicDataSpec, line_number: int) -> dict[str, Any]:
        row: dict[str, Any] = {}
        for column in spec.columns:
            value = self._clean(raw.get(column.name))
            if column.required and value is None:
                raise ValueError(f"{spec.source_key} CSV line {line_number} missing required {column.name}")
            row[column.name] = self._cast(value, column.kind, spec.source_key, column.name, line_number)
        return row

    def _cast(self, value: str | None, kind: str, source_key: str, column: str, line_number: int) -> Any:
        if value is None:
            return None
        try:
            if kind == "FLOAT":
                return float(value)
            if kind == "INT":
                return int(value)
            if kind == "JSON":
                return json.loads(value) if value else {}
            if kind == "ARRAY":
                return [item.strip() for item in value.replace("|", ",").split(",") if item.strip()]
            return value
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError(f"{source_key} CSV line {line_number} has invalid {column}: {value}") from exc

    def _load_rows(self, table_id: str, rows: list[dict[str, Any]]) -> None:
        try:
            from google.cloud import bigquery

            job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_APPEND)
            job = self.client.load_table_from_json(rows, table_id, job_config=job_config)
        except ImportError:
            job = self.client.load_table_from_json(rows, table_id, job_config=None)
        job.result()

    def _record_run(
        self,
        *,
        run_id: str,
        source_name: str,
        source_url: str | None,
        source_file_uri: str,
        status: str,
        records_loaded: int,
        started_at: datetime,
        finished_at: datetime | None,
        error_message: str | None,
    ) -> None:
        table_id = self._ops_table_id("ingestion_runs")
        row = {
            "run_id": run_id,
            "source_name": source_name,
            "source_url": source_url,
            "source_file_uri": source_file_uri,
            "status": status,
            "records_loaded": records_loaded,
            "error_message": error_message,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat() if finished_at else None,
        }
        errors = self.client.insert_rows_json(table_id, [row])
        if errors:
            raise RuntimeError(f"Failed to record ingestion run: {errors}")

    def _table_id(self, table: str) -> str:
        return f"{settings.google_cloud_project}.{settings.bigquery_public_dataset}.{table}"

    def _ops_table_id(self, table: str) -> str:
        return f"{settings.google_cloud_project}.kisan_ai_ops.{table}"

    def _spec(self, source_key: str) -> PublicDataSpec:
        try:
            return PUBLIC_DATA_SPECS[source_key]
        except KeyError as exc:
            supported = ", ".join(sorted(PUBLIC_DATA_SPECS))
            raise ValueError(f"Unsupported public data source '{source_key}'. Supported: {supported}") from exc

    def _clean(self, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned if cleaned else None
