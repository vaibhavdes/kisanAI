from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.models.schemas import LiveTokenRequest, LiveTokenResponse


class LiveCallService:
    def create_token(self, payload: LiveTokenRequest) -> LiveTokenResponse:
        model = payload.model or settings.gemini_live_model
        if not settings.enable_google_integrations or not settings.gemini_api_key:
            return LiveTokenResponse(
                ready=False,
                model=model,
                note="Gemini Live is not configured. Set ENABLE_GOOGLE_INTEGRATIONS=true and GEMINI_API_KEY.",
            )

        from google import genai

        now = datetime.now(UTC)
        expire_time = now + timedelta(minutes=30)
        new_session_expire_time = now + timedelta(minutes=1)
        client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options={"api_version": "v1alpha"},
        )
        token = client.auth_tokens.create(
            config={
                "uses": 1,
                "expire_time": expire_time,
                "new_session_expire_time": new_session_expire_time,
                "live_connect_constraints": {
                    "model": model,
                    "config": {
                        "session_resumption": {},
                        "temperature": 0.7,
                        "response_modalities": ["AUDIO"],
                    },
                },
                "http_options": {"api_version": "v1alpha"},
            }
        )
        return LiveTokenResponse(
            ready=True,
            model=model,
            token=token.name,
            expire_time=expire_time,
            new_session_expire_time=new_session_expire_time,
            note="Use this short-lived token from the frontend for Gemini Live WebSocket/SDK audio session.",
        )
