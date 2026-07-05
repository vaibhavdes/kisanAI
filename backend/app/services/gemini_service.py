import json

from app.core.config import settings
from app.models.schemas import (
    AdvisoryTestRequest,
    AdvisoryTestResponse,
    DiagnosisRequest,
    DiagnosisResult,
    FarmerResponse,
    ProviderFeature,
    ProviderName,
    RiskLevel,
)
from app.repositories.store import store
from app.services.service_audit_log_service import ServiceAuditLogService


class AdvisoryProviderUnavailable(RuntimeError):
    pass


class GeminiService:
    def generate_test_advisory(self, payload: AdvisoryTestRequest) -> AdvisoryTestResponse:
        errors: list[str] = []
        for provider in self._provider_order():
            try:
                if provider == ProviderName.vertex_ai:
                    return self._generate_advisory_with_vertex(payload)
                if provider == ProviderName.gemini:
                    return self._generate_advisory_with_gemini(payload)
            except Exception as exc:
                errors.append(f"{provider.value}:{exc.__class__.__name__}:{exc}")
        message = "; ".join(errors) if errors else "No LLM advisory provider is configured."
        raise AdvisoryProviderUnavailable(message)

    def diagnose_crop_health(
        self,
        farmer: FarmerResponse,
        payload: DiagnosisRequest,
    ) -> DiagnosisResult:
        if settings.enable_google_integrations and settings.gemini_api_key:
            # Production path: call Gemini or Vertex Vision with photo_uri and symptoms.
            # Keep response shape identical to this fallback.
            return self._fallback_diagnosis(payload)

        return self._fallback_diagnosis(payload)

    def generate_farmer_reply(
        self,
        *,
        farmer_id: str | None,
        channel: str | None,
        language: str,
        user_message: str,
        intent: str,
        farmer_context: dict,
        recent_messages: list[dict],
        data_context: dict,
        draft_answer: str,
    ) -> tuple[str, dict[str, str | None]]:
        errors: list[str] = []
        for provider in self._provider_order():
            start = ServiceAuditLogService().start()
            try:
                if provider == ProviderName.vertex_ai:
                    reply = self._generate_farmer_reply_with_vertex(
                        language=language,
                        user_message=user_message,
                        intent=intent,
                        farmer_context=farmer_context,
                        recent_messages=recent_messages,
                        data_context=data_context,
                        draft_answer=draft_answer,
                    )
                elif provider == ProviderName.gemini:
                    reply = self._generate_farmer_reply_with_gemini(
                        language=language,
                        user_message=user_message,
                        intent=intent,
                        farmer_context=farmer_context,
                        recent_messages=recent_messages,
                        data_context=data_context,
                        draft_answer=draft_answer,
                    )
                else:
                    continue
                ServiceAuditLogService().record(
                    farmer_id=farmer_id,
                    channel=channel,
                    service="llm_advisory",
                    operation="generate_farmer_reply",
                    provider=provider.value,
                    success=True,
                    duration_ms=ServiceAuditLogService().elapsed_ms(start),
                    request_body={"intent": intent, "language": language, "message": user_message},
                    response_body={"reply": reply},
                )
                return reply, {"aiSource": provider.value, "aiModel": self._model_for_provider(provider)}
            except Exception as exc:
                errors.append(f"{provider.value}:{exc.__class__.__name__}:{exc}")
                ServiceAuditLogService().record(
                    farmer_id=farmer_id,
                    channel=channel,
                    service="llm_advisory",
                    operation="generate_farmer_reply",
                    provider=provider.value,
                    success=False,
                    duration_ms=ServiceAuditLogService().elapsed_ms(start),
                    request_body={"intent": intent, "language": language, "message": user_message},
                    error=str(exc),
                )
        raise AdvisoryProviderUnavailable("; ".join(errors) or "No LLM advisory provider is configured.")

    def _generate_advisory_with_vertex(self, payload: AdvisoryTestRequest) -> AdvisoryTestResponse:
        from google import genai

        if not settings.google_cloud_project:
            raise AdvisoryProviderUnavailable("GOOGLE_CLOUD_PROJECT is required for Vertex AI.")
        client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
        return self._generate_with_client(
            client=client,
            model=settings.vertex_ai_model,
            payload=payload,
            source=ProviderName.vertex_ai.value,
        )

    def _generate_advisory_with_gemini(self, payload: AdvisoryTestRequest) -> AdvisoryTestResponse:
        from google import genai

        if not settings.gemini_api_key:
            raise AdvisoryProviderUnavailable("GEMINI_API_KEY is required for Gemini API fallback.")
        client = genai.Client(api_key=settings.gemini_api_key)
        return self._generate_with_client(
            client=client,
            model=settings.gemini_model,
            payload=payload,
            source=ProviderName.gemini.value,
        )

    def _generate_with_client(
        self,
        *,
        client,
        model: str,
        payload: AdvisoryTestRequest,
        source: str,
    ) -> AdvisoryTestResponse:
        prompt = f"""
You are KISAN-AI, an agricultural advisory assistant.

Return only JSON with keys:
advisory_text, risk_level, recommended_actions.

Farmer language: {payload.language}
Farmer name: {payload.farmer_name}
Location: {payload.location}
Crop: {payload.crop}
Crop stage: {payload.crop_stage}
Weather: {payload.weather_summary}
Rain forecast mm: {payload.rainfall_forecast_mm}
Soil moisture: {payload.soil_moisture}

Keep advisory farmer-friendly, short, and actionable.
"""
        response = client.models.generate_content(model=model, contents=prompt)
        text = (response.text or "").strip()
        if not text:
            raise AdvisoryProviderUnavailable(f"{source} returned an empty advisory response.")
        data = self._parse_json_response(text)
        actions = data.get("recommended_actions", [])
        if not isinstance(actions, list):
            actions = []
        return AdvisoryTestResponse(
            source=source,
            model=model,
            advisory_text=str(data.get("advisory_text") or text),
            risk_level=self._risk_from_text(str(data.get("risk_level") or "medium")),
            recommended_actions=[str(item) for item in actions if str(item).strip()][:5],
        )

    def _generate_farmer_reply_with_vertex(self, **kwargs) -> str:
        from google import genai

        if not settings.google_cloud_project:
            raise AdvisoryProviderUnavailable("GOOGLE_CLOUD_PROJECT is required for Vertex AI.")
        client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
        return self._generate_farmer_reply_with_client(client, settings.vertex_ai_model, **kwargs)

    def _generate_farmer_reply_with_gemini(self, **kwargs) -> str:
        from google import genai

        if not settings.gemini_api_key:
            raise AdvisoryProviderUnavailable("GEMINI_API_KEY is required for Gemini API fallback.")
        client = genai.Client(api_key=settings.gemini_api_key)
        return self._generate_farmer_reply_with_client(client, settings.gemini_model, **kwargs)

    def _generate_farmer_reply_with_client(
        self,
        client,
        model: str,
        *,
        language: str,
        user_message: str,
        intent: str,
        farmer_context: dict,
        recent_messages: list[dict],
        data_context: dict,
        draft_answer: str,
    ) -> str:
        prompt = f"""
You are Kisan AI, a natural agricultural assistant for small Indian farmers.

Write the final farmer-facing reply only. No JSON, no markdown, no English labels unless the farmer wrote in English.

Rules:
- Reply in the same language/style as the farmer's latest message. If it is Roman Hindi/Hinglish, answer in simple Hindi written naturally. If it is Marathi, answer in Marathi.
- Use simple everyday farmer language. Avoid scientific report style.
- Do not include technical source labels like open_meteo, BigQuery, NDVI unless the farmer asks for source. Those are already logged separately.
- If information is missing, ask only one or two necessary questions and keep already-known details.
- If a crop is planted/planned, continue slot filling naturally: crop, sowing date, variety, area if needed.
- Respect channel: {data_context.get("channel")}. Do not ask for app upload when the farmer is on WhatsApp or SMS.
- Keep under 700 characters.

Latest farmer message: {user_message}
Intent: {intent}
Language code: {language}
Farmer context: {json.dumps(farmer_context, ensure_ascii=False)}
Recent messages: {json.dumps(recent_messages[-8:], ensure_ascii=False)}
Fetched data/context: {json.dumps(data_context, ensure_ascii=False)}

Draft facts to convert into farmer-friendly answer:
{draft_answer}
"""
        response = client.models.generate_content(model=model, contents=prompt)
        text = (response.text or "").strip()
        if not text:
            raise AdvisoryProviderUnavailable("LLM returned an empty farmer reply.")
        return text.removeprefix("```").removesuffix("```").strip()

    def _model_for_provider(self, provider: ProviderName) -> str:
        if provider == ProviderName.vertex_ai:
            return settings.vertex_ai_model
        return settings.gemini_model

    def _parse_json_response(self, text: str) -> dict:
        cleaned = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            parsed = json.loads(cleaned)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

    def _risk_from_text(self, value: str) -> RiskLevel:
        normalized = value.lower()
        if "critical" in normalized:
            return RiskLevel.critical
        if "high" in normalized:
            return RiskLevel.high
        if "low" in normalized:
            return RiskLevel.low
        return RiskLevel.medium

    def _fallback_diagnosis(self, payload: DiagnosisRequest) -> DiagnosisResult:
        text = " ".join(
            item.lower()
            for item in [payload.symptoms_text, payload.voice_transcript, payload.photo_uri]
            if item
        )

        if any(token in text for token in ["curl", "whitefly", "white insects", "leaf curl"]):
            issue = "Possible sucking pest or leaf curl complex"
            action = "Scout leaf underside, use yellow sticky traps, and request expert validation."
            severity = RiskLevel.high
            confidence = 0.78
        elif any(token in text for token in ["yellow", "nitrogen", "pale"]):
            issue = "Possible nutrient deficiency"
            action = "Check soil test and avoid excess nitrogen until moisture is adequate."
            severity = RiskLevel.medium
            confidence = 0.66
        elif any(token in text for token in ["spot", "fungus", "blight"]):
            issue = "Possible fungal leaf disease"
            action = "Remove infected leaves and consult RSK before spraying."
            severity = RiskLevel.high
            confidence = 0.72
        else:
            issue = "General crop stress"
            action = "Capture a clear leaf and whole-plant photo for expert review."
            severity = RiskLevel.medium
            confidence = 0.55

        return DiagnosisResult(
            crop=payload.crop,
            likely_issue=issue,
            confidence=confidence,
            severity=severity,
            immediate_action=action,
            needs_expert_followup=True,
        )

    def _provider_order(self) -> list[ProviderName]:
        route = store.get_provider_route(ProviderFeature.llm_advisory)
        if not route.enabled:
            return []

        providers = [route.primary]
        if route.allow_fallback and route.secondary:
            providers.append(route.secondary)
        return providers
