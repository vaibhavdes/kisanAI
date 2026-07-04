# Cloud Run Deployment

This guide deploys the FastAPI backend to Cloud Run, connects daily alerts through Cloud Scheduler and Pub/Sub, and lists the webhook URLs to configure in Dialogflow CX and Authkey.

Official references:

- Cloud Run source/container deployment: https://cloud.google.com/run/docs/deploying-source-code
- `gcloud run deploy`: https://cloud.google.com/sdk/gcloud/reference/run/deploy
- Cloud Run environment variables: https://cloud.google.com/run/docs/configuring/services/environment-variables
- Cloud Scheduler Pub/Sub jobs: https://cloud.google.com/sdk/gcloud/reference/scheduler/jobs/create/pubsub

## 1. Local Verification

Backend:

```bash
cd kisan-alert-hackathon
DATA_STORE_PROVIDER=local ENABLE_GOOGLE_INTEGRATIONS=false .venv-google/bin/python -m pytest tests
DATA_STORE_PROVIDER=local ENABLE_GOOGLE_INTEGRATIONS=false .venv-google/bin/python -m compileall app scripts smoke_tests tests
DATA_STORE_PROVIDER=local ENABLE_GOOGLE_INTEGRATIONS=false .venv-google/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080
```

Smoke check:

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/admin
curl -X POST http://127.0.0.1:8080/api/v1/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{"from_phone":"+91 99999 88888","text":"Should I irrigate today?","language":"en-IN"}'
```

Frontend:

```bash
cd react_native_chat_app
npm install
npm run typecheck
EXPO_PUBLIC_API_URL=http://127.0.0.1:8080 npm run export:web
EXPO_PUBLIC_API_URL=http://127.0.0.1:8080 npm run web -- --port 8081
```

For Android emulator:

```bash
EXPO_PUBLIC_API_URL=http://10.0.2.2:8080 npm run android
```

## 2. Required Google Setup

Before deploying:

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project kisanai-501120
```

Make sure these resources exist or are ready:

- Firestore database in Native mode.
- Cloud Storage bucket, for example `kisanai-501120-kisan-ai-media`.
- Pub/Sub topic, created by script if missing.
- BigQuery datasets/tables for public data ingestion.
- Earth Engine project registration completed.
- Dialogflow CX agent created.
- Secret Manager secrets for real API keys.

Recommended secret names:

```text
GEMINI_API_KEY
SARVAM_API_KEY
AUTHKEY_API_KEY
MAPS_API_KEY
```

Create or update a secret:

```bash
printf '%s' 'your-secret-value' | gcloud secrets create GEMINI_API_KEY --data-file=-
printf '%s' 'new-secret-value' | gcloud secrets versions add GEMINI_API_KEY --data-file=-
```

## 3. Deploy Cloud Run

From repository root:

```bash
PROJECT_ID=kisanai-501120 \
REGION=asia-south1 \
SERVICE_NAME=kisan-alert-api \
GEMINI_API_KEY_SECRET=GEMINI_API_KEY \
SARVAM_API_KEY_SECRET=SARVAM_API_KEY \
AUTHKEY_API_KEY_SECRET=AUTHKEY_API_KEY \
MAPS_API_KEY_SECRET=MAPS_API_KEY \
scripts/deploy_cloud_run.sh
```

Optional Dialogflow env when the CX agent ID is known:

```bash
DIALOGFLOW_ROUTING_ENABLED=true \
DIALOGFLOW_LOCATION=asia-south1 \
DIALOGFLOW_AGENT_ID=<cx-agent-id> \
scripts/deploy_cloud_run.sh
```

The script deploys the Dockerfile-backed FastAPI service, sets non-secret env vars, attaches Secret Manager values when secret env names are supplied, and prints the Cloud Run URL.

## 4. Configure Scheduler And Pub/Sub

After Cloud Run is deployed:

```bash
PROJECT_ID=kisanai-501120 \
REGION=asia-south1 \
SERVICE_NAME=kisan-alert-api \
PUBSUB_ALERT_TOPIC=kisan-alerts \
SCHEDULE="0 7 * * *" \
TIME_ZONE=Asia/Kolkata \
MESSAGE_BODY='{"crop":"maize","min_priority":"medium","max_farmers":100}' \
scripts/setup_scheduler_pubsub.sh
```

This creates or updates:

- Pub/Sub topic: `kisan-alerts`
- Push subscription: `kisan-alerts-daily-push`
- Scheduler job: `kisan-alerts-daily`
- Push endpoint: `/api/v1/alerts/run-daily/pubsub`

Manual worker test:

```bash
SERVICE_URL=$(gcloud run services describe kisan-alert-api --region asia-south1 --format='value(status.url)')
curl -X POST "${SERVICE_URL}/api/v1/alerts/run-daily" \
  -H "Content-Type: application/json" \
  -d '{"crop":"maize","min_priority":"medium","max_farmers":10}'
```

## 5. Configure Webhooks

Print all URLs:

```bash
PROJECT_ID=kisanai-501120 REGION=asia-south1 SERVICE_NAME=kisan-alert-api scripts/print_webhook_urls.sh
```

Dialogflow CX:

- Fulfillment webhook: `/api/v1/dialogflow/webhook`
- Attach fulfillment tags such as `irrigation_advisory`, `crop_recommendation`, `crop_diagnosis`, `location_update`, `expert_followup`.

Authkey:

- WhatsApp inbound: `/api/v1/whatsapp/webhook`
- WhatsApp delivery receipt: `/api/v1/whatsapp/receipt`
- SMS inbound: `/api/v1/sms/webhook`
- SMS receipt: `/api/v1/sms/receipt`
- Voice-call inbound: `/api/v1/calls/webhook`
- Voice-call receipt: `/api/v1/calls/receipt`

Twilio:

- WhatsApp inbound message URL: `/api/v1/twilio/whatsapp`
- SMS inbound message URL: `/api/v1/twilio/sms`
- Voice call webhook / Gather action URL: `/api/v1/twilio/voice`

The Twilio endpoints accept `application/x-www-form-urlencoded` provider payloads and return TwiML. Text and speech are routed through Dialogflow CX when enabled. WhatsApp location and media payloads are normalized by the backend first because Twilio sends them as `Latitude` / `Longitude` and `MediaUrl0` / `MediaContentType0`.

## 6. Post-Deployment Checks

```bash
SERVICE_URL=$(gcloud run services describe kisan-alert-api --region asia-south1 --format='value(status.url)')
curl "${SERVICE_URL}/health"
curl "${SERVICE_URL}/admin"
curl -X POST "${SERVICE_URL}/api/v1/whatsapp/webhook" \
  -H "Content-Type: application/json" \
  -d '{"from_phone":"+91 99999 88888","text":"Should I irrigate today?","language":"en-IN"}'
```

If `/health` shows Google services as false, check env vars, Secret Manager bindings, API enablement and the Cloud Run service account IAM roles.
