# WhatsApp Integration Notes

This file records the Twilio WhatsApp sandbox setup, test URLs, smoke-test results, and operational notes for the current local/ngrok integration.

## Sandbox Settings

Use these values in Twilio Console > Messaging > Try it out > Send a WhatsApp message > Sandbox settings.

```text
When a message comes in:
https://<your-ngrok-domain>/api/v1/twilio/whatsapp
Method: POST

Status callback URL:
https://<your-ngrok-domain>/api/v1/twilio/status
Method: POST
```

The ngrok URL is temporary. If ngrok is restarted, replace the hostname in both Twilio Sandbox fields.

## Required Environment

Keep these in local ignored env/secrets only. Do not commit real values.

```text
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_PUBLIC_BASE_URL=https://<your-ngrok-domain>
TWILIO_VALIDATE_WEBHOOKS=true
TWILIO_ENABLE_LIVE_SEND=false
```

For real live outbound proactive sends, set `TWILIO_ENABLE_LIVE_SEND=true`. For sandbox testing, the recipient must first join the sandbox from WhatsApp.

## Local Services Used

```text
Backend:
http://127.0.0.1:8000

ngrok API:
http://127.0.0.1:4040/api/tunnels

Current public URL:
https://<your-ngrok-domain>
```

Backend health was verified at `/health`, with WhatsApp readiness true.

## Completed Tests

### Credential And Webhook Smoke

- Twilio account authentication succeeded.
- Account status returned `active`.
- Account type returned `Trial`.
- Public `/health` through ngrok returned HTTP 200.
- Signed POST to `/api/v1/twilio/whatsapp` returned HTTP 200 with TwiML.
- Unsigned POST to `/api/v1/twilio/whatsapp` returned HTTP 403.
- Signed POST to `/api/v1/twilio/status` returned HTTP 200 and saved a delivery receipt.

### Inbound Text

- Before Sandbox settings were updated, Twilio replied with its default message:

```text
Configure your WhatsApp Sandbox's Inbound URL to change this message.
```

- This confirmed Twilio was not yet routing inbound messages to the backend.
- After updating Sandbox settings, inbound webhook routing reached the backend.

### Inbound Image

- Signed inbound image webhook simulation returned HTTP 200 TwiML.
- Backend handled the image media path.

### Inbound Document

- Signed inbound document webhook simulation returned HTTP 200 TwiML.
- Backend returned the document-received response path.

### Inbound Audio

- Signed inbound audio webhook simulation returned HTTP 200 TwiML.
- For the smoke test, STT/TTS provider routes were temporarily disabled to avoid paid speech calls.
- Routes were restored afterward.

### Inbound Location

- Real WhatsApp location was sent from the verified sandbox phone.
- Twilio delivered the location to `/api/v1/twilio/whatsapp`.
- Backend returned HTTP 200.
- Farmer profile was created/identified for the verified phone.
- Farm coordinates were saved and verified. Exact test coordinates are intentionally redacted before push:

```text
latitude: [redacted]
longitude: [redacted]
```

- Backend generated a reply and Twilio fetched generated audio reply media from `/api/v1/twilio/media/{media_id}` with HTTP 200.

### Outbound Image Media

First attempt:

- Media URL was a Wikimedia thumbnail.
- Twilio accepted the request with HTTP 201 and initial status `queued`.
- Twilio later failed it with error `63019`.
- Root cause: Twilio could not download that media URL.

Successful retry:

- Media URL: `https://demo.twilio.com/owl.png`
- Media precheck returned HTTP 200 with `image/png`.
- Twilio accepted the request with HTTP 201 and initial status `queued`.
- After the recipient joined the sandbox, Twilio reported the message as `read`.
- The image was received on the handset.

### Outbound Audio Media

- Media URL was a short direct MP3 with `audio/mpeg` content type.
- Media precheck returned HTTP 200 with `audio/mpeg`.
- Twilio accepted the request with HTTP 201 and initial status `queued`.
- Status progression:

```text
queued -> sent -> read
```

- Error code was `null`.

## Important Twilio Sandbox Notes

- Sandbox recipient must send the join code before receiving outbound WhatsApp messages.
- If the recipient has not joined, outbound free-form messages can fail or become undelivered.
- If the sandbox inbound URL is not set, Twilio uses its default responder and the backend will not receive messages.
- Twilio `sent` does not always mean the phone displayed it. Use final callback/poll states such as `delivered` or `read` where possible.
- Error `63016` means the message cannot be sent as a free-form WhatsApp message in the current window/session/template context.
- Error `63019` means Twilio could not download the media URL.
- Outbound media URLs must be direct, public, unauthenticated, and return the correct `Content-Type`.

## Backend Behavior Verified

- Twilio webhook signature validation works with `TWILIO_PUBLIC_BASE_URL`.
- WhatsApp inbound text/media/location flows route through `WhatsAppService`.
- Farmer identity is phone based.
- New farmer records can be created from WhatsApp inbound messages.
- Location updates save latitude/longitude into the farmer farm profile.
- TwiML text replies are returned to Twilio.
- Generated audio replies can be served through `/api/v1/twilio/media/{media_id}` for local/ngrok testing.
- Twilio status callbacks save receipts.

## Current Limitations

- Current ngrok URL is temporary.
- Sandbox sender is `whatsapp:+14155238886`; production needs a real approved WhatsApp sender or Messaging Service.
- Local in-memory audio media URLs are fine for local testing but should not be used as durable production media.
- Real production proactive messages outside the WhatsApp session window should use approved Twilio Content Templates.
- Credentials used for testing should be rotated after demo/testing because they were pasted into local notes/chat.

## Useful Commands

Backend tests:

```powershell
$env:PYTHONPATH='backend'
pytest backend/tests/test_core_flow.py -q
```

Frontend checks:

```powershell
cd react_native_chat_app
npm run typecheck
npm run lint
```

Check current ngrok URL:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:4040/api/tunnels'
```

Check backend health:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health'
```
