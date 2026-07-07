#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-kisanai-501120}"
REGION="${REGION:-asia-south1}"
SERVICE_NAME="${FRONTEND_SERVICE_NAME:-kisan-alert-web}"
BACKEND_SERVICE_NAME="${BACKEND_SERVICE_NAME:-kisan-alert-api}"
EXPO_PUBLIC_API_URL="${EXPO_PUBLIC_API_URL:-}"

gcloud config set project "${PROJECT_ID}" >/dev/null

if [[ -z "${EXPO_PUBLIC_API_URL}" ]]; then
  EXPO_PUBLIC_API_URL=$(gcloud run services describe "${BACKEND_SERVICE_NAME}" \
    --region "${REGION}" \
    --format="value(status.url)")
fi

gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com >/dev/null

gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --region "${REGION}" \
  --allow-unauthenticated \
  --set-env-vars "EXPO_PUBLIC_API_URL=${EXPO_PUBLIC_API_URL}" \
  --set-build-env-vars "EXPO_PUBLIC_API_URL=${EXPO_PUBLIC_API_URL}"

FRONTEND_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --format="value(status.url)")

echo "Frontend URL: ${FRONTEND_URL}"
echo "Frontend backend API URL: ${EXPO_PUBLIC_API_URL}"
