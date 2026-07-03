# Google Smoke Test Results

Date: 2026-07-03

Project used for checks: `kisanai-501120`

## Summary

| Service | Result | Meaning |
|---|---|---|
| Gemini API | Passed | API key works with `gemini-2.5-flash` |
| FastAPI backend | Passed | App imports, runs, `/health` works |
| `/advisory/test` | Passed | Endpoint returns Gemini advisory JSON with `source: gemini` |
| Pytest suite | Passed | `3 passed` |
| Firestore | Passed | Named database `kisanai` connected |
| Cloud Storage | Passed | Bucket `kisanai-501120-kisan-ai-media` exists |
| BigQuery | Passed | BigQuery connected; no datasets yet |
| Pub/Sub | Passed | Topic `projects/kisanai-501120/topics/kisan-alerts` exists |
| Speech-to-Text | Passed | API responded with demo silent audio |
| Text-to-Speech | Passed | API generated demo audio bytes |
| Translation API | Passed | API translated Marathi text to English |
| Secret Manager | Passed | Secret Manager connected; 2 secrets visible |
| Dialogflow CX | Passed | API connected; no agents created yet |
| Earth Engine | Passed | Earth Engine initialized and computed demo geometry area |
| Maps Geocoding | Passed | API key works for Geocoding API |
| Open-Meteo Weather | Passed | Fallback weather provider returned live forecast context |
| Authkey Balance | Passed | Authkey balance API responded |
| Authkey Channels | Passed | SMS, voice, voice fallback, WhatsApp template/media/bulk scenarios build in dry-run |

Local machine note:

- ADC now works.
- No service account JSON is tracked in the repo.
- Local `.env` uses `FIRESTORE_DATABASE=kisanai` because the project was created with a named Firestore database instead of `(default)`.

## Passed: Gemini

Command:

```bash
GEMINI_API_KEY="<local-key>" GEMINI_MODEL=gemini-2.5-flash \
  .venv-google/bin/python smoke_tests/test_gemini.py
```

Result:

```text
OK: Gemini responded using gemini-2.5-flash
```

## Passed: FastAPI

Commands:

```bash
.venv-google/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080
curl http://127.0.0.1:8080/health
curl -X POST http://127.0.0.1:8080/advisory/test \
  -H "Content-Type: application/json" \
  -d '{"crop":"cotton","rainfall_forecast_mm":55}'
```

Result:

- `/health` returned `status: true`.
- `/advisory/test` returned `source: gemini` and Marathi advisory JSON.

## Passed: Firestore

Command:

```bash
.venv-google/bin/python smoke_tests/test_firestore.py
```

Result:

```text
OK: Firestore database kisanai connected. Collection count visible to credentials: 0
```

Local `.env` value:

```env
FIRESTORE_DATABASE=kisanai
```

## Passed: Google Service APIs

The following APIs are enabled and their smoke tests passed:

- Speech-to-Text
- Text-to-Speech
- Translation
- Dialogflow CX
- Maps Geocoding

Commands:

```bash
.venv-google/bin/python smoke_tests/test_speech_to_text.py
.venv-google/bin/python smoke_tests/test_text_to_speech.py
.venv-google/bin/python smoke_tests/test_translation.py
.venv-google/bin/python smoke_tests/test_dialogflow.py
.venv-google/bin/python smoke_tests/test_maps_geocoding.py
```

## Old Common Failure: ADC Missing

Affected services:

- Firestore
- Cloud Storage
- BigQuery
- Pub/Sub
- Speech-to-Text
- Text-to-Speech
- Translation
- Secret Manager
- Dialogflow CX

If seen again, the error is:

```text
google.auth.exceptions.DefaultCredentialsError:
Your default credentials were not found.
```

Fix option A, recommended for local development:

```bash
brew install --cask google-cloud-sdk
gcloud init
gcloud config set project kisanai-501120
gcloud auth application-default login
```

Then rerun:

```bash
GOOGLE_CLOUD_PROJECT=kisanai-501120 .venv-google/bin/python smoke_tests/test_firestore.py
```

Fix option B, service account JSON:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/secure/local/path/kisan-ai-backend.json
```

Do not commit the JSON file.

## Passed: Earth Engine

Command:

```bash
.venv-google/bin/python smoke_tests/test_earth_engine.py
```

Result:

```text
OK: Earth Engine initialized. Demo buffer area: 776015 sq m
```

## Old Earth Engine Failure

Observed error:

```text
Project kisanai-501120 is not registered to use Earth Engine.
Visit https://console.cloud.google.com/earth-engine/configuration?project=kisanai-501120
```

Fix:

```bash
.venv-google/bin/earthengine authenticate
.venv-google/bin/earthengine set_project kisanai-501120
.venv-google/bin/python smoke_tests/test_earth_engine.py
```

If the same registration error remains, complete project registration at:

```text
Google Cloud Console -> Earth Engine -> Configuration
```

Earth Engine is enabled as an API, but it has a separate project registration/access step.

## Passed: Authkey

Balance command:

```bash
.venv-google/bin/python smoke_tests/test_authkey_balance.py
```

Channel scenario command:

```bash
.venv-google/bin/python smoke_tests/test_authkey_channels.py
```

Result:

```text
OK: Authkey balance API responded
OK: Authkey dry-run build scenarios covered: send_sms, send_voice, send_parallel_sms_voice, send_voice_with_sms_fallback, send_whatsapp_template_get, send_whatsapp_template_json, send_whatsapp_media_template_get, send_whatsapp_bulk_template_json
```

`AUTHKEY_SEND_ENABLED=false` is the default to prevent accidental SMS, WhatsApp, or voice calls.

## Passed: Maps Geocoding

Local `.env` must include:

```env
MAPS_API_KEY=your-local-maps-key
```

Result:

```text
OK: Google Maps Geocoding responded
```

## Current Verification Commands

Run:

```bash
.venv-google/bin/python smoke_tests/test_gemini.py
.venv-google/bin/python smoke_tests/test_firestore.py
.venv-google/bin/python smoke_tests/test_storage.py
.venv-google/bin/python smoke_tests/test_bigquery.py
.venv-google/bin/python smoke_tests/test_pubsub.py
.venv-google/bin/python smoke_tests/test_speech_to_text.py
.venv-google/bin/python smoke_tests/test_text_to_speech.py
.venv-google/bin/python smoke_tests/test_translation.py
.venv-google/bin/python smoke_tests/test_secret_manager.py
.venv-google/bin/python smoke_tests/test_dialogflow.py
.venv-google/bin/python smoke_tests/test_earth_engine.py
.venv-google/bin/python smoke_tests/test_maps_geocoding.py
.venv-google/bin/python smoke_tests/test_open_meteo.py
.venv-google/bin/python smoke_tests/test_authkey_balance.py
.venv-google/bin/python smoke_tests/test_authkey_channels.py
```

## Required Before Next Development Step

1. Install Google Cloud CLI locally.
2. Run `gcloud auth application-default login`.
3. Create/confirm Firestore database `kisanai`.
4. Create/confirm bucket `kisanai-501120-kisan-ai-media`.
5. Create Pub/Sub topic `kisan-alerts`.
6. Add local `.env` values:

```env
GOOGLE_CLOUD_PROJECT=kisanai-501120
GOOGLE_CLOUD_LOCATION=global
GCP_REGION=asia-south1
FIRESTORE_DATABASE=kisanai
GEMINI_API_KEY=your-rotated-local-key
GEMINI_MODEL=gemini-2.5-flash
STORAGE_BUCKET=kisanai-501120-kisan-ai-media
PUBSUB_ALERT_TOPIC=kisan-alerts
MAPS_API_KEY=your-local-maps-key
```

7. Rerun each smoke test individually.
