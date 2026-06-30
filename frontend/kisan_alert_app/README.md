# Kisan Alert Flutter Frontend

Mobile-first Flutter chat UI for the Kisan Alert hackathon project.

This branch contains only frontend screens and local interaction logic. It does not modify the FastAPI backend.

## Flow

1. First launch shows login with:
   - phone number
   - language selection
2. Farmer enters WhatsApp-like chat.
3. Farmer can type in selected language.
4. Media button opens:
   - camera
   - gallery
   - soil card upload
   - voice note placeholder
5. If a query requires location and location is not shared yet, app asks farmer to share location.
6. If a query requires farm boundary/field selection, app opens a map-style farm selection screen.
7. Chat remains language-first and channel-like, ready to connect with the backend later.

## Run

Flutter is not required in this repository until frontend work starts. Once installed:

```bash
cd frontend/kisan_alert_app
flutter create . --platforms=android,ios,web
flutter pub get
flutter run
```

## Backend Connection Later

Wire these screens to existing backend endpoints:

- `POST /api/v1/whatsapp/webhook` for chat-like text/media intake
- `POST /api/v1/voice/intake` for voice transcript
- `POST /api/v1/soil-cards/extract` for soil card image/text extraction
- `POST /api/v1/advisories/crop-stage` for stage advice
- `POST /api/v1/recommendations/crop` for crop recommendation

Keep platform integrations behind services:

- `LocationService`
- `MediaService`
- `ChatApiClient`
- `FarmMapService`

