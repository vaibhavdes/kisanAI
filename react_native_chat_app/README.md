# Kisan Alert React Native Chat

Expo React Native farmer chat prototype for Android and web.

## Run

Start the backend:

```bash
cd ..
DATA_STORE_PROVIDER=local ENABLE_GOOGLE_INTEGRATIONS=false .venv-google/bin/uvicorn app.main:app --reload --port 8080
```

Install and run the mobile app:

```bash
cd react_native_chat_app
npm install
npm run typecheck
npm run android
```

For web:

```bash
EXPO_PUBLIC_API_URL=http://127.0.0.1:8080 npm run web
```

Static web export check:

```bash
EXPO_PUBLIC_API_URL=http://127.0.0.1:8080 npm run export:web
```

For Android emulator, the default API URL is `http://10.0.2.2:8080`. For a physical Android device, set `EXPO_PUBLIC_API_URL` to your machine LAN IP, for example:

```bash
EXPO_PUBLIC_API_URL=http://192.168.1.20:8080 npm start
```

## Current Scope

- Phone and language onboarding.
- Mobile-first WhatsApp-like chat UI.
- Text, image, audio and location messages to the app endpoint `/api/v1/chat/message`.
- Provider WhatsApp webhooks remain separate at `/api/v1/whatsapp/webhook` and `/api/v1/twilio/whatsapp`.
- Location permission and coordinate sharing through Expo Location.
- Crop photo selection/camera through Expo Image Picker.
- Voice notes through Expo Audio and backend STT/TTS when configured.
- Runs in Expo Go; no custom native build is required for this first version.
