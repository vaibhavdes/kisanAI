# Google Setup Verification

This document maps the Google setup plan to the current FastAPI project and gives the team a safe order to verify services.

## Security First

Do not commit API keys, service account JSON, or provider tokens.

Use local `.env` only:

```env
GOOGLE_CLOUD_PROJECT=kisanai-501120
GOOGLE_CLOUD_LOCATION=global
GCP_REGION=asia-south1
FIRESTORE_DATABASE=kisanai
GEMINI_API_KEY=replace-with-rotated-local-key
GEMINI_MODEL=gemini-2.5-flash
STORAGE_BUCKET=kisanai-501120-kisan-ai-media
PUBSUB_ALERT_TOPIC=kisan-alerts
MAPS_API_KEY=replace-local-only
```

If a real key was placed in `Details.txt` or `.env.example`, rotate it in Google AI Studio and keep the new value only in `.env`.

## What Is Already Aligned

| Plan item | Current project status |
|---|---|
| FastAPI project | Done |
| `requirements.txt` | Added |
| Gemini SDK | Added via `google-genai` |
| `test_gemini.py` | Added under `smoke_tests/` |
| First endpoint | Added: `POST /advisory/test` and `POST /api/v1/advisory/test` |
| Firestore interface | Smoke test added for named database `kisanai`; runtime repository uses Firestore by default |
| Cloud Storage interface | Smoke test added |
| Speech-to-Text interface | Smoke test added |
| Text-to-Speech interface | Smoke test added |
| Translation interface | Smoke test added |
| BigQuery interface | Smoke test added |
| Pub/Sub interface | Smoke test added |
| Secret Manager interface | Smoke test added |
| Dialogflow interface | Smoke test added |
| Earth Engine interface | Smoke test added |
| Maps Geocoding interface | Smoke test added |

## Local Setup

Use Python 3.11+.

```bash
cd kisan-alert-hackathon
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Google SDKs are part of `requirements.txt` because this project is evaluated on Google Cloud usage.

## Run Backend First

```bash
uvicorn app.main:app --reload --port 8080
```

Check:

```bash
curl http://127.0.0.1:8080/health
```

## Test Gemini First

```bash
python smoke_tests/test_gemini.py
```

Expected:

- Marathi advisory prints.
- Final line says Gemini responded.

## Test First FastAPI Gemini Endpoint

```bash
curl -X POST http://127.0.0.1:8080/advisory/test \
  -H "Content-Type: application/json" \
  -d '{
    "farmer_name": "Vaibhav",
    "language": "mr-IN",
    "crop": "cotton",
    "crop_stage": "vegetative",
    "location": "Jalgaon",
    "weather_summary": "Heavy rain likely tomorrow",
    "rainfall_forecast_mm": 55
  }'
```

Expected:

- `source` is `gemini` when `GEMINI_API_KEY` is valid.
- `source` is fallback when key/package/API fails.
- Response includes `advisory_text`, `risk_level`, `recommended_actions`.

## Smoke Test Order

Run in this order:

```bash
python smoke_tests/test_gemini.py
python smoke_tests/test_firestore.py
python smoke_tests/test_storage.py
python smoke_tests/test_speech_to_text.py
python smoke_tests/test_text_to_speech.py
python smoke_tests/test_translation.py
python smoke_tests/test_bigquery.py
python smoke_tests/test_bigquery_public_context.py
python smoke_tests/test_pubsub.py
python smoke_tests/test_secret_manager.py
python smoke_tests/test_dialogflow.py
python smoke_tests/test_earth_engine.py
python smoke_tests/test_maps_geocoding.py
python smoke_tests/test_open_meteo.py
python smoke_tests/test_authkey_balance.py
python smoke_tests/test_authkey_channels.py
```

Run each smoke test individually. Do not run everything blindly; each service needs its own API, auth, and sometimes a resource such as a bucket or topic.

Authkey channel tests are dry-run by default unless `AUTHKEY_SEND_ENABLED=true`.

Latest smoke-test result notes are tracked in:

- [Google smoke test results](GOOGLE_SMOKE_TEST_RESULTS.md)

## Development Order

Build feature-by-feature:

1. `/advisory/test`
   - Gemini advisory with farmer/weather data.
2. `/api/v1/farmers`
   - Firestore repository and progressive identity are added.
3. `/advisory/active-crop`
   - Read farmer, weather context, Gemini advisory, save advisory.
4. `/vision/crop-health`
   - Upload crop image, Gemini multimodal diagnosis, expert ticket.
5. `/vision/soil-card`
   - Upload soil card, extract pH/NPK/organic carbon.
6. `/api/v1/recommendations/crop`
   - Connect BigQuery and Earth Engine.
7. `/voice/transcribe`
   - Audio to text.
8. `/voice/speak`
   - Text to audio.
9. `/alerts/run-daily`
   - Check farmers, detect risk, create alert jobs.
10. `/dialogflow/webhook`
   - Dialogflow CX to FastAPI to Gemini response.

## Team Split

- Member 1: Gemini + advisory endpoints.
- Member 2: Firestore + Storage + media upload.
- Member 3: Voice/Translation/Dialogflow channels.
- Shared: BigQuery/Earth Engine public-data integrations.
