# Service Fallback Plan

Default strategy: use Google Cloud services first. Use fallback services only when the toggle is enabled in admin/frontend config or when the Google service is unavailable during demo.

## Toggle Names

| Feature | Default Google service | Fallback option | Toggle key |
|---|---|---|---|
| Weather forecast | Google/IMD adapter later | Open-Meteo | `weatherProvider` |
| Historical rainfall | BigQuery public-data tables | data.gov.in/official export loaded into BigQuery | `publicDataProvider` |
| Satellite NDVI/NDWI | Earth Engine | Mock satellite index, Sentinel/Landsat public export later | `satelliteProvider` |
| Maps/geocoding | Google Maps + Geocoding | OpenStreetMap + Nominatim | `mapsProvider` |
| Translation | Google Translation API | Gemini direct language response, local phrase fallback | `translationProvider` |
| Speech-to-text | Google Speech-to-Text | Browser Web Speech API in frontend, provider transcript from voice-call service | `speechProvider` |
| Text-to-speech | Google Text-to-Speech | Sarvam TTS if available | `ttsProvider` |
| WhatsApp | Meta Cloud API or Authkey WhatsApp | Twilio WhatsApp sandbox | `whatsappProvider` |
| SMS | Authkey SMS | Twilio SMS trial | `smsProvider` |
| Voice call | Authkey voice | Twilio Voice trial | `voiceCallProvider` |
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

- Weather: Open-Meteo is the free fallback when IMD/government access is unavailable.
- Maps UI: OpenStreetMap tiles can be used only as configured fallback; respect tile usage limits.
- Geocoding: Nominatim can work for small tests; respect usage policy and cache results.
- Translation: Gemini can directly answer in farmer language, so Translation API can be fallback instead of mandatory.
- Speech in browser: Web Speech API is not a backend provider; keep it outside core advisory decisions.
- TTS in browser: Browser speech synthesis is not a backend provider; use only as frontend convenience.
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
