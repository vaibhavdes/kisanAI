#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-kisanai-501120}"
REGION="${REGION:-asia-south1}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-kisan-alert-runner}"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_EMAIL:-${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com}"
STORAGE_BUCKET="${STORAGE_BUCKET:-${PROJECT_ID}-kisan-ai-media}"
PUBSUB_ALERT_TOPIC="${PUBSUB_ALERT_TOPIC:-kisan-alerts}"
BIGQUERY_LOCATION="${BIGQUERY_LOCATION:-${REGION}}"
APPLY_BIGQUERY_SCHEMA="${APPLY_BIGQUERY_SCHEMA:-true}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_DIR="$(cd "${BACKEND_DIR}/.." && pwd)"
SCHEMA_FILE="${SCHEMA_FILE:-${BACKEND_DIR}/infra/bigquery/public_data_schema.sql}"
ENV_FILE="${ENV_FILE:-${REPO_DIR}/.env}"

echo "Provisioning Kisan Alert resources in project ${PROJECT_ID}, region ${REGION}"

gcloud config set project "${PROJECT_ID}" >/dev/null

gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  firestore.googleapis.com \
  pubsub.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com \
  dialogflow.googleapis.com \
  speech.googleapis.com \
  texttospeech.googleapis.com \
  translate.googleapis.com \
  earthengine.googleapis.com \
  bigquery.googleapis.com \
  storage.googleapis.com \
  geocoding-backend.googleapis.com \
  maps-backend.googleapis.com

if ! gcloud iam service-accounts describe "${SERVICE_ACCOUNT_EMAIL}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}" \
    --display-name="Kisan Alert Cloud Run service account"
fi

for role in \
  roles/datastore.user \
  roles/bigquery.jobUser \
  roles/bigquery.dataViewer \
  roles/storage.objectAdmin \
  roles/pubsub.publisher \
  roles/pubsub.subscriber \
  roles/secretmanager.secretAccessor \
  roles/aiplatform.user \
  roles/speech.client \
  roles/cloudtranslate.user \
  roles/dialogflow.client \
  roles/cloudscheduler.admin; do
  if ! gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="${role}" \
    --quiet >/dev/null; then
    echo "Warning: could not grant ${role} to ${SERVICE_ACCOUNT_EMAIL}. Check role availability/permissions." >&2
  fi
done

if ! gcloud storage buckets describe "gs://${STORAGE_BUCKET}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${STORAGE_BUCKET}" \
    --location="${REGION}" \
    --uniform-bucket-level-access
fi

if ! gcloud pubsub topics describe "${PUBSUB_ALERT_TOPIC}" >/dev/null 2>&1; then
  gcloud pubsub topics create "${PUBSUB_ALERT_TOPIC}"
fi

if [[ -f "${ENV_FILE}" ]]; then
  PROJECT_ID="${PROJECT_ID}" ENV_FILE="${ENV_FILE}" "${SCRIPT_DIR}/sync_env_to_secret_manager.sh"
else
  echo "No .env found at ${ENV_FILE}; skipping Secret Manager sync."
fi

if [[ "${APPLY_BIGQUERY_SCHEMA}" == "true" ]]; then
  TMP_SCHEMA="$(mktemp)"
  sed "s/kisanai-501120/${PROJECT_ID}/g; s/asia-south1/${BIGQUERY_LOCATION}/g" "${SCHEMA_FILE}" > "${TMP_SCHEMA}"
  bq --project_id="${PROJECT_ID}" query --use_legacy_sql=false < "${TMP_SCHEMA}"
  rm -f "${TMP_SCHEMA}"
fi

cat <<EOF

Provisioning complete.

Firestore:
  If this is a new project, create Firestore Native mode once:
  gcloud firestore databases create --database="(default)" --location="${REGION}"

Storage bucket:
  gs://${STORAGE_BUCKET}

Pub/Sub topic:
  ${PUBSUB_ALERT_TOPIC}

Service account:
  ${SERVICE_ACCOUNT_EMAIL}
EOF
