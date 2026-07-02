# Service Fallback Plan

Default strategy: use Google Cloud services first. Use fallback services only when the toggle is enabled in admin/frontend config or when the Google service is unavailable during demo.

## Toggle Names

| Feature | Default Google service | Fallback option | Toggle key |
|---|---|---|---|
| Weather forecast | Google/IMD adapter later | Open-Meteo | `weatherProvider` |
| Historical rainfall | BigQuery public-data tables | Local CSV/sample data, data.gov.in export | `publicDataProvider` |
| Satellite NDVI/NDWI | Earth Engine | Mock satellite index, Sentinel/Landsat public export later | `satelliteProvider` |
| Maps/geocoding | Google Maps + Geocoding | OpenStreetMap + Nominatim | `mapsProvider` |
| Translation | Google Translation API | Gemini direct language response, local phrase fallback | `translationProvider` |
| Speech-to-text | Google Speech-to-Text | Browser Web Speech API in frontend, provider transcript from voice-call service | `speechProvider` |
| Text-to-speech | Google Text-to-Speech | Browser speech synthesis, Twilio/Vomyra provider voice, Sarvam if available | `ttsProvider` |
| WhatsApp | Meta Cloud API or Authkey WhatsApp | Twilio WhatsApp sandbox | `whatsappProvider` |
| SMS | Authkey SMS | Twilio SMS trial, provider mock | `smsProvider` |
| Voice call | Twilio Voice trial | Vomyra if trial/webhook is available | `voiceCallProvider` |
| Storage | Cloud Storage | Local file storage for dev only | `storageProvider` |
| Queue/alerts | Pub/Sub | In-process queue for local dev only | `queueProvider` |
| Database | Firestore | In-memory/local JSON for dev only | `databaseProvider` |

## Recommended Defaults

```json
{
  "weatherProvider": "open_meteo",
  "publicDataProvider": "bigquery",
  "satelliteProvider": "earth_engine",
  "mapsProvider": "google_maps",
  "translationProvider": "gemini",
  "speechProvider": "google_speech",
  "ttsProvider": "google_tts",
  "whatsappProvider": "authkey",
  "smsProvider": "authkey",
  "voiceCallProvider": "twilio",
  "storageProvider": "cloud_storage",
  "queueProvider": "pubsub",
  "databaseProvider": "firestore"
}
```

## Practical Free/Easy Choices For Hackathon

- Weather: Open-Meteo is easiest and free for demo.
- Maps UI: OpenStreetMap tiles are easiest for frontend demo; respect tile usage limits.
- Geocoding: Nominatim can work for small tests; respect usage policy and cache results.
- Translation: Gemini can directly answer in farmer language, so Translation API can be fallback instead of mandatory.
- Speech in browser: Web Speech API is useful for demo but not reliable across all devices.
- TTS in browser: Web Speech synthesis is useful for demo and avoids cloud TTS cost.
- Voice call: Twilio trial is usually easiest.
- WhatsApp: Authkey if your number is already configured; otherwise Meta Cloud API test number.

## Frontend Toggle Design

Create a developer/settings screen later with grouped selectors:

- Communication:
  - WhatsApp provider
  - SMS provider
  - Voice-call provider
- AI and language:
  - Gemini model
  - Translation provider
  - Speech provider
  - TTS provider
- Field intelligence:
  - Weather provider
  - Satellite provider
  - Maps provider
  - Public data provider

Only show this screen in developer/admin mode, not to farmers.

