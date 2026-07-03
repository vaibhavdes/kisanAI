# Authkey SMS and WhatsApp

Authkey can be considered for quick SMS and WhatsApp testing because it provides developer-friendly messaging APIs and trial/sandbox-style onboarding. Use it only through provider adapters so the app can switch providers later.

Official links:

- Authkey home: https://authkey.io/
- WhatsApp Business API page: https://authkey.io/whatsapp-business-api

## Best Use In This Project

- SMS fallback when WhatsApp is unavailable.
- WhatsApp Business API test/demo if Meta direct onboarding takes longer.
- Voice-call fallback for high-priority alerts such as severe dry-spell, flood, pest, or disease risk.
- OTP or verification can be added later, but not needed for hackathon MVP.

## Local Environment

Keep credentials only in local `.env` or Secret Manager:

```env
AUTHKEY_API_KEY=local-only
AUTHKEY_TEST_MOBILE=9970000000
AUTHKEY_TEST_COUNTRY_CODE=91
AUTHKEY_SMS_SENDER=KISAN
AUTHKEY_WHATSAPP_TEMPLATE_ID=approved-template-id
AUTHKEY_WHATSAPP_MEDIA_TEMPLATE_ID=approved-media-template-id
AUTHKEY_SEND_ENABLED=false
```

`AUTHKEY_SEND_ENABLED=false` is intentional. It lets smoke tests verify request construction without sending SMS, WhatsApp, or voice calls.

Enable real sending only for a controlled demo:

```bash
AUTHKEY_SEND_ENABLED=true .venv-google/bin/python smoke_tests/test_authkey_channels.py
```

This can send multiple messages/calls to `AUTHKEY_TEST_MOBILE`, so keep it off in CI and normal local checks.

## Phase 0: Local Mock

Use the existing endpoint:

```text
POST /api/v1/sms/webhook
POST /api/v1/whatsapp/webhook
```

Keep responses local and store messages through `ConversationStore`.

## Phase 1: Hackathon Demo

1. Create an Authkey account.
2. Check available trial/sandbox credits and supported channels.
3. Generate API key/token.
4. Choose channel:
   - SMS for text alerts.
   - WhatsApp API for farmer chat if available in account.
5. Configure webhook URL after deploying FastAPI on Cloud Run:

```text
https://<cloud-run-url>/api/v1/sms/webhook
https://<cloud-run-url>/api/v1/whatsapp/webhook
```

6. Add env vars:

```env
SMS_PROVIDER=authkey
SMS_PROVIDER_API_KEY=...
WHATSAPP_PROVIDER=authkey
WHATSAPP_BUSINESS_TOKEN=...
```

7. Use the adapter methods:
   - `send_sms(phone, text)`
   - `send_voice(phone, text)`
   - `send_parallel_sms_voice(phone, sms, voice)`
   - `send_voice_with_sms_fallback(phone, voice, fallback_sms)`
   - `send_whatsapp_template_get(phone, template_id, params)`
   - `send_whatsapp_template_json(phone, template_id, params)`
   - `send_whatsapp_media_template_get(phone, template_id, media_url)`
   - `send_whatsapp_bulk_template_json(phones, template_id, params)`

## Smoke Tests

Balance/account check calls Authkey for real:

```bash
.venv-google/bin/python smoke_tests/test_authkey_balance.py
```

Channel scenario check defaults to dry-run:

```bash
.venv-google/bin/python smoke_tests/test_authkey_channels.py
```

Covered scenarios:

- SMS direct send.
- Voice direct call.
- Parallel SMS + voice.
- Voice with SMS fallback.
- WhatsApp template using GET.
- WhatsApp template using JSON POST.
- WhatsApp media template using GET.
- WhatsApp bulk template JSON API.

WhatsApp sends need approved Authkey/WhatsApp template IDs. Without real template IDs, keep dry-run enabled.

## Phase 2: Production-Like Pilot

1. Complete any KYC/business verification required by provider.
2. For SMS in India, verify DLT/template rules.
3. Register templates:
   - Dry-spell warning.
   - Crop disease photo request.
   - Rythu Seva expert follow-up.
   - Crop-stage advisory.
4. Add delivery receipt webhook handling.
5. Add retry and failure logging.

## Adapter Shape

Implemented:

```text
app/services/providers/authkey_client.py
```

Each adapter should return a normalized result:

```json
{
  "provider": "authkey",
  "channel": "sms",
  "sent": true,
  "provider_message_id": "...",
  "error": null
}
```

## Risks

- Trial limits may be small.
- SMS delivery in India can require templates/DLT even if API integration is simple.
- WhatsApp business-initiated messages usually require approved templates.
