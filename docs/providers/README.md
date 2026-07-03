# Channel Provider Roadmap

This folder documents provider options for the Kisan Alert hackathon build. Keep provider-specific code behind the existing service interfaces:

- SMS: `SmsService`
- WhatsApp: `WhatsAppService`
- Voice/IVR/web call: `CallService` and `VoiceService`
- Conversational routing: future Dialogflow adapter

## Recommended Phase Plan

| Phase | Goal | Recommended path |
|---|---|---|
| Phase 0: local API verification | Show endpoint contracts without provider side effects | Use FastAPI endpoints and unit tests |
| Phase 1: hackathon proof | Real WhatsApp/SMS/voice proof | Authkey for SMS/voice, WhatsApp provider with approved template/session messaging, Twilio fallback |
| Phase 2: structured conversation | Intent routing and multilingual flows | Dialogflow CX/ES or Gemini function-calling orchestration |
| Phase 3: production pilot | Reliable farmer outreach | Approved WhatsApp Business account, SMS DLT setup, voice provider number, message templates, opt-in handling |

## Provider Priority

1. WhatsApp Business Cloud API or Authkey WhatsApp: most farmer-friendly channel.
2. SMS through Authkey or another India SMS provider: fallback for low connectivity.
3. Voice call through Authkey, with Twilio fallback: only for high/critical priority alerts.
4. Dialogflow: useful once intents and scripted flows become complex.

## Common Integration Rules

- Do not store provider tokens in git. Use `.env`.
- Persist incoming webhook payloads in `ConversationStore` for demo traceability.
- Use `AlertPriorityPolicy` to decide channel escalation.
- Keep provider adapters small; convert provider payloads into internal schemas.
- For India SMS, expect DLT/template requirements for production.
- For WhatsApp, expect template approval for business-initiated messages.

## Free/Sandbox Caution

Provider trial/free limits can change. Treat every free tier as a demo helper, not a production plan. Verify quota, country support, sender limits, and business verification status during onboarding.
