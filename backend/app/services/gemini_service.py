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
    def classify_farmer_intent(
        self,
        *,
        farmer_id: str | None,
        channel: str | None,
        language: str,
        user_message: str,
        local_intent: str,
    ) -> tuple[str, dict[str, str | None]]:
        errors: list[str] = []
        for provider in self._provider_order():
            start = ServiceAuditLogService().start()
            try:
                if provider == ProviderName.vertex_ai:
                    intent = self._classify_intent_with_vertex(
                        language=language,
                        user_message=user_message,
                        local_intent=local_intent,
                    )
                elif provider == ProviderName.gemini:
                    intent = self._classify_intent_with_gemini(
                        language=language,
                        user_message=user_message,
                        local_intent=local_intent,
                    )
                else:
                    continue
                ServiceAuditLogService().record(
                    farmer_id=farmer_id,
                    channel=channel,
                    service="llm_advisory",
                    operation="classify_farmer_intent",
                    provider=provider.value,
                    success=True,
                    duration_ms=ServiceAuditLogService().elapsed_ms(start),
                    request_body={"language": language, "message": user_message, "local_intent": local_intent},
                    response_body={"intent": intent},
                )
                return intent, {"intentAiSource": provider.value, "intentAiModel": self._model_for_provider(provider)}
            except Exception as exc:
                errors.append(f"{provider.value}:{exc.__class__.__name__}:{exc}")
                ServiceAuditLogService().record(
                    farmer_id=farmer_id,
                    channel=channel,
                    service="llm_advisory",
                    operation="classify_farmer_intent",
                    provider=provider.value,
                    success=False,
                    duration_ms=ServiceAuditLogService().elapsed_ms(start),
                    request_body={"language": language, "message": user_message, "local_intent": local_intent},
                    error=str(exc),
                )
        raise AdvisoryProviderUnavailable("; ".join(errors) or "No LLM intent provider is configured.")

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
            location=settings.vertex_ai_location or settings.google_cloud_location,
        )
        return self._generate_advisory_with_model_fallback(client, ProviderName.vertex_ai, payload)

    def _generate_advisory_with_gemini(self, payload: AdvisoryTestRequest) -> AdvisoryTestResponse:
        from google import genai

        if not settings.gemini_api_key:
            raise AdvisoryProviderUnavailable("GEMINI_API_KEY is required for Gemini API fallback.")
        client = genai.Client(api_key=settings.gemini_api_key)
        return self._generate_advisory_with_model_fallback(client, ProviderName.gemini, payload)

    def _generate_advisory_with_model_fallback(
        self,
        client,
        provider: ProviderName,
        payload: AdvisoryTestRequest,
    ) -> AdvisoryTestResponse:
        errors: list[str] = []
        for model in self._models_for_provider(provider):
            try:
                return self._generate_with_client(
                    client=client,
                    model=model,
                    payload=payload,
                    source=provider.value,
                )
            except Exception as exc:
                errors.append(f"{model}:{exc}")
                if not self._is_resource_exhausted(exc):
                    raise
        raise AdvisoryProviderUnavailable("; ".join(errors))

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
            location=settings.vertex_ai_location or settings.google_cloud_location,
        )
        return self._generate_farmer_reply_with_model_fallback(client, ProviderName.vertex_ai, **kwargs)

    def _classify_intent_with_vertex(self, **kwargs) -> str:
        from google import genai

        if not settings.google_cloud_project:
            raise AdvisoryProviderUnavailable("GOOGLE_CLOUD_PROJECT is required for Vertex AI.")
        client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.vertex_ai_location or settings.google_cloud_location,
        )
        return self._classify_intent_with_model_fallback(client, ProviderName.vertex_ai, **kwargs)

    def _generate_farmer_reply_with_gemini(self, **kwargs) -> str:
        from google import genai

        if not settings.gemini_api_key:
            raise AdvisoryProviderUnavailable("GEMINI_API_KEY is required for Gemini API fallback.")
        client = genai.Client(api_key=settings.gemini_api_key)
        return self._generate_farmer_reply_with_model_fallback(client, ProviderName.gemini, **kwargs)

    def _classify_intent_with_gemini(self, **kwargs) -> str:
        from google import genai

        if not settings.gemini_api_key:
            raise AdvisoryProviderUnavailable("GEMINI_API_KEY is required for Gemini API fallback.")
        client = genai.Client(api_key=settings.gemini_api_key)
        return self._classify_intent_with_model_fallback(client, ProviderName.gemini, **kwargs)

    def _generate_farmer_reply_with_model_fallback(self, client, provider: ProviderName, **kwargs) -> str:
        errors: list[str] = []
        for model in self._models_for_provider(provider):
            try:
                return self._generate_farmer_reply_with_client(client, model, **kwargs)
            except Exception as exc:
                errors.append(f"{model}:{exc}")
                if not self._is_resource_exhausted(exc):
                    raise
        raise AdvisoryProviderUnavailable("; ".join(errors))

    def _classify_intent_with_model_fallback(self, client, provider: ProviderName, **kwargs) -> str:
        errors: list[str] = []
        for model in self._models_for_provider(provider):
            try:
                return self._classify_intent_with_client(client, model, **kwargs)
            except Exception as exc:
                errors.append(f"{model}:{exc}")
                if not self._is_resource_exhausted(exc):
                    raise
        raise AdvisoryProviderUnavailable("; ".join(errors))

    def _classify_intent_with_client(
        self,
        client,
        model: str,
        *,
        language: str,
        user_message: str,
        local_intent: str,
    ) -> str:
        allowed = {
            "general_advisory",
            "weather_query",
            "irrigation_advisory",
            "satellite_advisory",
            "crop_recommendation",
            "crop_planning",
            "crop_diagnosis",
            "identity_query",
            "greeting",
        }
        prompt = f"""
Classify this farmer message into exactly one intent.

Allowed intents:
- weather_query: local weather, rain, temperature forecast.
- irrigation_advisory: whether to water now, soil moisture, dry spell, irrigation.
- satellite_advisory: farm/crop growth, field health report, crop improvement vs last week, water stress seen by satellite, NDVI/satellite/Earth Engine.
- crop_recommendation: which crop to grow or choose.
- crop_planning: farmer says they planted/sowed/planning a crop or gives sowing date/variety.
- crop_diagnosis: disease, pest, leaf spot, crop photo diagnosis.
- identity_query: asks who they are.
- greeting: hello/namaste only.
- general_advisory: anything else.

Return only JSON: {{"intent":"one_allowed_intent"}}

Language code: {language}
Rule-based initial intent: {local_intent}
Farmer message: {user_message}
"""
        response = client.models.generate_content(model=model, contents=prompt)
        data = self._parse_json_response((response.text or "").strip())
        intent = str(data.get("intent") or "").strip()
        if intent not in allowed:
            raise AdvisoryProviderUnavailable(f"Intent classifier returned unsupported intent: {intent}")
        return intent

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

    def _models_for_provider(self, provider: ProviderName) -> list[str]:
        if provider == ProviderName.vertex_ai:
            primary = settings.vertex_ai_model
            fallback = settings.vertex_ai_fallback_models
        else:
            primary = settings.gemini_model
            fallback = settings.gemini_fallback_models
        models = [primary]
        models.extend(model.strip() for model in fallback.split(",") if model.strip())
        deduped: list[str] = []
        for model in models:
            if model not in deduped:
                deduped.append(model)
        return deduped

    def _is_resource_exhausted(self, exc: Exception) -> bool:
        text = str(exc).lower()
        return "resource_exhausted" in text or "resource exhausted" in text or "429" in text or "quota" in text

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
