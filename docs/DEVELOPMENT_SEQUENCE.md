# Backend Development Sequence

The backend should become complete before frontend polish. Every step must keep API tests passing and expose a simple endpoint that teammates can verify from Swagger or curl.

## 1. Provider Registry

Status: implemented.

Endpoint:

```text
GET /api/v1/providers/config
PATCH /api/v1/providers/config
```

Purpose:

- Admin/frontend can choose primary and secondary provider per feature.
- Defaults prefer Google/government providers.
- Satellite has no manual fallback because original data is required.

## 2. Firestore Persistence

Replace local store with repository interfaces:

- Farmers
- Farms
- Conversations
- Advisories
- Alerts
- Expert tickets
- Provider config

Keep BigQuery for analytics/public data, not transactional farmer records.

## 3. Weather Provider

Implement weather context service:

- Primary: IMD API/agromet where available.
- Secondary: Open-Meteo.
- Output one normalized forecast shape used by advisory logic.

Fields needed:

- Current temperature, humidity, wind speed.
- Daily rainfall forecast.
- Thunderstorm/heavy rain alert.
- ET0 if available.
- Soil moisture/soil temperature if available.
- Source and fallback status.

## 4. BigQuery Public Data

Provision raw/curated/ops datasets and load first sample files:

- Rainfall daily/history.
- Groundwater depth.
- Soil health.
- Crop production/yield.
- IMD agromet advisories.

Expose:

```text
POST /api/v1/data/context
```

using real BigQuery context instead of static text.

## 5. Crop Recommendation Engine

Use:

- Farmer soil/farm data.
- BigQuery rainfall normals.
- BigQuery groundwater.
- BigQuery crop production history.
- Earth Engine NDVI/NDWI.

Return top crops with traceable reasons and data sources.

## 6. Earth Engine Farm Signals

Use real Earth Engine:

- Farm point/polygon.
- Sentinel/Landsat NDVI.
- Optional NDWI/water stress.
- Date range and cloud filtering.

## 7. Gemini Advisory Brain

Build final prompt context from:

- Farmer profile.
- Active crop and stage.
- Weather forecast.
- BigQuery historical context.
- Earth Engine signals.
- IMD agromet warning/advisory.

Return JSON only and store source context.

## 8. Voice Pipeline

Implement:

- Google STT primary, Sarvam fallback.
- Google TTS primary, Sarvam fallback.
- Language detection/selection.
- Generated audio URI in Cloud Storage.

## 9. WhatsApp, SMS, Voice Channels

Use:

- WhatsApp: Authkey primary, Twilio fallback.
- SMS/voice: Authkey primary, Twilio fallback.

Support:

- User-initiated free-form WhatsApp session where provider supports it.
- Template messages for proactive alerts.
- Delivery receipts.
- Incoming media download.

## 10. Vision/OCR

Use:

- Gemini Vision primary.
- Vertex AI Vision fallback.

Flows:

- Crop photo diagnosis.
- Soil-card extraction.
- Expert ticket creation.

## 11. Daily Alert Worker

Use Cloud Scheduler + Pub/Sub:

1. Pull active farmers/crops.
2. Fetch weather + public-data context.
3. Classify risk.
4. Generate advisory.
5. Send WhatsApp/SMS/voice by `AlertPriorityPolicy`.
6. Store delivery and decision trace.
