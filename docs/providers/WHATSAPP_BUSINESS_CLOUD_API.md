# WhatsApp Business Cloud API

Meta WhatsApp Business Platform / Cloud API is the cleanest direct path for WhatsApp-based farmer communication. It is useful for both hackathon testing and a production pilot.

Official links:

- WhatsApp Business Platform: https://business.whatsapp.com/products/business-platform
- Meta developer docs: https://developers.facebook.com/docs/whatsapp/cloud-api
- Pricing docs: https://developers.facebook.com/docs/whatsapp/pricing

## Best Use In This Project

- Farmer chat in a WhatsApp-like flow.
- Business-initiated crop alerts using approved templates.
- Farmer-initiated crop photo upload for diagnosis.
- Voice-note intake later if media download is enabled.

## Phase 0: Local Mock

Use:

```text
POST /api/v1/whatsapp/webhook
```

Payload shape already supports:

- `from_phone`
- `text`
- `media_uri`
- `language`

## Phase 1: Hackathon Test Number

1. Create or use a Meta developer account.
2. Create an app in Meta Developers.
3. Add WhatsApp product.
4. Use the generated test phone number and temporary access token.
5. Add recipient test numbers.
6. Deploy the backend to Cloud Run.
7. Configure webhook callback:

```text
https://<cloud-run-url>/api/v1/whatsapp/webhook
```

8. Add env vars:

```env
WHATSAPP_PROVIDER=meta_cloud_api
WHATSAPP_BUSINESS_TOKEN=...
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_VERIFY_TOKEN=...
```

9. Implement:
   - Webhook verification `GET`.
   - Incoming message parse.
   - Media download for crop photos.
   - Outbound text reply.

## Phase 2: Business-Initiated Alerts

1. Create message templates:
   - Dry-spell alert.
   - Crop-stage advisory.
   - Photo diagnosis follow-up.
   - Expert ticket update.
2. Submit templates for approval.
3. Route alerts using `AlertPriorityPolicy`.
4. Store delivery status in `ConversationStore`.

## Phase 3: Production Pilot

1. Complete business verification.
2. Use permanent access token or secure token refresh.
3. Add opt-in tracking.
4. Add rate limits and retry policy.
5. Add template language variants.

## Adapter Shape

Create later:

```text
app/services/providers/meta_whatsapp_provider.py
```

Normalize incoming WhatsApp messages into:

```json
{
  "from_phone": "...",
  "text": "...",
  "media_uri": "...",
  "language": "hi-IN"
}
```

## Risks

- Test phone number is good for demos, not real public rollout.
- Templates are required for many business-initiated messages.
- Media download requires provider API call and storage.

