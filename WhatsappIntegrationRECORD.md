# Twilio WhatsApp Integration Record

This file records every code, logic, test, and documentation change made for the Twilio WhatsApp integration.

## 2026-07-04 - Phase 0 Tracking

### Added

- Created `TASK.md` to track phased implementation.
- Created `RECORD.md` to record code and logic changes.

### Logic Decisions

- Twilio WhatsApp integration will be added without removing Authkey SMS and voice-call logic.
- Existing `WhatsAppService` remains the shared business logic for farmer identity, language, context, media diagnosis, voice STT/TTS, and conversation logging.
- Twilio-specific behavior will live in a provider adapter/service layer and in Twilio endpoints.

### Credentials

- No credentials requested or used.

### Verification

- Not run at this initial tracking step.

## 2026-07-04 - Worktree Monitor Snapshot

### Scope

- Monitor-only update. No code, tests, README content, or deployment logic edited by the monitor pass.
- Updated `TASK.md` and `RECORD.md` to reflect observed uncommitted Twilio WhatsApp integration work at that point in the build.

### Observed Code And Logic Changes

- `backend/pyproject.toml`: Added `twilio>=9.0.0` to backend project dependencies.
- `backend/requirements.txt`: Added the `twilio` runtime dependency.
- `backend/.env.example`: Added Twilio account, auth token, WhatsApp sender, Messaging Service, template, callback, public base URL, validation, and live-send env entries.
- `backend/app/core/config.py`: Added matching Twilio settings while leaving Authkey settings in place.
- `backend/app/services/twilio_whatsapp_service.py`: Added `TwilioWhatsAppService` with request validation, Twilio inbound form normalization, TwiML reply generation, response-audio media URL scaffolding, outbound message payload construction, dry-run results, live-send HTTP POST support, callback URL helpers, and WhatsApp phone normalization.
- `backend/app/api/v1/endpoints/twilio.py`: Refactored `/api/v1/twilio/whatsapp` to pass normalized payloads to `WhatsAppService` and return TwiML through the Twilio adapter.
- `backend/app/api/v1/endpoints/twilio.py`: Added `/api/v1/twilio/status` and `/api/v1/twilio/media/{media_id}` scaffolding.
- `backend/app/services/alert_delivery_service.py`: Added the Twilio WhatsApp branch for outbound WhatsApp alerts.
- `backend/app/services/channel_intent.py`: Routed document media to `document_message` instead of crop diagnosis.
- `backend/app/models/schemas.py`: Added `VoiceIntakeRequest.audio_mime_type` so inbound audio MIME type can flow into STT handling.
- `backend/app/services/voice_service.py` and `backend/app/services/vision_ocr_service.py`: Added Twilio basic auth support for `api.twilio.com` media downloads.
- `backend/app/api/v1/endpoints/health.py`: Counted Twilio account/auth/sender readiness toward `whatsappBusiness` health.
- `backend/scripts/deploy_cloud_run.sh` and `backend/scripts/sync_env_to_secret_manager.sh`: Added Twilio deployment and secret sync settings.

### Credentials

- No credentials requested or used.

## 2026-07-04 - Twilio WhatsApp Build Completion

### Added

- `backend/app/services/twilio_whatsapp_service.py`: Added the Twilio WhatsApp adapter for inbound form normalization, TwiML replies, optional webhook signature validation, outbound REST API payload construction, dry-run/live-send behavior, status callback URL generation, WhatsApp phone normalization, and response-audio media publishing.
- `backend/tests/test_core_flow.py`: Added Twilio WhatsApp regression coverage for audio voice notes, document attachments, outbound dry-run routing, outbound media dry-run routing, status callback receipt saving, and unsigned status callback rejection.
- `README.md`: Added Twilio WhatsApp setup notes for inbound webhook URL, status callback URL, webhook signature validation, media hosting, dry-run/live-send behavior, templates, and required credentials.

### Changed

- `backend/app/core/config.py`, `backend/.env.example`, and `backend/scripts/deploy_cloud_run.sh`: Added Twilio credential, sender, template, callback, public base URL, live-send, webhook validation, and reply-media settings.
- `backend/pyproject.toml` and `backend/requirements.txt`: Added the `twilio` runtime dependency.
- `backend/app/api/v1/endpoints/twilio.py`: Refactored `/api/v1/twilio/whatsapp` to use the Twilio adapter and added `/api/v1/twilio/status` plus `/api/v1/twilio/media/{media_id}`.
- `backend/app/api/v1/endpoints/twilio.py`: Added Twilio signature validation to `/api/v1/twilio/status` when `TWILIO_VALIDATE_WEBHOOKS=true`.
- `backend/app/services/twilio_whatsapp_service.py`: Added durable response-audio publishing through `TWILIO_MEDIA_BUCKET` or `STORAGE_BUCKET`, optional `TWILIO_MEDIA_PUBLIC_BASE_URL`, signed URL fallback, and short-lived in-memory local fallback.
- `backend/app/services/alert_delivery_service.py`: Wired Twilio as the WhatsApp provider while preserving Authkey for SMS and voice-call channels.
- `backend/app/models/schemas.py`, `backend/app/services/voice_service.py`, and `backend/app/services/whatsapp_service.py`: Preserved inbound audio MIME type so Twilio voice-note media can be passed correctly into STT.
- `backend/app/services/voice_service.py` and `backend/app/services/vision_ocr_service.py`: Added Twilio basic auth for `api.twilio.com` media downloads and converted failed HTTP media downloads into controlled provider-unavailable errors.
- `backend/app/services/channel_intent.py`, `backend/app/services/whatsapp_service.py`, and `backend/app/utils/language.py`: Added a dedicated `document_message` path so document attachments receive a clear response instead of being treated as crop photos.
- `backend/app/api/v1/endpoints/health.py`: Counts Twilio readiness toward WhatsApp Business health without removing Authkey readiness.
- `backend/scripts/sync_env_to_secret_manager.sh`: Syncs `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` into Secret Manager when present.
- `backend/scripts/print_webhook_urls.sh`: Prints the Twilio status callback URL.
- `backend/app/services/bigquery_public_data_service.py`: Added a lightweight test shim so injected fake clients do not require `google-cloud-bigquery` to be installed locally.

### Logic Decisions

- Twilio is the WhatsApp provider. Authkey is reserved for outbound SMS text and voice calls.
- Twilio live outbound sending remains disabled unless `TWILIO_ENABLE_LIVE_SEND=true`.
- Twilio template sends use `TWILIO_CONTENT_SID` and optional JSON `TWILIO_CONTENT_VARIABLES`; free-form text/media sends remain available for in-session or dry-run flows.
- Generated WhatsApp voice replies prefer durable public media publishing and only use the app-served in-memory media URL as a local development fallback.
- Live Twilio delivery semantics are intentionally left for credential-backed testing because final states depend on real Twilio callback payloads.

### Verification

- `python -m compileall app` passed.
- Focused Twilio/Authkey regression slice passed: 9 tests passed.
- Full backend test suite passed with `python -m pytest -q`: 58 passed, 1 warning.
- `git diff --check` passed with only Windows line-ending warnings.

### Credentials

- No credentials requested or used.
- Live Twilio testing still needs `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM`, and a public backend URL such as ngrok or Cloud Run.

## 2026-07-04 - Full Audit And Root Fixes

### Scope

- Rechecked backend, frontend, provider-route, deployment, and database-adjacent persistence paths after the Twilio WhatsApp implementation.
- Used parallel code-review agents for frontend/API compatibility, database/repository behavior, and deployment/config risks, then applied root fixes in the main workspace.

### Changed

- `backend/app/services/provider_config_service.py`: Restricted `sms_voice` to Authkey only, normalized stale stored `sms_voice` routes that still had Twilio fallback, and fixed PATCH semantics so explicit `secondary: null`, `allow_fallback`, `enabled`, and `note` updates are honored.
- `backend/app/repositories/store.py`: Updated default `sms_voice` route to Authkey-only with fallback disabled.
- `backend/app/api/v1/endpoints/admin_ui.py`: Removed Twilio from the `sms_voice` provider choices and disabled fallback controls for `sms_voice`.
- `backend/app/services/alert_delivery_service.py`: Added Twilio Content Template variables for `{message}`, `{media_url}`, and `{media_file_name}`, and separated `accepted` Twilio statuses from final sent/delivered status.
- `backend/app/services/twilio_whatsapp_service.py`: Added canonical public-base URL signature validation, strict base64 decoding, malformed `NumMedia` handling, normalized audio extensions, content-variable metadata in dry runs, queued/accepted live-send semantics, and production-safe generated-audio behavior when bucket publishing fails.
- `backend/app/api/v1/endpoints/twilio.py`: Applied Twilio signature validation consistently to WhatsApp, SMS, voice, and status callback endpoints.
- `backend/app/services/voice_service.py` and `backend/app/services/vision_ocr_service.py`: Converted invalid base64 media payloads into service-level unavailable errors instead of leaking decoder exceptions.
- `backend/app/api/v1/endpoints/health.py`: Prevented production live Twilio health from reporting ready when the sender is still the sandbox number.
- `backend/scripts/deploy_cloud_run.sh`: Sets `TWILIO_PUBLIC_BASE_URL` to the Cloud Run service URL after deploy when no custom public/callback URL is provided.
- `backend/scripts/sync_env_to_secret_manager.sh` and `backend/scripts/deploy_cloud_run.sh`: Treat `TWILIO_CONTENT_VARIABLES` as a Secret Manager value so JSON commas do not break `--set-env-vars`.
- `react_native_chat_app/app/index.tsx`: Stopped sending device-local photo URIs that the backend cannot load, added a clear alert when photo base64 is unavailable, guarded failed audio base64 conversion, and improved audio MIME inference for blob/WebM/AAC inputs.
- `react_native_chat_app/package.json`, `react_native_chat_app/package-lock.json`, and `react_native_chat_app/eslint.config.js`: Added Expo ESLint tooling so `npm run lint` can run locally.
- `README.md`: Updated Twilio setup notes for public base URL, content-template media variables, production media hosting behavior, and accepted-vs-delivered status semantics.
- `backend/tests/test_core_flow.py`: Expanded regression coverage for provider fallback, stale route migration, explicit fallback clearing, public-base signature validation, SMS/voice signature rejection, Twilio queued status handling, template media variables, production audio media fallback avoidance, malformed media metadata, invalid base64 handling, frontend-compatible chat behavior, and health readiness.

### Logic Decisions

- Authkey remains the default provider, but configured WhatsApp fallback is now real: skipped/failed primary sends can try the secondary provider.
- SMS/voice outbound delivery remains Authkey-only; Twilio SMS/voice endpoints are inbound webhooks, not outbound providers.
- Twilio `queued`, `accepted`, `sending`, and `scheduled` are treated as accepted by Twilio but not final delivery. Final state must come from status callbacks.
- Production generated voice replies require durable media publishing; short-lived in-memory media URLs are kept for local/ngrok development only.
- Twilio status callbacks are still stored as receipt events. Linking callbacks back to a specific proactive alert record would require a broader delivery-record schema and was not forced into this audit.

### Verification

- Installed missing declared backend dependency `twilio` in the local Python environment.
- `python -m py_compile` passed for the touched backend test/service/config files.
- Focused backend audit regression slice passed: 20 passed, 45 deselected, 1 warning.
- Full backend suite passed: 65 passed, 1 warning.
- Installed frontend dependencies with `npm ci`.
- `npm run typecheck` passed.
- `npm run lint` passed after Expo added ESLint config/dependencies.
- `npm audit --audit-level=high` did not fail; npm still reports moderate Expo dependency-chain advisories whose suggested fix is a breaking Expo upgrade.
- `git diff --check` passed with only Windows line-ending warnings.

### Credentials

- No credentials requested or used.
- Live Twilio webhook/send/status verification still needs real Twilio credentials and a public URL.

## 2026-07-04 - Credential-Authenticated Twilio Smoke Check

### Scope

- Used user-provided Twilio credentials from the local `PS.txt` file as temporary process environment values.
- Started local FastAPI on `127.0.0.1:8000` and exposed it through ngrok.
- Did not write Twilio secrets into repo files, logs, `TASK.md`, or `RECORD.md`.

### Verification

- Twilio account authentication succeeded against the Twilio Accounts API; account status returned `active` and type returned `Trial`.
- Public ngrok `/health` endpoint returned 200 and showed WhatsApp Business readiness.
- Signed public POST to `/api/v1/twilio/whatsapp` returned 200 TwiML with status callback attributes.
- Unsigned public POST to `/api/v1/twilio/whatsapp` returned 403 with `Invalid Twilio signature`.
- Signed public POST to `/api/v1/twilio/status` returned 200 and saved a Twilio WhatsApp delivery receipt.
- Repo secret scan found no copy of the provided SID, auth token, or Twilio phone number under `kisanAI-google-smoke-tests`.

### Remaining Live Step

- Real WhatsApp sandbox inbound/outbound testing still needs a recipient WhatsApp number that has joined the Twilio sandbox. The current checks prove credentials, public URL routing, signature validation, TwiML response, and receipt saving, but they do not send a real WhatsApp message to a handset.

## 2026-07-04 - Twilio Multimedia Smoke Check

### Scope

- Used the user-provided verified recipient number as the outbound WhatsApp target.
- Used temporary process credentials from local `PS.txt`; no Twilio secrets were written into repo files.
- Tested signed inbound multimedia webhook handling and real Twilio outbound WhatsApp media sending through the ngrok-backed local backend.

### Results

- Inbound image webhook simulation returned 200 TwiML.
- Inbound document webhook simulation returned 200 TwiML.
- Inbound audio webhook simulation returned 200 TwiML after temporarily disabling local STT/TTS provider routes to avoid paid speech calls; routes were restored afterward.
- First outbound WhatsApp media attempt used a Wikimedia thumbnail URL. Twilio accepted it with HTTP 201/queued, then marked it failed with error `63019` because Twilio could not download that media URL.
- Retried outbound WhatsApp media with Twilio's documented demo image URL. Media URL precheck returned HTTP 200 with `image/png`; Twilio accepted the message with HTTP 201/queued and later reported status `sent` with no error code.
- The recipient joined the Twilio WhatsApp sandbox after the first outbound media attempt. The pre-join media message later resolved to `undelivered` with Twilio error `63016`.
- After the sandbox join, resent the media message with Twilio's demo image URL. Twilio accepted it with HTTP 201/queued and then reported status `read` with no error code.
- Twilio status callbacks reached `/api/v1/twilio/status` through ngrok and returned 200.
- Repo secret scan found no copy of the provided SID, auth token, or Twilio phone number under `kisanAI-google-smoke-tests`.

### Notes

- Outbound media send is working when the media URL is directly downloadable with a correct content type.
- Error `63019` is a media download failure, not a backend webhook failure.

## 2026-07-04 - Twilio Outbound Audio Media Smoke Check

### Scope

- Sent an outbound WhatsApp audio media message to the verified sandbox recipient after the recipient had joined the Twilio sandbox.
- Used a short direct MP3 URL with `audio/mpeg` content type.
- Used temporary process credentials from local `PS.txt`; no Twilio secrets were written into repo files.

### Results

- Audio media URL precheck returned HTTP 200 with `audio/mpeg`.
- Twilio accepted the WhatsApp audio media request with HTTP 201 and initial status `queued`.
- Twilio status polling moved from `queued` to `sent` to `read` with no error code.

## 2026-07-04 - Twilio Inbound Location Smoke Check

### Scope

- Verified the Twilio Sandbox inbound webhook after the sandbox URL was updated to the ngrok-backed backend endpoint.
- User sent a WhatsApp location from the verified sandbox phone.

### Results

- Twilio delivered the inbound location to `/api/v1/twilio/whatsapp`; backend returned HTTP 200.
- Backend identified/created the farmer for the verified phone and saved farm coordinates.
- Saved farm coordinates were verified; exact test coordinates were redacted before push.
- Backend generated a WhatsApp reply and Twilio fetched the generated audio reply media from `/api/v1/twilio/media/{media_id}` with HTTP 200.

## 2026-07-05 - Provider Ownership Correction

- WhatsApp inbound and outbound is Twilio-only.
- Outbound SMS text and outbound voice calls are Authkey-only.
- `backend/app/services/provider_config_service.py`: Restricted WhatsApp routes to Twilio only and normalizes stale Authkey WhatsApp route documents back to Twilio with fallback disabled.
- `backend/app/services/alert_delivery_service.py`: Removed Authkey WhatsApp delivery from proactive alert delivery.
- `backend/app/services/whatsapp_service.py`: Removed Authkey template sending from generic WhatsApp replies; Twilio webhooks return TwiML directly.
- `backend/app/api/v1/endpoints/health.py`: Counts only Twilio readiness for `whatsappBusiness`.
- `backend/scripts/print_webhook_urls.sh`, `backend/scripts/deploy_cloud_run.sh`, `.env.example`, smoke tests, and README now document Authkey only for SMS/voice.
