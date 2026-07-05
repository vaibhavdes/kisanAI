# Kisan AI Prompts And Intent Routing

## Farmer Reply Prompt

`GeminiService.generate_farmer_reply()` uses Vertex AI Gemini first and Gemini API fallback through the configured provider route `llm_advisory`.

Purpose:
- Convert backend facts into simple farmer language.
- Reply in the language/style of the latest farmer message.
- Keep source/provider details out of farmer-facing text unless the farmer asks.
- Ask only missing questions and carry forward known context.
- Respect channel limits, for example do not ask an SMS farmer to upload in the app.

Core prompt rules:
- You are Kisan AI, a natural agricultural assistant for small Indian farmers.
- Reply only in farmer-facing text, no JSON or markdown.
- Use simple everyday language, not scientific report style.
- Use fetched data/context and recent conversation memory.
- For crop planning, continue slot filling for crop, sowing date, variety, and area if needed.
- Keep the answer concise.

## Intent Map

| Intent | Trigger Examples | Main Services/Data Used | Stored Context Updated | Farmer-Facing Behavior |
|---|---|---|---|---|
| `greeting` / `general_advisory` | Hi, hello, namaste | Conversation history, open tickets | Name if farmer gives it | First asks name if unknown; daily greeting can include open ticket status |
| `identity_query` | who am I, main kaun hu | Farmer profile | None | Tells what profile is known |
| `location_update` | WhatsApp location, pincode, village/taluka text | Google Maps, OSM, India Post fallback | village, taluka, district, state, pincode, coordinates | Confirms identified location once and reuses later |
| `weather_query` | weather, mausam, havaman, rain | Weather route: IMD primary, Open-Meteo fallback | None | Gives simple weather/rain guidance; provider details in metadata/audit |
| `irrigation_advisory` | water, pani, सिंचाई, पाणी | Weather, dry-spell logic, Earth Engine if available, Vertex/Gemini advisory | crop/water info if mentioned | Gives practical irrigation advice |
| `crop_recommendation` | suggest crop, which crop | BigQuery public data, rainfall, groundwater, soil, recommendation engine, Earth Engine if available | crop/water/soil if mentioned | Recommends top crop options and asks only missing critical info |
| `crop_planning` | I planted jowar, planning cotton | Farmer profile, crop-stage planning | active crop, crop status, planted date, variety | Continues slot filling for stage-wise advisory |
| `crop_diagnosis` | crop photo, disease, leaf spot | Gemini/Vertex vision path, expert ticket service | expert ticket | Gives localized diagnosis and creates RSK follow-up ticket |
| `voice_message` | WhatsApp/app audio | Google STT, Sarvam STT, Google TTS, Sarvam TTS | transcript in conversation log | Transcribes, answers, and returns audio when TTS succeeds |
| `document_message` | PDF/document | Soil-card/app upload path placeholder | None | Tells correct channel-specific next step |

## Audit Visibility

Service calls are recorded in `service_audit_logs` and exposed at:

`GET /api/v1/providers/audit?limit=100`

Admin dashboard displays:
- service
- operation
- provider
- success/failure
- status code when available
- duration
- small request/response summaries
- error text

Audited services currently include:
- LLM advisory/natural reply generation
- Weather providers
- BigQuery public data context
- STT
- TTS

## Language Policy

The latest farmer message controls response language. Stored profile language is only a fallback.

Examples:
- `Hindi mein batao` -> Hindi response.
- `Aaj ka havaman` -> Hindi/Marathi inferred by phrase.
- Devanagari Hindi/Marathi is detected from script and words.

The backend still stores initial language for fallback, but it does not force future replies to that language.
