#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-kisanai-501120}"
REGION="${REGION:-asia-south1}"
SERVICE_NAME="${SERVICE_NAME:-kisan-alert-api}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-kisan-alert-runner}"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_EMAIL:-${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com}"
FIRESTORE_DATABASE="${FIRESTORE_DATABASE:-(default)}"
BIGQUERY_PUBLIC_DATASET="${BIGQUERY_PUBLIC_DATASET:-kisan_ai_curated}"
STORAGE_BUCKET="${STORAGE_BUCKET:-${PROJECT_ID}-kisan-ai-media}"
PUBSUB_ALERT_TOPIC="${PUBSUB_ALERT_TOPIC:-kisan-alerts}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.5-flash}"
VERTEX_AI_MODEL="${VERTEX_AI_MODEL:-gemini-2.5-flash}"
OPEN_METEO_BASE_URL="${OPEN_METEO_BASE_URL:-https://api.open-meteo.com/v1/forecast}"
RYTHU_SEVA_DEFAULT_CENTER="${RYTHU_SEVA_DEFAULT_CENTER:-RSK Demo Center}"

echo "Deploying ${SERVICE_NAME} to project ${PROJECT_ID}, region ${REGION}"

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
  storage.googleapis.com

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
  roles/secretmanager.secretAccessor \
  roles/aiplatform.user \
  roles/dialogflow.client; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="${role}" \
    --quiet >/dev/null
done

ENV_VARS=$(
  IFS=,
  echo "ENVIRONMENT=production,\
DATA_STORE_PROVIDER=firestore,\
ENABLE_GOOGLE_INTEGRATIONS=true,\
GOOGLE_CLOUD_PROJECT=${PROJECT_ID},\
GOOGLE_CLOUD_LOCATION=${REGION},\
GCP_REGION=${REGION},\
FIRESTORE_DATABASE=${FIRESTORE_DATABASE},\
BIGQUERY_PUBLIC_DATASET=${BIGQUERY_PUBLIC_DATASET},\
STORAGE_BUCKET=${STORAGE_BUCKET},\
PUBSUB_ALERT_TOPIC=${PUBSUB_ALERT_TOPIC},\
GEMINI_MODEL=${GEMINI_MODEL},\
VERTEX_AI_MODEL=${VERTEX_AI_MODEL},\
OPEN_METEO_BASE_URL=${OPEN_METEO_BASE_URL},\
RYTHU_SEVA_DEFAULT_CENTER=${RYTHU_SEVA_DEFAULT_CENTER},\
DIALOGFLOW_ROUTING_ENABLED=${DIALOGFLOW_ROUTING_ENABLED:-false},\
DIALOGFLOW_LOCATION=${DIALOGFLOW_LOCATION:-${REGION}},\
DIALOGFLOW_AGENT_ID=${DIALOGFLOW_AGENT_ID:-},\
DIALOGFLOW_ENVIRONMENT_ID=${DIALOGFLOW_ENVIRONMENT_ID:-},\
DIALOGFLOW_CONFIDENCE_THRESHOLD=${DIALOGFLOW_CONFIDENCE_THRESHOLD:-0.45}"
)

SECRET_MAPPINGS=()
if [[ -n "${GEMINI_API_KEY_SECRET:-}" ]]; then
  SECRET_MAPPINGS+=("GEMINI_API_KEY=${GEMINI_API_KEY_SECRET}:latest")
fi
if [[ -n "${SARVAM_API_KEY_SECRET:-}" ]]; then
  SECRET_MAPPINGS+=("SARVAM_API_KEY=${SARVAM_API_KEY_SECRET}:latest")
fi
if [[ -n "${AUTHKEY_API_KEY_SECRET:-}" ]]; then
  SECRET_MAPPINGS+=("AUTHKEY_API_KEY=${AUTHKEY_API_KEY_SECRET}:latest")
fi
if [[ -n "${MAPS_API_KEY_SECRET:-}" ]]; then
  SECRET_MAPPINGS+=("MAPS_API_KEY=${MAPS_API_KEY_SECRET}:latest")
fi

SECRET_ARGS=()
if [[ "${#SECRET_MAPPINGS[@]}" -gt 0 ]]; then
  SECRET_ARGS+=(--set-secrets "$(IFS=,; echo "${SECRET_MAPPINGS[*]}")")
fi

gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --region "${REGION}" \
  --service-account "${SERVICE_ACCOUNT_EMAIL}" \
  --allow-unauthenticated \
  --set-env-vars "${ENV_VARS}" \
  "${SECRET_ARGS[@]}"

SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --format="value(status.url)")

echo
echo "Cloud Run URL: ${SERVICE_URL}"
echo "Health: ${SERVICE_URL}/health"
echo "Admin: ${SERVICE_URL}/admin"
echo "Dialogflow webhook: ${SERVICE_URL}/api/v1/dialogflow/webhook"
echo "WhatsApp webhook: ${SERVICE_URL}/api/v1/whatsapp/webhook"
echo "SMS webhook: ${SERVICE_URL}/api/v1/sms/webhook"
echo "Voice-call webhook: ${SERVICE_URL}/api/v1/calls/webhook"
