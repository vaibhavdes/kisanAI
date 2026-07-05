# Twilio WhatsApp Integration Tasks

Goal: integrate WhatsApp completely through Twilio while preserving existing Authkey code and current frontend/backend behavior.

## Phase 0 - Tracking And Grounding

- [x] Create `TASK.md` for implementation phases and task status.
- [x] Create `RECORD.md` for code/logic change records.
- [x] Keep `TASK.md` and `RECORD.md` updated after each completed implementation phase.

## Phase 1 - Twilio Configuration And Dependencies

- [x] Add Twilio runtime dependency to backend package files.
- [x] Add Twilio settings to backend config without removing Authkey settings.
- [x] Add `.env.example` entries for Twilio WhatsApp sender, live-send flag, webhook validation, status callback, and public media URL support.
- [x] Document credential-only values that must come from the user.

## Phase 2 - Twilio Inbound WhatsApp Adapter

- [x] Refactor `/api/v1/twilio/whatsapp` to normalize Twilio WhatsApp inbound form fields through `TwilioWhatsAppService.inbound_payload`.
- [x] Support inbound text messages.
- [x] Support inbound image/photo media.
- [x] Support inbound document media.
- [x] Support inbound audio/voice-note media by passing `MediaUrl0` into backend STT as `audio_uri`.
- [x] Support inbound location messages using `Latitude`, `Longitude`, `Address`, and `Label`.
- [x] Preserve existing farmer registration, language detection, context, intent, conversation logging, media diagnosis, STT, and TTS through `WhatsAppService`.
- [x] Add optional Twilio request signature validation for inbound WhatsApp webhooks.

## Phase 3 - Twilio Replies And Media Responses

- [x] Return TwiML text replies for inbound WhatsApp messages.
- [x] Attach generated voice responses when backend produces `response_audio_base64`.
- [x] Add media-publishing scaffolding so generated audio can be exposed as a URL Twilio can fetch.
- [x] Keep text fallback when no generated response media is available.
- [x] Add TwiML status callback/action attributes where a callback URL is configured.
- [x] Add configurable durable public media publishing through GCS/signed URLs, with short-lived in-memory fallback for local development.

## Phase 4 - Twilio Outbound WhatsApp Sender

- [x] Add Twilio outbound text sender for proactive WhatsApp alerts.
- [x] Add Twilio outbound media sender for public media URLs.
- [x] Add optional Twilio Content Template sender for messages outside the WhatsApp customer-service window.
- [x] Wire Twilio branch into `AlertDeliveryService` when provider route is `twilio`.
- [x] Keep Authkey branch unchanged.
- [x] Support dry-run mode unless `TWILIO_ENABLE_LIVE_SEND=true`.

## Phase 5 - Twilio Status Callbacks And Receipts

- [x] Add `/api/v1/twilio/status` endpoint scaffolding for outbound delivery callbacks.
- [x] Normalize Twilio `MessageStatus` values through existing receipt logic.
- [x] Store Twilio message SID, phone, channel, status, and raw callback payload.
- [x] Add Twilio request signature validation to `/api/v1/twilio/status`.
- [ ] Verify final Twilio delivery status semantics against live callback payloads.

## Phase 6 - Tests

- [x] Test inbound Twilio WhatsApp text.
- [x] Test inbound Twilio WhatsApp image media.
- [x] Test inbound Twilio WhatsApp document media.
- [x] Test inbound Twilio WhatsApp audio/voice note.
- [x] Test inbound Twilio WhatsApp location.
- [x] Test TwiML text response.
- [x] Test TwiML audio media response using a mocked/local media publisher.
- [x] Test Twilio outbound WhatsApp dry-run.
- [x] Test Twilio outbound WhatsApp with provider route set to Twilio.
- [x] Test Twilio status callback receipt saving.
- [x] Test Twilio status callback signature validation.
- [x] Test generated-audio media publishing with durable configuration path and mocked/local fallback.
- [x] Keep existing Authkey tests passing.

## Phase 7 - Documentation And Verification

- [x] Update README webhook/config notes for Twilio WhatsApp.
- [x] Update deployment/env scripts if Twilio envs need to be passed to Cloud Run.
- [x] Run backend test suite.
- [x] Run frontend typecheck if frontend files are touched.
- [x] Record final verification results in `RECORD.md`.
- [x] Verify README Twilio notes cover status callbacks, signature validation, media hosting, dry-run/live-send behavior, and required credentials.
- [ ] Run live Twilio WhatsApp webhook/send/status tests with real credentials and public URL.

## Phase 8 - Full Audit And Root Fixes

- [x] Recheck backend Twilio/Authkey/provider/database integration paths.
- [x] Recheck frontend chat payload and response compatibility.
- [x] Fix stale `sms_voice` provider-route compatibility for older stored route documents.
- [x] Fix provider PATCH semantics so explicit `secondary: null` clears a fallback route.
- [x] Fix WhatsApp provider fallback so configured secondary providers are actually attempted after skipped/failed primary sends.
- [x] Harden Twilio signature validation behind Cloud Run/custom/public base URLs.
- [x] Harden malformed media metadata and invalid base64 handling for voice/image inputs.
- [x] Prevent production generated-audio replies from falling back to per-instance memory when bucket publishing fails.
- [x] Keep Twilio live `queued`/`accepted` results separate from final delivered status.
- [x] Add frontend guards for unsendable local photo URIs and failed voice-note encoding.
- [x] Add Expo ESLint config/dependencies and run frontend lint.
- [x] Run full backend tests, frontend typecheck, frontend lint, and diff whitespace check.
- [x] Run credential-authenticated Twilio account and signed public webhook smoke checks through ngrok.
- [ ] Run real handset WhatsApp sandbox inbound/outbound test after a recipient joins the Twilio sandbox.

## Credentials Needed From User

Ask the user only when live testing or real sends require credentials:

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_FROM`
- Optional `TWILIO_MESSAGING_SERVICE_SID`
- Optional `TWILIO_CONTENT_SID`
- Optional `TWILIO_CONTENT_VARIABLES`
- Optional `TWILIO_STATUS_CALLBACK_URL`
- Optional `TWILIO_MEDIA_BUCKET`
- Optional `TWILIO_MEDIA_PUBLIC_BASE_URL`
