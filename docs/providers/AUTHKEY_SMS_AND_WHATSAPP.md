# Authkey SMS and WhatsApp

Authkey can be considered for quick SMS and WhatsApp testing because it provides developer-friendly messaging APIs and trial/sandbox-style onboarding. Use it only through provider adapters so the app can switch providers later.

Official links:

- Authkey home: https://authkey.io/
- WhatsApp Business API page: https://authkey.io/whatsapp-business-api

## Best Use In This Project

- SMS fallback when WhatsApp is unavailable.
- WhatsApp Business API test/demo if Meta direct onboarding takes longer.
- OTP or verification can be added later, but not needed for hackathon MVP.

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

7. Implement adapter methods later:
   - `send_sms(phone, text)`
   - `send_whatsapp_text(phone, text)`
   - `send_whatsapp_template(phone, template_name, params)`

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

Create later:

```text
app/services/providers/authkey_sms_provider.py
app/services/providers/authkey_whatsapp_provider.py
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

