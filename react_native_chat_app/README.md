# Kisan AI React Native Chat

Expo React Native farmer chat prototype for Android and web.

This app is the farmer-facing chat frontend. It calls the backend app endpoint:

```text
POST /api/v1/chat/message
```

Provider webhooks such as `/api/v1/whatsapp/webhook` and `/api/v1/twilio/whatsapp` are for WhatsApp providers only, not for this frontend app.

## Run

Start the backend:

```bash
cd ../backend
DATA_STORE_PROVIDER=local ENABLE_GOOGLE_INTEGRATIONS=false .venv/bin/uvicorn app.main:app --reload --port 8080
```

Install and run the mobile app:

```bash
cd react_native_chat_app
npm install
npm run typecheck
npm run android
```

For Android emulator, the default backend URL is `http://10.0.2.2:8080`.

For web:

```bash
EXPO_PUBLIC_API_URL=http://127.0.0.1:8080 npm run web
```

Static web export check:

```bash
EXPO_PUBLIC_API_URL=http://127.0.0.1:8080 npm run export:web
```

Deploy web frontend to Cloud Run after backend is deployed:

```bash
PROJECT_ID=kisanai-501120 \
REGION=asia-south1 \
BACKEND_SERVICE_NAME=kisan-alert-api \
FRONTEND_SERVICE_NAME=kisan-alert-web \
scripts/deploy_cloud_run_web.sh
```

For a physical Android device, set `EXPO_PUBLIC_API_URL` to your machine LAN IP, for example:

```bash
EXPO_PUBLIC_API_URL=http://192.168.1.20:8080 npm start
```

## Current Scope

- Phone and language onboarding.
- Mobile-first WhatsApp-like chat UI.
- Phrase-level UI translations for English, Hindi, Marathi, Telugu, Tamil, Kannada and Gujarati.
- Location/state-based language suggestion when location permission is already available or when the farmer shares location.
- Text, image, audio and location messages to the app endpoint `/api/v1/chat/message`.
- Provider WhatsApp webhooks remain separate at `/api/v1/whatsapp/webhook` and `/api/v1/twilio/whatsapp`.
- Location permission and coordinate sharing through Expo Location.
- Crop photo selection/camera through Expo Image Picker.
- Voice notes through Expo Audio and backend STT/TTS when configured.
- Runs in Expo Go; no custom native build is required for this first version.
