#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-kisanai-501120}"
ENV_FILE="${ENV_FILE:-}"

if [[ -z "${ENV_FILE}" ]]; then
  if [[ -f ".env" ]]; then
    ENV_FILE=".env"
  elif [[ -f "../.env" ]]; then
    ENV_FILE="../.env"
  else
    echo "No .env found. Pass ENV_FILE=/path/to/.env" >&2
    exit 1
  fi
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ENV_FILE not found: ${ENV_FILE}" >&2
  exit 1
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

load_env_file "${ENV_FILE}"

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-${PROJECT_ID}}"

gcloud config set project "${PROJECT_ID}" >/dev/null
gcloud services enable secretmanager.googleapis.com >/dev/null

sync_secret() {
  local env_name="$1"
  local value="${!env_name:-}"
  local secret_name="${env_name}"

  if [[ -z "${value}" ]]; then
    return
  fi

  if ! gcloud secrets describe "${secret_name}" >/dev/null 2>&1; then
    gcloud secrets create "${secret_name}" --replication-policy="automatic" >/dev/null
  fi

  printf "%s" "${value}" | gcloud secrets versions add "${secret_name}" --data-file=- >/dev/null
  echo "Synced ${env_name} -> Secret Manager secret ${secret_name}"
}

for env_name in \
  GEMINI_API_KEY \
  SARVAM_API_KEY \
  AUTHKEY_API_KEY \
  AUTHKEY_WHATSAPP_TEMPLATE_ID \
  AUTHKEY_WHATSAPP_MEDIA_TEMPLATE_ID \
  TWILIO_ACCOUNT_SID \
  TWILIO_AUTH_TOKEN \
  TWILIO_CONTENT_SID \
  TWILIO_CONTENT_VARIABLES \
  TWILIO_MESSAGING_SERVICE_SID \
  MAPS_API_KEY \
  IMD_API_KEY \
  SMS_PROVIDER_API_KEY \
  WHATSAPP_BUSINESS_TOKEN \
  VOICE_CALL_PROVIDER_API_KEY; do
  sync_secret "${env_name}"
done

echo "Secret sync complete for project ${PROJECT_ID}."
