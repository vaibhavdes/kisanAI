CREATE SCHEMA IF NOT EXISTS `kisanai-501120.kisan_ai_raw`
OPTIONS(location = "asia-south1");

CREATE SCHEMA IF NOT EXISTS `kisanai-501120.kisan_ai_curated`
OPTIONS(location = "asia-south1");

CREATE SCHEMA IF NOT EXISTS `kisanai-501120.kisan_ai_ops`
OPTIONS(location = "asia-south1");

CREATE TABLE IF NOT EXISTS `kisanai-501120.kisan_ai_ops.ingestion_runs` (
  run_id STRING NOT NULL,
  source_name STRING NOT NULL,
  source_url STRING,
  source_file_uri STRING,
  status STRING NOT NULL,
  records_loaded INT64,
  error_message STRING,
  started_at TIMESTAMP NOT NULL,
  finished_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `kisanai-501120.kisan_ai_curated.district_rainfall_daily` (
  state STRING NOT NULL,
  district STRING NOT NULL,
  observation_date DATE NOT NULL,
  rainfall_mm FLOAT64,
  source_name STRING NOT NULL,
  source_url STRING,
  source_file_uri STRING,
  ingested_at TIMESTAMP NOT NULL
)
PARTITION BY observation_date
CLUSTER BY state, district;

CREATE TABLE IF NOT EXISTS `kisanai-501120.kisan_ai_curated.district_rainfall_normals` (
  state STRING NOT NULL,
  district STRING NOT NULL,
  month INT64 NOT NULL,
  normal_rainfall_mm FLOAT64,
  source_name STRING NOT NULL,
  source_url STRING,
  source_file_uri STRING,
  ingested_at TIMESTAMP NOT NULL
)
CLUSTER BY state, district;

CREATE TABLE IF NOT EXISTS `kisanai-501120.kisan_ai_curated.district_groundwater_level` (
  state STRING NOT NULL,
  district STRING NOT NULL,
  block STRING,
  observation_date DATE,
  groundwater_depth_m FLOAT64,
  category STRING,
  source_name STRING NOT NULL,
  source_url STRING,
  source_file_uri STRING,
  ingested_at TIMESTAMP NOT NULL
)
PARTITION BY observation_date
CLUSTER BY state, district;

CREATE TABLE IF NOT EXISTS `kisanai-501120.kisan_ai_curated.soil_health_summary` (
  state STRING NOT NULL,
  district STRING NOT NULL,
  block STRING,
  village STRING,
  soil_type STRING,
  ph FLOAT64,
  organic_carbon FLOAT64,
  nitrogen STRING,
  phosphorus STRING,
  potassium STRING,
  micronutrients JSON,
  source_name STRING NOT NULL,
  source_url STRING,
  source_file_uri STRING,
  ingested_at TIMESTAMP NOT NULL
)
CLUSTER BY state, district;

CREATE TABLE IF NOT EXISTS `kisanai-501120.kisan_ai_curated.crop_production_history` (
  state STRING NOT NULL,
  district STRING,
  crop STRING NOT NULL,
  season STRING,
  crop_year INT64 NOT NULL,
  area_hectare FLOAT64,
  production_tonne FLOAT64,
  yield_kg_per_hectare FLOAT64,
  source_name STRING NOT NULL,
  source_url STRING,
  source_file_uri STRING,
  ingested_at TIMESTAMP NOT NULL
)
CLUSTER BY state, district, crop;

CREATE TABLE IF NOT EXISTS `kisanai-501120.kisan_ai_curated.agromet_advisory` (
  state STRING NOT NULL,
  district STRING,
  bulletin_date DATE NOT NULL,
  language STRING,
  crop STRING,
  advisory_text STRING NOT NULL,
  risk_tags ARRAY<STRING>,
  source_name STRING NOT NULL,
  source_url STRING,
  source_file_uri STRING,
  ingested_at TIMESTAMP NOT NULL
)
PARTITION BY bulletin_date
CLUSTER BY state, district, crop;
