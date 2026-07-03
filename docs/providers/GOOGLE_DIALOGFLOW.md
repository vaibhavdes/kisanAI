# Google Dialogflow

Dialogflow can be used when conversation routing becomes more structured than simple Gemini function calling. It is optional for MVP, because the current backend already has basic intent routing, but the backend now exposes a Dialogflow CX-compatible fulfillment webhook.

Official links:

- Dialogflow overview: https://cloud.google.com/dialogflow/docs
- Dialogflow CX docs: https://cloud.google.com/dialogflow/cx/docs
- Dialogflow ES docs: https://cloud.google.com/dialogflow/es/docs

## Best Use In This Project

- Menu-like farmer conversation flows.
- Multi-turn slot filling:
  - crop
  - pincode/location
  - crop stage
  - symptoms
  - soil values
- IVR/call flows.
- WhatsApp chatbot routing before Gemini final response.

## Dialogflow CX vs ES

Use Dialogflow CX if:

- Flow is multi-step.
- We need visual state-machine conversations.
- IVR routing is important.
- Team wants reusable flows for WhatsApp, SMS and calls.

Use Dialogflow ES if:

- We need quick simple intents.
- MVP is small.
- We do not need complex state management.

Recommendation: use CX only if the team has enough time. Otherwise keep Gemini function calling + current `channel_intent.py`.

## Phase 0: Current Local Router

Current code:

```text
app/services/channel_intent.py
```

This is enough for:

- water/irrigation
- crop recommendation
- crop diagnosis
- general advisory

## Phase 1: Dialogflow Prototype

1. Create Google Cloud project.
2. Enable Dialogflow API.
3. Create a Dialogflow CX agent in the same Google Cloud project and preferred region.
4. Configure default language and add required Indic languages gradually.
5. Create intents:
   - `irrigation_advisory`
   - `crop_recommendation`
   - `crop_diagnosis`
   - `soil_card_upload`
   - `expert_followup`
6. Create entity types:
   - crop
   - crop stage
   - district
   - pincode
   - soil value
7. Create webhook fulfillment endpoint:

```text
https://<cloud-run-url>/api/v1/dialogflow/webhook
```

8. In each fulfillment, set the webhook tag to one of:
   - `irrigation_advisory`
   - `crop_recommendation`
   - `crop_diagnosis`
   - `location_update`
9. Fulfillment calls internal services:
   - `WeatherService`
   - `RecommendationEngine`
   - `SoilCardVisionService`
   - `GeminiService`
   - `ExpertService`

## Backend Webhook Status

Implemented endpoint:

```text
POST /api/v1/dialogflow/webhook
```

The endpoint accepts Dialogflow CX standard webhook JSON. Dialogflow sends `fulfillmentInfo.tag`, `intentInfo.displayName`, and `sessionInfo.parameters`; the backend returns `fulfillmentResponse.messages`, `sessionInfo.parameters`, and `payload`.

Supported parameters:

```text
phone, name, village, district, state, pincode, latitude, longitude,
crop, season, expected_rainfall_mm, rainfall_forecast_mm,
soil_moisture, temperature_c, water_availability, ndvi, text
```

Example request body for an irrigation flow:

```json
{
  "languageCode": "en-IN",
  "fulfillmentInfo": {"tag": "irrigation_advisory"},
  "sessionInfo": {
    "parameters": {
      "phone": "9999999999",
      "crop": "maize",
      "rainfall_forecast_mm": [0, 0, 0, 0, 0, 0, 0],
      "soil_moisture": 0.13,
      "temperature_c": 37,
      "text": "Should I irrigate maize today?"
    }
  }
}
```

Example response shape:

```json
{
  "fulfillmentResponse": {
    "messages": [
      {"text": {"text": ["Farmer-facing response text"]}}
    ],
    "mergeBehavior": "REPLACE"
  },
  "sessionInfo": {
    "parameters": {
      "intent": "irrigation_advisory",
      "farmer_id": "farmer_x"
    }
  },
  "payload": {
    "intent": "irrigation_advisory",
    "source": "kisan_alert_backend"
  }
}
```

Dialogflow CX official webhook behavior to remember:

- Dialogflow sends an HTTPS POST to the configured webhook URL during fulfillment.
- The response must return before the configured webhook timeout and stay within Dialogflow response-size limits.
- `fulfillmentResponse` carries the farmer-facing response text.
- `sessionInfo.parameters` can update parameters for the next page/turn.

## Phase 2: Multichannel Dialogflow

1. WhatsApp/SMS/call webhook receives farmer message.
2. Provider adapter sends normalized text to Dialogflow.
3. Dialogflow returns intent and parameters.
4. Backend calls internal service.
5. Gemini generates natural response.
6. Response is sent back via original channel.

## Phase 3: Production

1. Add language-specific intents/entities.
2. Add fallback to Gemini when Dialogflow confidence is low.
3. Log all turns in `ConversationStore`.
4. Evaluate missed intents using BigQuery.
5. Add human handoff for high-risk diagnosis.

## Adapter Shape

Implemented:

```text
app/services/dialogflow_service.py
app/api/v1/endpoints/dialogflow.py
```

Normalized result:

```json
{
  "intent": "irrigation_advisory",
  "confidence": 0.87,
  "parameters": {
    "crop": "maize",
    "pincode": "522001"
  }
}
```

## When Not To Use Dialogflow

Do not add Dialogflow if the demo can be completed with Gemini function calling and simple intent routing. Dialogflow is valuable when scripted, auditable, multi-step flows matter.
