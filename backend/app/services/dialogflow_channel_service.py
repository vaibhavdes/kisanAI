from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from app.core.config import settings


class DialogflowChannelUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class DialogflowChannelResult:
    intent: str
    confidence: float | None = None
    reply: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None


class DialogflowChannelService:
    def route_text(
        self,
        *,
        text: str,
        language: str,
        session_id: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> DialogflowChannelResult:
        if not self.is_configured():
            raise DialogflowChannelUnavailable("Dialogflow routing is disabled or agent is not configured.")

        from google.cloud.dialogflowcx_v3 import DetectIntentRequest, QueryInput, SessionsClient, TextInput
        from google.protobuf.json_format import MessageToDict

        client = SessionsClient(client_options=self._client_options())
        session = self._session_path(client, session_id or f"session-{uuid4().hex[:12]}")
        request_args: dict[str, Any] = {
            "session": session,
            "query_input": QueryInput(text=TextInput(text=text), language_code=language),
        }
        query_params = self._query_params(parameters)
        if query_params:
            request_args["query_params"] = query_params
        request = DetectIntentRequest(**request_args)
        response = client.detect_intent(request=request)
        result = response.query_result
        detected_intent = self._normalize_intent(getattr(result.intent, "display_name", "") or "unknown")
        confidence = float(result.intent_detection_confidence or 0)
        if confidence < settings.dialogflow_confidence_threshold:
            raise DialogflowChannelUnavailable(
                f"Dialogflow confidence {confidence:.2f} below threshold {settings.dialogflow_confidence_threshold:.2f}."
            )

        return DialogflowChannelResult(
            intent=detected_intent,
            confidence=confidence,
            reply=self._reply_text(result.response_messages),
            parameters=MessageToDict(result.parameters) if result.parameters else {},
            session_id=session.split("/")[-1],
        )

    def is_configured(self) -> bool:
        return bool(
            settings.dialogflow_routing_enabled
            and settings.enable_google_integrations
            and settings.google_cloud_project
            and settings.dialogflow_agent_id
        )

    def _client_options(self) -> dict[str, str] | None:
        location = self._location()
        if location == "global":
            return None
        return {"api_endpoint": f"{location}-dialogflow.googleapis.com"}

    def _session_path(self, client: Any, session_id: str) -> str:
        location = self._location()
        base = client.session_path(
            settings.google_cloud_project,
            location,
            settings.dialogflow_agent_id,
            session_id,
        )
        if settings.dialogflow_environment_id:
            return (
                f"projects/{settings.google_cloud_project}/locations/{location}/agents/"
                f"{settings.dialogflow_agent_id}/environments/{settings.dialogflow_environment_id}/sessions/{session_id}"
            )
        return base

    def _query_params(self, parameters: dict[str, Any] | None):
        if not parameters:
            return None
        from google.cloud.dialogflowcx_v3 import QueryParameters
        from google.protobuf.struct_pb2 import Struct

        struct = Struct()
        struct.update(parameters)
        return QueryParameters(parameters=struct)

    def _location(self) -> str:
        return settings.dialogflow_location or "global"

    def _reply_text(self, messages: Any) -> str | None:
        parts: list[str] = []
        for message in messages:
            text = getattr(message, "text", None)
            if text and getattr(text, "text", None):
                parts.extend(item for item in text.text if item)
        return "\n".join(parts) if parts else None

    def _normalize_intent(self, value: str) -> str:
        normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
        aliases = {
            "water": "irrigation_advisory",
            "irrigation": "irrigation_advisory",
            "irrigation_advisory": "irrigation_advisory",
            "crop": "crop_recommendation",
            "crop_recommendation": "crop_recommendation",
            "recommend_crop": "crop_recommendation",
            "photo": "crop_diagnosis",
            "crop_photo": "crop_diagnosis",
            "crop_diagnosis": "crop_diagnosis",
            "disease": "crop_diagnosis",
            "location": "location_update",
            "location_update": "location_update",
        }
        return aliases.get(normalized, normalized or "unknown")
