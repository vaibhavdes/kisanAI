# Kisan Alert Hackathon Prototype

Track 4: Smart Water, Crop and Advisory System.

This is a standalone FastAPI prototype for the competition track. It intentionally contains only the pieces required for the Kisan Alert problem statement and avoids product-specific or proprietary application code from any existing system. It shows one complete end-to-end flow:

1. Register a farmer and farm context.
2. Recommend crops using soil, rainfall, groundwater, NDVI and water availability.
3. Generate dry-spell irrigation/fertilizer alerts from weather and sensor readings.
4. Log crop health through text, voice transcript or photo metadata.
5. Create a Rythu Seva Kendra follow-up ticket.
6. Support WhatsApp Business, voice-call and SMS style intake for low-connectivity farmers.

The code runs locally without Google credentials. Google Cloud services and communication providers are isolated behind adapters so the team can replace demo logic with real integrations quickly.

## Stack

- Python 3.11+
- FastAPI
- Pydantic
- Uvicorn
- Optional Google Cloud adapters:
  - Gemini API or Vertex AI for advisory and crop photo diagnosis
  - Earth Engine for NDVI and satellite signals
  - Cloud Speech-to-Text and Text-to-Speech for voice
  - Translation API for Indic language localization
  - Cloud Run for deployment
  - BigQuery for public datasets and analytics
- WhatsApp Business API, SMS gateway, or voice-call IVR provider for farmer channels

## Project Structure

```text
app/
  api/v1/endpoints/      HTTP endpoints by feature
  core/                  settings and app configuration
  models/                request/response schemas and crop domain data
  repositories/          persistence boundary; in-memory for demo
  services/              business logic and external integration adapters
  utils/                 language helpers
tests/                   FastAPI flow tests
```

## Run Locally

```bash
cd kisan-alert-hackathon
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8080
```

Open:

- API docs: http://127.0.0.1:8080/docs
- Health: http://127.0.0.1:8080/health
- API channels:
  - `/api/v1/sms/webhook`
  - `/api/v1/whatsapp/webhook`
  - `/api/v1/calls/webhook`
  - `/api/v1/advisories/crop-stage`
  - `/api/v1/soil-cards/extract`
  - `/api/v1/data/sources`
  - `/api/v1/conversations/log`

## Demo API Flow

Create a farmer:

```bash
curl -X POST http://127.0.0.1:8080/api/v1/farmers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ravi",
    "phone": "9999999999",
    "language": "te-IN",
    "village": "Demo Village",
    "district": "Guntur",
    "state": "Andhra Pradesh",
    "farm": {
      "area_acres": 2.5,
      "soil_type": "black",
      "soil_ph": 6.8,
      "groundwater_depth_m": 18,
      "latitude": 16.3,
      "longitude": 80.4
    }
  }'
```

Get crop recommendations:

```bash
curl -X POST http://127.0.0.1:8080/api/v1/recommendations/crop \
  -H "Content-Type: application/json" \
  -d '{
    "farmer_id": "replace-with-created-id",
    "season": "kharif",
    "expected_rainfall_mm": 620,
    "ndvi": 0.42,
    "water_availability": "medium"
  }'
```

Generate a dry-spell advisory:

```bash
curl -X POST http://127.0.0.1:8080/api/v1/advisories/dry-spell \
  -H "Content-Type: application/json" \
  -d '{
    "farmer_id": "replace-with-created-id",
    "crop": "maize",
    "soil_moisture": 0.18,
    "rainfall_forecast_mm": [0, 0, 0, 1, 0, 0, 3],
    "temperature_c": 36
  }'
```

Log crop health and create expert follow-up:

```bash
curl -X POST http://127.0.0.1:8080/api/v1/diagnosis/log \
  -H "Content-Type: application/json" \
  -d '{
    "farmer_id": "replace-with-created-id",
    "crop": "chilli",
    "symptoms_text": "Leaves curling and white insects visible",
    "photo_uri": "gs://demo/chilli-leaf.jpg"
  }'
```

Simulate a WhatsApp message:

```bash
curl -X POST http://127.0.0.1:8080/api/v1/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "from_phone": "9999999999",
    "text": "my chilli leaves are curling",
    "language": "hi-IN"
  }'
```

Simulate a voice-call IVR callback:

```bash
curl -X POST http://127.0.0.1:8080/api/v1/calls/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "from_phone": "9999999999",
    "call_id": "demo-call-1",
    "dtmf_digit": "1",
    "language": "te-IN"
  }'
```

## Google Cloud Integration Plan

Use the existing service classes as stable boundaries:

- `GeminiService`: switch `diagnose_crop_health` and language response generation to Gemini or Vertex AI.
- `EarthEngineService`: replace demo NDVI payload with Earth Engine polygon/time-series fetch.
- `VoiceService`: replace simulated transcript/audio with Cloud Speech-to-Text and Text-to-Speech.
- `SmsService`: plug Twilio, Gupshup, or a basic SMS gateway webhook.
- `WhatsAppService`: plug WhatsApp Business Cloud API webhook verification, templates and media fetch.
- `CallService`: plug Exotel, Twilio Voice, Knowlarity or another IVR/call provider callback.
- `WeatherService`: plug IMD/Open-Meteo/Google weather partner feed and ground sensor ingestion.
- `GovernmentDataService`: plug data.gov.in, IMD, India-WRIS, Soil Health Card and Agmarknet ingestion.
- `CropStageAdvisoryService`: add crop-stage rules and Gemini synthesis for sowing through harvest.
- `SoilCardVisionService`: replace text-parser fallback with Gemini/Vertex AI Vision soil-card extraction.
- `ConversationStore`: replace in-memory storage with Firestore/Cloud SQL and BigQuery export.
- `AlertPriorityPolicy`: central policy for WhatsApp/SMS/voice-call escalation.

For the competition, this structure gives a working demo now and a clear route to use Google Cloud technologies in the final build.

## Provider Onboarding Docs

- [Google setup verification](docs/setup/GOOGLE_SETUP_VERIFICATION.md)
- [Google smoke test results](docs/setup/GOOGLE_SMOKE_TEST_RESULTS.md)
- [Service fallback plan](docs/setup/SERVICE_FALLBACKS.md)
- [Channel provider roadmap](docs/providers/README.md)
- [Authkey SMS and WhatsApp](docs/providers/AUTHKEY_SMS_AND_WHATSAPP.md)
- [WhatsApp Business Cloud API](docs/providers/WHATSAPP_BUSINESS_CLOUD_API.md)
- [Vomyra Voice AI](docs/providers/VOMYRA_VOICE_AI.md)
- [Google Dialogflow](docs/providers/GOOGLE_DIALOGFLOW.md)

## IP Boundary

This repository is a clean hackathon scaffold. It does not import or copy private business logic, database schemas, app screens, assets, translations, or release code from existing products. The overlap is limited to the public competition domain: crop recommendation, dry-spell advisory, crop health logging, expert follow-up and low-connectivity farmer channels.

The frontend can be added later as a WhatsApp-like chat UI, but the backend does not assume any specific frontend framework.
