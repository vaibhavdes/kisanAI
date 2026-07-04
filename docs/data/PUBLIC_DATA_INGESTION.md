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
| IMD Free Data Access | https://dsp.imdpune.gov.in/home_freedataaccess.php | All-India monthly/seasonal rainfall series and other free climate series. |
| IMD Gridded Climatology | https://dsp.imdpune.gov.in/home_gridded_climatology.php | Monthly gridded rainfall climatology, including 0.25 x 0.25 degree rainfall. |
| IMD Station Normals | https://dsp.imdpune.gov.in/home_normals.php | Station climatological normals; useful for nearest-station baseline where district data is missing. |
| IMD Data Service Portal | https://dsp.imdpune.gov.in/ | Historical meteorological observations, climate tables, free series and gridded climatological data. |
| UPAg | https://upag.gov.in/ | Official agriculture statistics portal for crop area, production, and yield. |
| data.gov.in APIs | https://www.data.gov.in/apis | Public API access to government datasets when resource IDs are available. |
| data.gov.in Catalog | https://www.data.gov.in/catalogs | Dataset discovery before manual download or API integration. |
| Soil Health Card | https://soilhealth.dac.gov.in/ | Soil pH, NPK, organic carbon, micronutrients when farmer image/data is available. |
| India-WRIS | https://indiawris.gov.in/wris/ | Water resources and groundwater context. |
| Earth Engine Data Catalog | https://developers.google.com/earth-engine/datasets | Dataset catalog for satellite and climate signals. |
| Sentinel-2 Surface Reflectance | https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED | Farm-level NDVI, NDWI, NDMI, NDRE where cloud-free imagery is available. |
| MODIS MOD13Q1 Vegetation Indices | https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13Q1 | 16-day NDVI/EVI backup when Sentinel imagery is cloudy or too sparse. |
| CHIRPS Daily Rainfall | https://developers.google.com/earth-engine/datasets/catalog/UCSB-CHG_CHIRPS_DAILY | Long rainfall time series for drought/dry-spell context when official district rows are unavailable. |
| SMAP L4 Soil Moisture | https://developers.google.com/earth-engine/datasets/catalog/NASA_SMAP_SPL4SMGP_008 | Surface/root-zone soil moisture and wetness signals. |
| Open-Meteo | https://open-meteo.com/en/docs | Free fallback weather forecast with current/hourly/daily, ET0, soil moisture, soil temperature. |

## Maharashtra Sources Added

| Source | Endpoint / file | Loaded into | Current status |
|---|---|---|---|
| data.gov.in IMD subdivision rainfall resource | `https://api.data.gov.in/resource/d0419b03-b41b-4226-b48b-0bc92bf139f8` | `subdivision_rainfall_history` | Script ready; live API timed out locally, so current load uses the downloaded CSV. |
| Downloaded IMD subdivision CSV | `Sub_Division_IMD_2017.csv` | `subdivision_rainfall_history` | Loaded: 50,256 rows. |
| Maharain tehsil dry spell | `https://maharain.maharashtra.gov.in/test/maharain/rpt_past_queries_tehsil_wise_dryspell.php` | `maharashtra_dryspell_events` | Loaded 2021-2025: 6,747 rows. |
| Maharain tehsil heavy rainfall | `https://maharain.maharashtra.gov.in/test/maharain/rpt_past_queries_tehsil_wise_heavy_rainfall.php` | `maharashtra_heavy_rainfall_events` | Loaded 2021-2025: 6,023 rows. |
| Maharashtra rice estimate CSV | `Final-Estimate-of-Area,-Production-&-Yield-for-Rice.csv` | `crop_production_history` | Loaded: 15 rows. |
| All-India crop-wise APY CSV | `All-India_-Crop-wise-Area,-Production-&-Yield.csv` | `crop_production_history` | Loaded: 474 rows. |
| All-India year-wise APY CSV | `All-India_-Year-wise-Crop-Area,-Production-&-Yield.csv` | `crop_production_history` | Loaded: 4,888 rows. |
| DES district XLSX 2024-25 | `DES-District-Data-For-2024-25.xlsx` | `crop_production_history` | Loaded Maharashtra visible row: 1 row. |

## Source To Table Mapping

| Priority | Dataset | Primary source | Fallback/source helper | BigQuery table | Why it matters |
|---|---|---|---|---|---|
| 1 | District or nearest-grid rainfall normals | IMD gridded climatology / DSP | CHIRPS via Earth Engine, if official rows are delayed | `district_rainfall_normals` | Crop suitability and seasonal rainfall baseline. |
| 2 | Recent/daily rainfall observations | IMD API or DSP exports | CHIRPS daily rainfall through Earth Engine | `district_rainfall_daily` | Dry-spell detection and irrigation timing. |
| 3 | Current forecast, wind, humidity, ET0 | IMD API when approved | Open-Meteo Forecast API | Not stored by default; cached/runtime weather context | Real-time advisory and alert generation. |
| 4 | Official agromet bulletins | IMD agromet district/state bulletins | Manual bulletin upload until API is available | `agromet_advisory` | Grounds Gemini/Vertex advice in official advisory wording. |
| 5 | Groundwater depth/status | India-WRIS / CGWB official exports | Manual state/district CSV export | `district_groundwater_level` | Penalizes high-water crops and flags irrigation risk. |
| 6 | Soil pH/NPK/organic carbon | Farmer soil card OCR + Soil Health Card portal exports | District/block manual summary CSV | `soil_health_summary` | Crop recommendation and fertilizer guidance. |
| 7 | Crop area/production/yield | UPAg official statistics | data.gov.in catalog/API resource if available | `crop_production_history` | Regional crop performance signal for recommendation. |
| 8 | Farm vegetation/water stress | Earth Engine Sentinel-2 | MODIS vegetation index backup | Runtime Earth Engine response, optionally exported later | NDVI/NDWI/NDMI/NDRE crop health and water stress. |

## Exact Loading Order

1. `district_rainfall_normals`
   - Download monthly rainfall climatology from IMD DSP gridded climatology or free-data tables.
   - Normalize to `state,district,month,normal_rainfall_mm`.
   - Load with `source_key=rainfall_normals`.
2. `district_rainfall_daily`
   - Use IMD API once approved for daily district/rainfall products, or export observations from DSP.
   - For demo fallback, generate district-level daily aggregates from CHIRPS through Earth Engine.
   - Normalize to `state,district,observation_date,rainfall_mm`.
   - Load with `source_key=rainfall_daily`.
3. `district_groundwater_level`
   - Download district/block groundwater level/status from India-WRIS or CGWB/state reports.
   - Normalize to `state,district,block,observation_date,groundwater_depth_m,category`.
   - Load with `source_key=groundwater_level`.
4. `soil_health_summary`
   - Prefer farmer-level soil-card OCR results during runtime.
   - For missing farmer cards, load district/block summaries exported from Soil Health Card/state soil datasets.
   - Normalize to `state,district,block,village,soil_type,ph,organic_carbon,nitrogen,phosphorus,potassium,micronutrients`.
   - Load with `source_key=soil_health_summary`.
5. `crop_production_history`
   - Download crop area/production/yield from UPAg or the matching data.gov.in catalog resource.
   - Normalize to `state,district,crop,crop_year,season,area_hectare,production_tonne,yield_kg_per_hectare`.
   - Load with `source_key=crop_production_history`.
6. `agromet_advisory`
   - Download current and past IMD agromet bulletins.
   - Normalize PDF/text bulletin rows to `state,district,bulletin_date,language,crop,advisory_text,risk_tags`.
   - Load with `source_key=agromet_advisory`.

## Fetch And Normalize Commands

Normalize the downloaded IMD subdivision CSV:

```bash
.venv-google/bin/python scripts/fetch_public_data_sources.py normalize-imd-subdivision \
  /Users/vaibhavkurkute/Downloads/Sub_Division_IMD_2017.csv \
  --out data/normalized/subdivision_rainfall_history/imd_subdivision_2017.csv
```

Fetch data.gov IMD subdivision data when the API is responsive:

```bash
.venv-google/bin/python scripts/fetch_public_data_sources.py fetch-data-gov-imd-subdivision \
  --api-key "$DATA_GOV_API_KEY" \
  --limit 100 \
  --total 641 \
  --out-dir data/raw/data_gov \
  --normalized-out data/normalized/subdivision_rainfall_history/data_gov_imd_subdivision.csv
```

Fetch Maharain dry-spell and heavy-rainfall events for the last five seasons:

```bash
.venv-google/bin/python scripts/fetch_public_data_sources.py fetch-maharain \
  --start-year 2021 \
  --end-year 2025 \
  --out-dir data/raw/maharain \
  --normalized-dir data/normalized \
  --insecure
```

`--insecure` is explicit because the Maharain server certificate chain failed local Python CA verification. Keep it visible in scripts and CI logs rather than disabling TLS verification silently.

Normalize crop-history files:

```bash
.venv-google/bin/python scripts/fetch_public_data_sources.py normalize-crop-csv \
  "/Users/vaibhavkurkute/Downloads/Final-Estimate-of-Area,-Production-&-Yield-for-Rice.csv" \
  --state-filter Maharashtra \
  --out data/normalized/crop_production_history/maharashtra_rice_estimate.csv

.venv-google/bin/python scripts/fetch_public_data_sources.py normalize-crop-csv \
  "/Users/vaibhavkurkute/Downloads/All-India_-Crop-wise-Area,-Production-&-Yield.csv" \
  --out data/normalized/crop_production_history/all_india_crop_wise.csv

.venv-google/bin/python scripts/fetch_public_data_sources.py normalize-crop-csv \
  "/Users/vaibhavkurkute/Downloads/All-India_-Year-wise-Crop-Area,-Production-&-Yield.csv" \
  --out data/normalized/crop_production_history/all_india_year_wise.csv

.venv-google/bin/python scripts/fetch_public_data_sources.py normalize-des-district-xlsx \
  "/Users/vaibhavkurkute/Downloads/DES-District-Data-For-2024-25.xlsx" \
  --state-filter Maharashtra \
  --out data/normalized/crop_production_history/maharashtra_des_district_2024_25.csv
```

Apply schema and load:

```bash
bq query --use_legacy_sql=false < infra/bigquery/public_data_schema.sql

.venv-google/bin/python scripts/ingest_public_data.py subdivision_rainfall_history \
  data/normalized/subdivision_rainfall_history/imd_subdivision_2017.csv \
  --source-name "IMD subdivision rainfall CSV" \
  --source-url "https://api.data.gov.in/resource/d0419b03-b41b-4226-b48b-0bc92bf139f8" \
  --source-file-uri "local:data/normalized/subdivision_rainfall_history/imd_subdivision_2017.csv"

.venv-google/bin/python scripts/ingest_public_data.py maharashtra_dryspell_events \
  data/normalized/maharashtra_dryspell_events/maharain_dryspell.csv \
  --source-name "Maharain tehsil dry spell" \
  --source-url "https://maharain.maharashtra.gov.in/test/maharain/rpt_past_queries_tehsil_wise_dryspell.php"

.venv-google/bin/python scripts/ingest_public_data.py maharashtra_heavy_rainfall_events \
  data/normalized/maharashtra_heavy_rainfall_events/maharain_heavy_rainfall.csv \
  --source-name "Maharain tehsil heavy rainfall" \
  --source-url "https://maharain.maharashtra.gov.in/test/maharain/rpt_past_queries_tehsil_wise_heavy_rainfall.php"
```

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
| `subdivision_rainfall_history` | `subdivision_rainfall_history` | `subdivision,year,month` |
| `maharashtra_dryspell_events` | `maharashtra_dryspell_events` | `state,district,taluka,season_year,start_date,end_date` |
| `maharashtra_heavy_rainfall_events` | `maharashtra_heavy_rainfall_events` | `state,district,taluka,season_year,event_date` |

Optional columns are accepted when available:

```text
rainfall_daily: rainfall_mm
rainfall_normals: normal_rainfall_mm
groundwater_level: block, observation_date, groundwater_depth_m, category
soil_health_summary: block, village, soil_type, ph, organic_carbon, nitrogen, phosphorus, potassium, micronutrients
crop_production_history: district, season, area_hectare, production_tonne, yield_kg_per_hectare
agromet_advisory: district, language, crop, risk_tags
subdivision_rainfall_history: rainfall_mm
maharashtra_dryspell_events: duration_days
maharashtra_heavy_rainfall_events: rainfall_mm
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

## Regional Cache Policy

Many farmers in the same area can reuse the same data. The backend now includes `RegionalCachePolicy` and the `kisan_ai_ops.regional_source_cache` table to standardize reuse:

| Source type | Refresh window |
|---|---|
| Weather forecast | 3 hours |
| IMD warning | 1 hour |
| Agromet advisory | 24 hours |
| Earth Engine satellite index | 7 days |
| Maharain dry-spell/heavy-rainfall events | 7 days |
| Groundwater | 30 days |
| Soil health baseline | 90 days |
| Crop history | 365 days |

Cache keys use source type, provider, state, district, taluka and, when needed, rounded latitude/longitude cells. This lets a forecast or satellite query for one mapped farm be reused for nearby farms in the same region until its refresh window expires.
