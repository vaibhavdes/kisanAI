# Vomyra Voice AI

Vomyra can be evaluated for AI voice call demos, virtual phone numbers, and web/voice call style interaction. Because provider capabilities and pricing can change, treat it as a Phase 1 experiment until account setup is verified.

Official link:

- Vomyra: https://vomyra.com/

## Best Use In This Project

- High-priority dry-spell or disease alerts via automated call.
- Farmer calls a number and speaks in local language.
- Web voice demo if a browser-style voice call widget/API is available.

## Phase 0: Local Mock

Use:

```text
POST /api/v1/calls/webhook
```

Supported input:

- `from_phone`
- `call_id`
- `transcript`
- `language`
- `dtmf_digit`

The current `CallService` maps transcript/DTMF into internal intents.

## Phase 1: Trial Voice Demo

1. Create a Vomyra account.
2. Check whether trial/free usage is available for:
   - Phone number.
   - Inbound calls.
   - Outbound calls.
   - Web voice widget/API.
   - AI voice agent.
3. Configure a webhook/callback URL after Cloud Run deployment:

```text
https://<cloud-run-url>/api/v1/calls/webhook
```

4. Add env vars:

```env
VOICE_CALL_PROVIDER=vomyra
VOICE_CALL_PROVIDER_API_KEY=...
VOICE_CALL_WEBHOOK_SECRET=...
```

5. Test two flows:
   - Farmer presses `1` for water advice, `2` for crop suggestion, `3` for crop disease.
   - Farmer speaks a question, provider sends transcript.

## Phase 2: AI Voice Integration

1. Decide who owns speech:
   - Vomyra handles STT/TTS and sends transcript.
   - Or Kisan Alert uses Google STT/TTS and Vomyra only handles telephony.
2. If using Google STT/TTS:
   - Call provider records audio.
   - Backend sends audio to Cloud Speech-to-Text.
   - Gemini creates response.
   - Cloud Text-to-Speech creates audio.
   - Provider plays response.
3. Store transcript and response through `ConversationStore`.

## Phase 3: Critical Alert Calls

1. Use `AlertPriorityPolicy`.
2. Only place calls for `urgent` or selected `high` alerts.
3. Add retry limit, quiet hours, and call outcome tracking.
4. Escalate unanswered critical calls to SMS/WhatsApp and expert queue.

## Adapter Shape

Create later:

```text
app/services/providers/vomyra_call_provider.py
```

Normalize provider callback into:

```json
{
  "from_phone": "...",
  "call_id": "...",
  "transcript": "...",
  "dtmf_digit": "1",
  "language": "hi-IN"
}
```

## Risks

- Need to verify current API/webhook documentation during signup.
- Trial voice minutes may be limited.
- India telephony may require number/KYC approval.

