# Project Demo Video Link : https://youtu.be/D204o7oubEM

# Kisan Alert

Kisan Alert is a FastAPI + React Native/Web prototype for Track 4: Smart Water, Crop and Advisory System. It gives small farmers multilingual advisory through web/app, WhatsApp, SMS and outbound voice alerts.

Core features:
- Crop recommendation using farmer location, soil/crop context, rainfall history, groundwater/soil public data where available, and satellite signals.
- Weather, irrigation and dry-spell advisory using live weather, sensor readings and crop stage.
- Crop health logging from photo/voice with expert ticket follow-up.
- Earth Engine satellite farm signal and map preview using Sentinel-2 NDVI, NDWI and NDMI.
- Daily proactive alert runner for weather/crop updates.
- Admin UI for provider switches, farmers, tickets, audits, sensors and test alerts.

## Repository Layout

```text
backend/                FastAPI backend, GCP scripts, data ingestion and tests
react_native_chat_app/  React Native + web WhatsApp-style frontend
README.md               Setup, deployment and operation guide
```

## Google Cloud Resources

| Resource | Why it is used |
| --- | --- |
| Cloud Run | Hosts backend API and frontend web app. |
| Firestore Native | Farmer profile, farm context, tickets, conversations, sensor readings and audit records. |
| BigQuery | Curated public datasets: rainfall history, dry-spell/heavy-rain events, crop production and district context. |
| Cloud Storage | Crop photos, voice replies and Twilio media files. |
| Secret Manager | Runtime credentials and provider tokens. |
| Pub/Sub + Cloud Scheduler | Daily proactive weather/crop alert trigger. |
| Vertex AI / Gemini | Advisory reasoning, intent refinement, crop/photo/soil-card analysis. |
| Earth Engine | Sentinel-2 farm vegetation/moisture signals and map previews. |
| Speech-to-Text / Text-to-Speech | Voice intake and spoken responses. |
| Translation API | Language detection and translation fallback. |
| Dialogflow CX | Optional guided conversation routing for SMS/voice style flows. |
| Google Maps / Geocoding | Location and pincode/village resolution. |
| Twilio | WhatsApp inbound/outbound. |
| Authkey | Outbound voice call alerts, and SMS if enabled. |
| Open-Meteo | Free weather fallback when IMD/weather provider is unavailable. |
| Sarvam | STT/TTS/translation fallback. |

## Prerequisites

Install:

```bash
brew install --cask google-cloud-sdk
brew install node
```

Authenticate:

```bash
gcloud init
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

Create a Python environment:

```bash
cd backend
python3 -m venv ../.venv-google
../.venv-google/bin/pip install -r requirements.txt
cd ..
```

Install frontend packages:

```bash
cd react_native_chat_app
npm install
cd ..
```

## Environment File

Keep real credentials only in `.env`; do not commit it. Use `.env.example` if present, or create:

```bash
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GOOGLE_CLOUD_LOCATION=global
GCP_REGION=asia-south1
VERTEX_AI_LOCATION=global
SPEECH_LOCATION=global
TRANSLATION_LOCATION=global
APP_NAME=Kisan Alert
ENVIRONMENT=production
DATA_STORE_PROVIDER=firestore
ENABLE_GOOGLE_INTEGRATIONS=true
FIRESTORE_DATABASE=(default)
BIGQUERY_PUBLIC_DATASET=kisan_ai_curated
STORAGE_BUCKET=YOUR_PROJECT_ID-kisan-ai-media
PUBSUB_ALERT_TOPIC=kisan-alerts

GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODELS=gemini-2.5-flash
VERTEX_AI_MODEL=gemini-2.5-flash
VERTEX_AI_FALLBACK_MODELS=gemini-2.5-flash
SARVAM_API_KEY=
MAPS_API_KEY=
IMD_API_KEY=
IMD_API_BASE_URL=https://api.data.gov.in/resource/d0419b03-b41b-4226-b48b-0bc92bf139f8
OPEN_METEO_BASE_URL=https://api.open-meteo.com/v1/forecast

TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_CONTENT_SID=
TWILIO_ENABLE_LIVE_SEND=true
TWILIO_VALIDATE_WEBHOOKS=true

AUTHKEY_API_KEY=
AUTHKEY_TEST_COUNTRY_CODE=91
AUTHKEY_SMS_SENDER=
AUTHKEY_SEND_ENABLED=false

DIALOGFLOW_ROUTING_ENABLED=false
DIALOGFLOW_LOCATION=global
DIALOGFLOW_AGENT_ID=
DIALOGFLOW_ENVIRONMENT_ID=
DIALOGFLOW_CONFIDENCE_THRESHOLD=0.45
```

Do not set `GOOGLE_APPLICATION_CREDENTIALS` in Cloud Run. Cloud Run uses the service account from deployment.

Important location rule:
- `GCP_REGION` is the infrastructure region for Cloud Run, Scheduler, Storage and BigQuery.
- `GOOGLE_CLOUD_LOCATION`, `VERTEX_AI_LOCATION`, `SPEECH_LOCATION`, `TRANSLATION_LOCATION` and `DIALOGFLOW_LOCATION` should stay `global` unless you have verified the selected model/API supports another location.
- If Speech shows `Expected resource location to be global` or Vertex says a Gemini model is not found in `asia-south1`, run the Cloud Run env update in "Emergency Runtime Fix" below and redeploy with the corrected script.

## Provision GCP Resources

One-command provisioning:

```bash
PROJECT_ID=YOUR_PROJECT_ID REGION=asia-south1 \
  backend/scripts/provision_gcp_resources.sh
```

This enables APIs, creates the Cloud Run service account, adds IAM roles, creates the storage bucket and Pub/Sub topic, syncs `.env` credentials to Secret Manager, and applies the BigQuery schema.

Firestore Native mode is a one-time project step:

```bash
gcloud firestore databases create --database="(default)" --location=asia-south1
```

If this command says the database already exists, continue.

UI equivalent:
- APIs: Google Cloud Console -> APIs & Services -> Library -> enable the APIs listed in "Google Cloud Resources".
- Firestore: Firestore -> Create database -> Native mode -> region `asia-south1`.
- Storage: Cloud Storage -> Buckets -> Create bucket -> region `asia-south1` -> uniform bucket-level access.
- BigQuery: BigQuery -> create datasets `kisan_ai_raw`, `kisan_ai_curated`, `kisan_ai_ops`.
- Secret Manager: create one secret per key in the credentials section.
- IAM: grant the Cloud Run service account Firestore, BigQuery, Storage, Pub/Sub, Secret Manager, Vertex AI and Dialogflow permissions.

## Secret Manager

Sync local `.env` credentials:

```bash
PROJECT_ID=YOUR_PROJECT_ID ENV_FILE=.env \
  backend/scripts/sync_env_to_secret_manager.sh
```

Synced secrets include:
- `GEMINI_API_KEY`
- `SARVAM_API_KEY`
- `AUTHKEY_API_KEY`
- `AUTHKEY_WHATSAPP_TEMPLATE_ID`
- `AUTHKEY_WHATSAPP_MEDIA_TEMPLATE_ID`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_CONTENT_SID`
- `TWILIO_CONTENT_VARIABLES`
- `TWILIO_MESSAGING_SERVICE_SID`
- `MAPS_API_KEY`
- `IMD_API_KEY`
- `SMS_PROVIDER_API_KEY`
- `WHATSAPP_BUSINESS_TOKEN`
- `VOICE_CALL_PROVIDER_API_KEY`

Cloud Run mounts these with `--set-secrets`; non-secret switches such as provider enable flags remain normal env vars.

## Local Run

Offline/local mode, no live provider calls:

```bash
cd backend
DATA_STORE_PROVIDER=local ENABLE_GOOGLE_INTEGRATIONS=false \
  ../.venv-google/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080
```

Live GCP/provider mode:

```bash
cd backend
DATA_STORE_PROVIDER=firestore ENABLE_GOOGLE_INTEGRATIONS=true \
  ../.venv-google/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080
```

Frontend web:

```bash
cd react_native_chat_app
EXPO_PUBLIC_API_URL=http://127.0.0.1:8080 npm run web
```

Android:

```bash
cd react_native_chat_app
EXPO_PUBLIC_API_URL=http://10.0.2.2:8080 npx expo run:android
```

## Deploy Backend

```bash
PROJECT_ID=YOUR_PROJECT_ID REGION=asia-south1 ENV_FILE=.env \
  backend/scripts/deploy_cloud_run.sh
```

The script:
- Deploys `kisan-alert-api` to Cloud Run.
- Uses Firestore and Google integrations.
- Mounts configured credentials from Secret Manager.
- Sets `TWILIO_PUBLIC_BASE_URL` to the Cloud Run URL if not provided.

Important output:
- Backend health: `https://BACKEND_URL/health`
- Admin UI: `https://BACKEND_URL/admin`
- Twilio WhatsApp webhook: `https://BACKEND_URL/api/v1/twilio/whatsapp`
- Twilio status callback: `https://BACKEND_URL/api/v1/twilio/status`
- Dialogflow webhook: `https://BACKEND_URL/api/v1/dialogflow/webhook`

Emergency Runtime Fix:

If an older deploy accidentally set AI locations to the Cloud Run region, fix the live service immediately:

```bash
gcloud run services update kisan-alert-api \
  --region asia-south1 \
  --update-env-vars GOOGLE_CLOUD_LOCATION=global,VERTEX_AI_LOCATION=global,SPEECH_LOCATION=global,TRANSLATION_LOCATION=global,GCP_REGION=asia-south1,DIALOGFLOW_LOCATION=global,VERTEX_AI_MODEL=gemini-2.5-flash,VERTEX_AI_FALLBACK_MODELS=gemini-2.5-flash,GEMINI_MODEL=gemini-2.5-flash,GEMINI_FALLBACK_MODELS=gemini-2.5-flash
```

If STT fails with `speech.recognizers.recognize denied`, grant the Cloud Run service account Speech Client:

```bash
SERVICE_ACCOUNT_EMAIL=kisan-alert-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/speech.client"
```

## Deploy Frontend Web

```bash
cd react_native_chat_app
PROJECT_ID=YOUR_PROJECT_ID REGION=asia-south1 BACKEND_SERVICE_NAME=kisan-alert-api \
  scripts/deploy_cloud_run_web.sh
```

The script deploys `kisan-alert-web` and injects the backend Cloud Run URL into `EXPO_PUBLIC_API_URL`.

## Scheduler and Alerts

Create/update the daily alert schedule:

```bash
PROJECT_ID=YOUR_PROJECT_ID REGION=asia-south1 SERVICE_NAME=kisan-alert-api \
  SCHEDULE="0 7 * * *" TIME_ZONE="Asia/Kolkata" \
  backend/scripts/setup_scheduler_pubsub.sh
```

Default message body:

```json
{"kind":"weather","min_priority":"low","max_farmers":100}
```

Alerts use:
- WhatsApp through Twilio when the session/template allows it.
- Voice through Authkey for scheduled daily alert calls.
- SMS only when enabled and templates/sender are configured.

## Dialogflow CX Setup

CLI:

```bash
gcloud alpha dialogflow cx agents list --location=global --project=YOUR_PROJECT_ID
gcloud alpha dialogflow cx environments list \
  --location=global \
  --agent=AGENT_UUID \
  --project=YOUR_PROJECT_ID
```

Set:

```bash
DIALOGFLOW_ROUTING_ENABLED=true
DIALOGFLOW_LOCATION=global
DIALOGFLOW_AGENT_ID=AGENT_UUID
DIALOGFLOW_ENVIRONMENT_ID=
```

UI:
- Dialogflow CX Console -> select project -> create/open agent.
- Copy the agent UUID from the URL or agent details.
- Fulfillment/Webhook URL after backend deploy: `https://BACKEND_URL/api/v1/dialogflow/webhook`.
- Keep `DIALOGFLOW_ENVIRONMENT_ID` empty unless you publish an environment.

## Twilio WhatsApp Setup

UI:
- Twilio Console -> Messaging -> WhatsApp Sandbox or WhatsApp Sender.
- Set inbound webhook to `https://BACKEND_URL/api/v1/twilio/whatsapp`.
- Set status callback to `https://BACKEND_URL/api/v1/twilio/status`.
- For outbound proactive messages outside the 24-hour window, create an approved Content Template and set `TWILIO_CONTENT_SID`.

## Twilio Voice Number Setup

Use this when judges call the Twilio test number.

UI:
- Twilio Console -> Phone Numbers -> Manage -> Active numbers -> select `+1 775 269 8657`.
- Voice configuration:
  - A call comes in: `Webhook`
  - Method: `POST`
  - URL: `https://BACKEND_URL/api/v1/twilio/voice`
- Messaging configuration:
  - A message comes in: `Webhook`
  - Method: `POST`
  - URL: `https://BACKEND_URL/api/v1/twilio/sms`
- Save.

The web/app "Voice call" button opens `tel:+17752698657`. Twilio then posts call speech/DTMF to `/api/v1/twilio/voice`, and Kisan Alert returns TwiML with `<Gather>` for continued speech input.

CLI smoke check:

```bash
cd backend
ENABLE_GOOGLE_INTEGRATIONS=true ../.venv-google/bin/python smoke_tests/test_twilio_whatsapp.py
```

## Authkey Voice/SMS Setup

Set:

```bash
AUTHKEY_API_KEY=
AUTHKEY_TEST_COUNTRY_CODE=91
AUTHKEY_SMS_SENDER=
AUTHKEY_SEND_ENABLED=false
```

Voice alert testing is available from the admin UI. SMS requires sender/template approval, so keep SMS disabled until approved.

## Public Data and BigQuery Ingestion

Normalized files included:

```text
backend/data/normalized/subdivision_rainfall_history/imd_subdivision_2017.csv
backend/data/normalized/maharashtra_dryspell_events/maharain_dryspell.csv
backend/data/normalized/maharashtra_heavy_rainfall_events/maharain_heavy_rainfall.csv
backend/data/normalized/crop_production_history/all_india_crop_wise.csv
backend/data/normalized/crop_production_history/all_india_year_wise.csv
backend/data/normalized/crop_production_history/all_states_rice_estimate.csv
backend/data/normalized/crop_production_history/des_district_2024_25_all_visible_rows.csv
backend/data/normalized/crop_production_history/maharashtra_des_district_2024_25.csv
backend/data/normalized/crop_production_history/maharashtra_rice_estimate.csv
backend/data/normalized/aspirational_districts/aspirational_districts.csv
```

Load datasets:

```bash
cd backend

../.venv-google/bin/python scripts/ingest_public_data.py subdivision_rainfall_history \
  data/normalized/subdivision_rainfall_history/imd_subdivision_2017.csv \
  --source-name "IMD subdivision rainfall history" \
  --source-url "https://api.data.gov.in/resource/d0419b03-b41b-4226-b48b-0bc92bf139f8"

../.venv-google/bin/python scripts/ingest_public_data.py maharashtra_dryspell_events \
  data/normalized/maharashtra_dryspell_events/maharain_dryspell.csv \
  --source-name "Maharain tehsil dryspell events" \
  --source-url "https://maharain.maharashtra.gov.in"

../.venv-google/bin/python scripts/ingest_public_data.py maharashtra_heavy_rainfall_events \
  data/normalized/maharashtra_heavy_rainfall_events/maharain_heavy_rainfall.csv \
  --source-name "Maharain tehsil heavy rainfall events" \
  --source-url "https://maharain.maharashtra.gov.in"

for file in \
  data/normalized/crop_production_history/all_india_crop_wise.csv \
  data/normalized/crop_production_history/all_india_year_wise.csv \
  data/normalized/crop_production_history/all_states_rice_estimate.csv \
  data/normalized/crop_production_history/des_district_2024_25_all_visible_rows.csv \
  data/normalized/crop_production_history/maharashtra_des_district_2024_25.csv \
  data/normalized/crop_production_history/maharashtra_rice_estimate.csv; do
  ../.venv-google/bin/python scripts/ingest_public_data.py crop_production_history "$file" \
    --source-name "Crop production history"
done

../.venv-google/bin/python scripts/ingest_public_data.py aspirational_districts \
  data/normalized/aspirational_districts/aspirational_districts.csv \
  --source-name "Aspirational districts"
```

The advisory engine reads BigQuery through `/api/v1/data/context` and recommendation/advisory flows.

## Tests and Smoke Checks

Backend unit/integration tests:

```bash
cd backend
DATA_STORE_PROVIDER=local ENABLE_GOOGLE_INTEGRATIONS=false \
  ../.venv-google/bin/python -m pytest tests
```

Frontend typecheck:

```bash
cd react_native_chat_app
npm run typecheck
```

Live provider smoke tests:

```bash
cd backend
ENABLE_GOOGLE_INTEGRATIONS=true ../.venv-google/bin/python smoke_tests/test_gemini.py
ENABLE_GOOGLE_INTEGRATIONS=true ../.venv-google/bin/python smoke_tests/test_vertex_ai.py
ENABLE_GOOGLE_INTEGRATIONS=true ../.venv-google/bin/python smoke_tests/test_bigquery.py
ENABLE_GOOGLE_INTEGRATIONS=true ../.venv-google/bin/python smoke_tests/test_secret_manager.py
ENABLE_GOOGLE_INTEGRATIONS=true ../.venv-google/bin/python smoke_tests/test_earth_engine.py
```

## API Quick Reference

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Service readiness. |
| `GET /admin` | Passwordless demo/admin console. |
| `POST /api/v1/chat/message` | App/web conversation. |
| `POST /api/v1/twilio/whatsapp` | Twilio WhatsApp webhook. |
| `POST /api/v1/sensors/readings` | Generic IoT/manual sensor reading. |
| `POST /api/v1/satellite/farm-signal` | Earth Engine NDVI/NDWI/NDMI/EVI/NDRE signal. |
| `POST /api/v1/satellite/farm-map` | Earth Engine map thumbnail URL. |
| `POST /api/v1/alerts/run-daily` | Run proactive alerts manually. |
| `POST /api/v1/alerts/run-daily/pubsub` | Pub/Sub Scheduler target. |
| `POST /api/v1/dialogflow/webhook` | Dialogflow fulfillment webhook. |

## Release Checklist

1. `.env` exists locally and is not committed.
2. `backend/scripts/provision_gcp_resources.sh` completed.
3. Firestore Native database exists.
4. `backend/scripts/sync_env_to_secret_manager.sh` completed.
5. Backend Cloud Run deploy completed.
6. Frontend Cloud Run deploy completed.
7. Scheduler script completed.
8. Twilio and Dialogflow webhook URLs updated to backend Cloud Run URL.
9. BigQuery data ingestion completed.
10. `/health`, `/admin`, web chat and WhatsApp test message verified.

## Notes

- Intent detection uses local safety rules plus AI refinement when enabled, so it is not limited to exact keywords.
- Sensor integration is vendor-neutral. Any IoT source can post normalized moisture/weather readings to `/api/v1/sensors/readings`.
- Earth Engine thumbnail URLs are generated by Google Earth Engine; the backend sends the URL through WhatsApp/app as media.
- Keep `backend.zip`, `Archive.zip`, `.env`, virtualenvs and local secret files out of commits.
