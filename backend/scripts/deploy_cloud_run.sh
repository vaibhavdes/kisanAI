#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-kisanai-501120}"
REGION="${REGION:-asia-south1}"
SERVICE_NAME="${SERVICE_NAME:-kisan-alert-api}"
ENV_FILE="${ENV_FILE:-}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-kisan-alert-runner}"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_EMAIL:-}"
FIRESTORE_DATABASE="${FIRESTORE_DATABASE:-(default)}"
BIGQUERY_PUBLIC_DATASET="${BIGQUERY_PUBLIC_DATASET:-kisan_ai_curated}"
STORAGE_BUCKET="${STORAGE_BUCKET:-${PROJECT_ID}-kisan-ai-media}"
PUBSUB_ALERT_TOPIC="${PUBSUB_ALERT_TOPIC:-kisan-alerts}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.5-flash}"
VERTEX_AI_MODEL="${VERTEX_AI_MODEL:-gemini-2.5-flash}"
OPEN_METEO_BASE_URL="${OPEN_METEO_BASE_URL:-https://api.open-meteo.com/v1/forecast}"
RYTHU_SEVA_DEFAULT_CENTER="${RYTHU_SEVA_DEFAULT_CENTER:-RSK Demo Center}"

if [[ -z "${ENV_FILE}" ]]; then
  if [[ -f ".env" ]]; then
    ENV_FILE=".env"
  elif [[ -f "../.env" ]]; then
    ENV_FILE="../.env"
  fi
fi

load_env_file() {
  local file="$1"
  local line key value
  while IFS= read -r line || [[ -n "${line}" ]]; do
    line="${line%$'\r'}"
    [[ -z "${line}" || "${line}" =~ ^[[:space:]]*# ]] && continue
    [[ "${line}" != *=* ]] && continue
    key="${line%%=*}"
    value="${line#*=}"
    key="$(echo "${key}" | xargs)"
    [[ "${key}" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    if [[ "${value}" == \"*\" && "${value}" == *\" ]]; then
      value="${value:1:${#value}-2}"
    elif [[ "${value}" == \'*\' && "${value}" == *\' ]]; then
      value="${value:1:${#value}-2}"
    fi
    export "${key}=${value}"
  done < "${file}"
}

if [[ -n "${ENV_FILE}" && -f "${ENV_FILE}" ]]; then
  load_env_file "${ENV_FILE}"
fi

SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_EMAIL:-${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com}"

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
    --display-name="Kisan AI Cloud Run service account"
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
IMD_API_BASE_URL=${IMD_API_BASE_URL:-},\
AUTHKEY_TEST_COUNTRY_CODE=${AUTHKEY_TEST_COUNTRY_CODE:-91},\
AUTHKEY_SMS_SENDER=${AUTHKEY_SMS_SENDER:-},\
AUTHKEY_SEND_ENABLED=${AUTHKEY_SEND_ENABLED:-false},\
TWILIO_WHATSAPP_FROM=${TWILIO_WHATSAPP_FROM:-whatsapp:+14155238886},\
TWILIO_MESSAGING_SERVICE_SID=${TWILIO_MESSAGING_SERVICE_SID:-},\
TWILIO_CONTENT_SID=${TWILIO_CONTENT_SID:-},\
TWILIO_STATUS_CALLBACK_URL=${TWILIO_STATUS_CALLBACK_URL:-},\
TWILIO_PUBLIC_BASE_URL=${TWILIO_PUBLIC_BASE_URL:-},\
TWILIO_MEDIA_BUCKET=${TWILIO_MEDIA_BUCKET:-${STORAGE_BUCKET}},\
TWILIO_MEDIA_PUBLIC_BASE_URL=${TWILIO_MEDIA_PUBLIC_BASE_URL:-},\
TWILIO_MEDIA_SIGNED_URL_MINUTES=${TWILIO_MEDIA_SIGNED_URL_MINUTES:-15},\
TWILIO_MEDIA_MEMORY_TTL_SECONDS=${TWILIO_MEDIA_MEMORY_TTL_SECONDS:-600},\
TWILIO_VALIDATE_WEBHOOKS=${TWILIO_VALIDATE_WEBHOOKS:-false},\
TWILIO_ENABLE_LIVE_SEND=${TWILIO_ENABLE_LIVE_SEND:-false},\
SARVAM_API_BASE_URL=${SARVAM_API_BASE_URL:-https://api.sarvam.ai},\
SARVAM_STT_MODEL=${SARVAM_STT_MODEL:-saaras:v3},\
SARVAM_TRANSLATE_MODEL=${SARVAM_TRANSLATE_MODEL:-mayura:v1},\
DIALOGFLOW_ROUTING_ENABLED=${DIALOGFLOW_ROUTING_ENABLED:-false},\
DIALOGFLOW_LOCATION=${DIALOGFLOW_LOCATION:-${REGION}},\
DIALOGFLOW_AGENT_ID=${DIALOGFLOW_AGENT_ID:-},\
DIALOGFLOW_ENVIRONMENT_ID=${DIALOGFLOW_ENVIRONMENT_ID:-},\
DIALOGFLOW_CONFIDENCE_THRESHOLD=${DIALOGFLOW_CONFIDENCE_THRESHOLD:-0.45}"
)

SECRET_MAPPINGS=()
for env_name in \
  GEMINI_API_KEY \
  SARVAM_API_KEY \
  AUTHKEY_API_KEY \
  TWILIO_ACCOUNT_SID \
  TWILIO_AUTH_TOKEN \
  TWILIO_CONTENT_VARIABLES \
  MAPS_API_KEY \
  IMD_API_KEY \
  SMS_PROVIDER_API_KEY \
  WHATSAPP_BUSINESS_TOKEN \
  VOICE_CALL_PROVIDER_API_KEY; do
  secret_var="${env_name}_SECRET"
  secret_name="${!secret_var:-${env_name}}"
  if gcloud secrets describe "${secret_name}" >/dev/null 2>&1; then
    SECRET_MAPPINGS+=("${env_name}=${secret_name}:latest")
  fi
done

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

if [[ -z "${TWILIO_PUBLIC_BASE_URL:-}" && -z "${TWILIO_STATUS_CALLBACK_URL:-}" ]]; then
  gcloud run services update "${SERVICE_NAME}" \
    --region "${REGION}" \
    --update-env-vars "TWILIO_PUBLIC_BASE_URL=${SERVICE_URL}" \
    --quiet >/dev/null
  echo "Set TWILIO_PUBLIC_BASE_URL to Cloud Run URL for Twilio callbacks and signature validation."
fi

echo
echo "Cloud Run URL: ${SERVICE_URL}"
echo "Health: ${SERVICE_URL}/health"
echo "Admin: ${SERVICE_URL}/admin"
echo "Dialogflow webhook: ${SERVICE_URL}/api/v1/dialogflow/webhook"
echo "Twilio WhatsApp webhook: ${SERVICE_URL}/api/v1/twilio/whatsapp"
echo "Twilio status callback: ${SERVICE_URL}/api/v1/twilio/status"
echo "SMS webhook: ${SERVICE_URL}/api/v1/sms/webhook"
echo "Voice-call webhook: ${SERVICE_URL}/api/v1/calls/webhook"
