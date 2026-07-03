#!/usr/bin/env bash
set -euo pipefail

SERVICE_URL="${SERVICE_URL:-}"
PROJECT_ID="${PROJECT_ID:-kisanai-501120}"
REGION="${REGION:-asia-south1}"
SERVICE_NAME="${SERVICE_NAME:-kisan-alert-api}"

if [[ -z "${SERVICE_URL}" ]]; then
  gcloud config set project "${PROJECT_ID}" >/dev/null
  SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --region "${REGION}" \
    --format="value(status.url)")
fi

cat <<URLS
Backend:
  Health:              ${SERVICE_URL}/health
  Admin:               ${SERVICE_URL}/admin

Dialogflow CX:
  Fulfillment webhook: ${SERVICE_URL}/api/v1/dialogflow/webhook

Authkey / WhatsApp:
  WhatsApp inbound:    ${SERVICE_URL}/api/v1/whatsapp/webhook
  WhatsApp receipt:    ${SERVICE_URL}/api/v1/whatsapp/receipt
  SMS inbound:         ${SERVICE_URL}/api/v1/sms/webhook
  SMS receipt:         ${SERVICE_URL}/api/v1/sms/receipt
  Voice-call inbound:  ${SERVICE_URL}/api/v1/calls/webhook
  Voice-call receipt:  ${SERVICE_URL}/api/v1/calls/receipt

Scheduler/PubSub:
  Daily alert worker:  ${SERVICE_URL}/api/v1/alerts/run-daily/pubsub
URLS
