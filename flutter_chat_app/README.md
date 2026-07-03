# Kisan Alert Flutter Chat

Mobile-first WhatsApp-like farmer chat prototype.

## Run

Start the backend first:

```bash
cd ..
uvicorn app.main:app --reload --port 8080
```

Run on Android emulator:

```bash
cd flutter_chat_app
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8080
```

Run on Chrome or desktop:

```bash
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8080
```

## Current Scope

- Phone and language onboarding.
- WhatsApp-like chat surface.
- Sends text to `/api/v1/whatsapp/webhook`.
- Location, crop-photo and voice-note demo buttons send normalized backend payloads.
- Device GPS/camera plugins are intentionally not added yet; add `geolocator` and `image_picker` after the flow is approved.
