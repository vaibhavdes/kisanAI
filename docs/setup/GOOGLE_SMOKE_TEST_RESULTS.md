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
| Firestore | Blocked | Local Application Default Credentials missing |
| Cloud Storage | Blocked | Local Application Default Credentials missing |
| BigQuery | Blocked | Local Application Default Credentials missing |
| Pub/Sub | Blocked | Local Application Default Credentials missing |
| Speech-to-Text | Blocked | Local Application Default Credentials missing |
| Text-to-Speech | Blocked | Local Application Default Credentials missing |
| Translation API | Blocked | Local Application Default Credentials missing |
| Secret Manager | Blocked | Local Application Default Credentials missing |
| Dialogflow CX | Blocked | Local Application Default Credentials missing |
| Earth Engine | Blocked | Earth Engine account/auth not initialized |
| Maps Geocoding | Blocked | `MAPS_API_KEY` missing in local `.env` |

Local machine note:

- `gcloud` is not installed, so ADC cannot be created from this terminal yet.
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

## Common Failure: ADC Missing

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

Observed error:

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
