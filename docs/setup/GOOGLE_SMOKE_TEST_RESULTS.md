# Google Smoke Test Results

Date: 2026-07-02

Project used for checks: `kisanai-501120`

## Summary

| Service | Result | Meaning |
|---|---|---|
| Gemini API | Passed | API key works with `gemini-2.5-flash` |
| FastAPI backend | Passed | App imports, runs, `/health` works |
| `/advisory/test` | Passed | Endpoint returns Gemini advisory JSON with `source: gemini` |
| Pytest suite | Passed | `3 passed` |
| Firestore | Blocked | ADC works, but Firestore database is not created |
| Cloud Storage | Passed | Bucket `kisanai-501120-kisan-ai-media` exists |
| BigQuery | Passed | BigQuery connected; no datasets yet |
| Pub/Sub | Passed | Topic `projects/kisanai-501120/topics/kisan-alerts` exists |
| Speech-to-Text | Blocked | `speech.googleapis.com` is disabled |
| Text-to-Speech | Blocked | `texttospeech.googleapis.com` is disabled |
| Translation API | Blocked | `translate.googleapis.com` is disabled |
| Secret Manager | Passed | Secret Manager connected; 2 secrets visible |
| Dialogflow CX | Blocked | `dialogflow.googleapis.com` is disabled |
| Earth Engine | Blocked | `earthengine.googleapis.com` is disabled |
| Maps Geocoding | Blocked | `MAPS_API_KEY` missing in local `.env` |

Local machine note:

- ADC now works.
- No service account JSON was found in the repo.

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

## Firestore Failure

Observed error:

```text
The database (default) does not exist for project kisanai-501120
```

Fix:

```bash
gcloud firestore databases create --database="(default)" --location=asia-south1
```

Or use Console:

```text
Google Cloud Console -> Firestore -> Create database -> Native mode
```

## Disabled API Failures

Affected services:

- Speech-to-Text
- Text-to-Speech
- Translation
- Dialogflow CX
- Earth Engine

Fix:

```bash
gcloud services enable \
  speech.googleapis.com \
  texttospeech.googleapis.com \
  translate.googleapis.com \
  dialogflow.googleapis.com \
  earthengine.googleapis.com \
  --project kisanai-501120
```

Wait a few minutes and rerun the corresponding smoke tests.

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

## Earth Engine Failure

Observed error:

```text
Please authorize access to your Earth Engine account by running earthengine authenticate
```

Fix:

```bash
.venv-google/bin/earthengine authenticate
.venv-google/bin/earthengine set_project kisanai-501120
.venv-google/bin/python smoke_tests/test_earth_engine.py
```

If project access is not approved in Earth Engine yet, complete Earth Engine signup/project registration first.

## Maps Geocoding Failure

Observed error:

```text
RuntimeError: MAPS_API_KEY missing. Add it to local .env, not .env.example.
```

Fix:

```env
MAPS_API_KEY=your-local-maps-key
```

Then:

```bash
.venv-google/bin/python smoke_tests/test_maps_geocoding.py
```

## Required Before Next Development Step

1. Install Google Cloud CLI locally.
2. Run `gcloud auth application-default login`.
3. Create/confirm Firestore database.
4. Create/confirm bucket `kisanai-501120-kisan-ai-media`.
5. Create Pub/Sub topic `kisan-alerts`.
6. Add local `.env` values:

```env
GOOGLE_CLOUD_PROJECT=kisanai-501120
GOOGLE_CLOUD_LOCATION=global
GCP_REGION=asia-south1
GEMINI_API_KEY=your-rotated-local-key
GEMINI_MODEL=gemini-2.5-flash
STORAGE_BUCKET=kisanai-501120-kisan-ai-media
PUBSUB_ALERT_TOPIC=kisan-alerts
MAPS_API_KEY=your-local-maps-key
```

7. Rerun each smoke test individually.
