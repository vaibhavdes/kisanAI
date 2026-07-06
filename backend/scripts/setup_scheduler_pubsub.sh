#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-kisanai-501120}"
REGION="${REGION:-asia-south1}"
SERVICE_NAME="${SERVICE_NAME:-kisan-alert-api}"
TOPIC_NAME="${PUBSUB_ALERT_TOPIC:-kisan-alerts}"
SUBSCRIPTION_NAME="${SUBSCRIPTION_NAME:-kisan-alerts-daily-push}"
SCHEDULER_JOB_NAME="${SCHEDULER_JOB_NAME:-kisan-alerts-daily}"
SCHEDULE="${SCHEDULE:-0 7 * * *}"
TIME_ZONE="${TIME_ZONE:-Asia/Kolkata}"
MESSAGE_BODY="${MESSAGE_BODY:-{\"kind\":\"weather\",\"min_priority\":\"low\",\"max_farmers\":100}}"

gcloud config set project "${PROJECT_ID}" >/dev/null

SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --format="value(status.url)")

PUSH_ENDPOINT="${SERVICE_URL}/api/v1/alerts/run-daily/pubsub"

if ! gcloud pubsub topics describe "${TOPIC_NAME}" >/dev/null 2>&1; then
  gcloud pubsub topics create "${TOPIC_NAME}"
fi

if gcloud pubsub subscriptions describe "${SUBSCRIPTION_NAME}" >/dev/null 2>&1; then
  gcloud pubsub subscriptions update "${SUBSCRIPTION_NAME}" \
    --push-endpoint="${PUSH_ENDPOINT}"
else
  gcloud pubsub subscriptions create "${SUBSCRIPTION_NAME}" \
    --topic="${TOPIC_NAME}" \
    --push-endpoint="${PUSH_ENDPOINT}"
fi

if gcloud scheduler jobs describe "${SCHEDULER_JOB_NAME}" --location="${REGION}" >/dev/null 2>&1; then
  gcloud scheduler jobs update pubsub "${SCHEDULER_JOB_NAME}" \
    --location="${REGION}" \
    --schedule="${SCHEDULE}" \
    --time-zone="${TIME_ZONE}" \
    --topic="${TOPIC_NAME}" \
    --message-body="${MESSAGE_BODY}"
else
  gcloud scheduler jobs create pubsub "${SCHEDULER_JOB_NAME}" \
    --location="${REGION}" \
    --schedule="${SCHEDULE}" \
    --time-zone="${TIME_ZONE}" \
    --topic="${TOPIC_NAME}" \
    --message-body="${MESSAGE_BODY}"
fi

echo "Scheduler job: ${SCHEDULER_JOB_NAME}"
echo "Topic: ${TOPIC_NAME}"
echo "Push subscription: ${SUBSCRIPTION_NAME}"
echo "Push endpoint: ${PUSH_ENDPOINT}"
echo "Message body: ${MESSAGE_BODY}"
