# Public Data And BigQuery Ingestion

This project should prefer government or Google data first. Free third-party APIs are fallbacks only when the government/Google source is unavailable or too slow for the demo.

## Provisioning

Use Mumbai region for data residency and lower latency:

```bash
export PROJECT_ID=kisanai-501120
export REGION=asia-south1

gcloud storage buckets create gs://$PROJECT_ID-kisan-ai-public-data \
  --location=$REGION \
  --uniform-bucket-level-access

bq --location=$REGION mk --dataset $PROJECT_ID:kisan_ai_raw
bq --location=$REGION mk --dataset $PROJECT_ID:kisan_ai_curated
bq --location=$REGION mk --dataset $PROJECT_ID:kisan_ai_ops
```

Apply curated schema:

```bash
bq query --use_legacy_sql=false < infra/bigquery/public_data_schema.sql
```

Current project status:

- Bucket provisioned: `gs://kisanai-501120-kisan-ai-public-data`
- BigQuery datasets provisioned in `asia-south1`: `kisan_ai_raw`, `kisan_ai_curated`, `kisan_ai_ops`
- Curated tables provisioned from `infra/bigquery/public_data_schema.sql`
- Backend context service queries the curated tables and reports missing sources until official data rows are ingested.

## Storage Layout

```text
gs://kisanai-501120-kisan-ai-public-data/
  raw/
    imd_rainfall/yyyy=2026/mm=07/source-file.csv
    imd_agromet/yyyy=2026/mm=07/source-file.pdf
    groundwater/yyyy=2026/mm=07/source-file.csv
    soil_health/yyyy=2026/mm=07/source-file.csv
    crop_production/yyyy=2026/mm=07/source-file.csv
  normalized/
    rainfall_daily/
    agromet_advisory/
    groundwater_level/
    soil_health_summary/
    crop_production/
```

## Useful Data Sources

| Source | Link | Use |
|---|---|---|
| IMD API Platform | https://api.imd.gov.in/ | Current forecast, warnings, nowcast, weather products when API access is available. |
| IMD Agromet Advisories | https://mausam.imd.gov.in/responsive/agromet_adv_ser_state_current.php | District/state agromet bulletins, crop-weather advisory signal, official alert wording. |
| IMD Data Service Portal | https://dsp.imdpune.gov.in/ | Historical meteorological observations, climate tables, gridded climatological data. |
| UPAg | https://upag.gov.in/ | Official agriculture statistics portal for crop area, production, and yield. |
| data.gov.in APIs | https://www.data.gov.in/apis | Public API access to government datasets when resource IDs are available. |
| data.gov.in Catalog | https://www.data.gov.in/catalogs | Dataset discovery before manual download or API integration. |
| Soil Health Card | https://soilhealth.dac.gov.in/ | Soil pH, NPK, organic carbon, micronutrients when farmer image/data is available. |
| India-WRIS | https://indiawris.gov.in/wris/ | Water resources and groundwater context. |
| Google Earth Engine | https://earthengine.google.com/ | Satellite NDVI/NDWI and farm vegetation/water stress. |
| Open-Meteo | https://open-meteo.com/en/docs | Free fallback weather forecast with current/hourly/daily, ET0, soil moisture, soil temperature. |

## Ingestion Flow

1. Download or export source files manually from official portals.
2. Upload unchanged files to `raw/source/yyyy/mm`.
3. Normalize state, district, crop, season, date, and units into the CSV formats below.
4. Load normalized CSV rows into `kisan_ai_curated` with `scripts/ingest_public_data.py`.
5. Keep the unchanged raw file path in `source_file_uri`.
6. Advisory and recommendation services read only curated tables.
7. Keep source URL, source file path, license/permission notes, and ingestion timestamp in each table.

## IMD API vs BigQuery

Use the IMD API platform for live or near-real-time products when access is approved: forecast, warnings, nowcast, current observations, and weather products. Use BigQuery for reference or repeatedly queried datasets: historical rainfall normals, downloaded rainfall observations, agromet bulletins, groundwater snapshots, soil summaries, and crop production history. This avoids repeated API calls during advisory generation and makes every recommendation auditable.

## Why Manual First

- Many government sources are CSV/XLS/PDF portals, not stable JSON APIs.
- Manual ingestion avoids unnecessary live API calls and gives repeatable hackathon demos.
- Curated BigQuery tables make advisory decisions fast and auditable.

## First Tables To Populate

1. `district_rainfall_daily`
   - Drives dry-spell baseline and crop suitability by season.
2. `district_rainfall_normals`
   - Compares forecast rainfall against historical normal.
3. `district_groundwater_level`
   - Penalizes high-water crops where groundwater is deep.
4. `soil_health_summary`
   - Adds soil pH/NPK/organic carbon signal where farmer soil card is missing.
5. `crop_production_history`
   - Adds regional yield history for crop recommendation.
6. `agromet_advisory`
   - Adds official IMD advisory context for Gemini prompt grounding.

## Normalized CSV Load Commands

Run from the project root after `gcloud auth application-default login` or with `GOOGLE_APPLICATION_CREDENTIALS` configured:

```bash
python scripts/ingest_public_data.py rainfall_normals data/normalized/rainfall_normals.csv \
  --source-name "IMD rainfall normals" \
  --source-url "https://dsp.imdpune.gov.in/" \
  --source-file-uri "gs://kisanai-501120-kisan-ai-public-data/raw/imd_rainfall/source.csv"
```

Supported `source_key` values:

| source_key | BigQuery table | Required CSV columns |
|---|---|---|
| `rainfall_daily` | `district_rainfall_daily` | `state,district,observation_date` |
| `rainfall_normals` | `district_rainfall_normals` | `state,district,month` |
| `groundwater_level` | `district_groundwater_level` | `state,district` |
| `soil_health_summary` | `soil_health_summary` | `state,district` |
| `crop_production_history` | `crop_production_history` | `state,crop,crop_year` |
| `agromet_advisory` | `agromet_advisory` | `state,bulletin_date,advisory_text` |

Optional columns are accepted when available:

```text
rainfall_daily: rainfall_mm
rainfall_normals: normal_rainfall_mm
groundwater_level: block, observation_date, groundwater_depth_m, category
soil_health_summary: block, village, soil_type, ph, organic_carbon, nitrogen, phosphorus, potassium, micronutrients
crop_production_history: district, season, area_hectare, production_tonne, yield_kg_per_hectare
agromet_advisory: district, language, crop, risk_tags
```

Formatting rules:

- Dates use `YYYY-MM-DD`.
- `risk_tags` can be comma- or pipe-separated, for example `rain|spray|pest`.
- `micronutrients` should be JSON, for example `{"zinc":"low","boron":"medium"}`.
- Every load writes `running`, then `success` or `failed`, into `kisan_ai_ops.ingestion_runs`.
## Service Usage Rule

For every advisory decision, store the sources used:

```json
{
  "weather": "imd_api",
  "weatherFallback": "open_meteo",
  "rainfallHistory": "bigquery:district_rainfall_normals",
  "groundwater": "bigquery:district_groundwater_level",
  "satellite": "earth_engine",
  "advisory": "gemini"
}
```
