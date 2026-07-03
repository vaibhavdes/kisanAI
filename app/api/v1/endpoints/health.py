from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    google_ready = bool(settings.enable_google_integrations and settings.google_cloud_project)
    authkey_ready = bool(settings.authkey_api_key)
    return {
        "status": True,
        "checkedAt": datetime.now(UTC).isoformat(),
        "services": {
            "api": True,
            "database": True,
            "vertexAi": google_ready,
            "gemini": bool(settings.gemini_api_key),
            "earthEngine": google_ready,
            "speechToText": google_ready,
            "textToSpeech": google_ready,
            "sms": authkey_ready or bool(settings.sms_provider_api_key),
            "whatsappBusiness": authkey_ready or bool(settings.whatsapp_business_token),
            "voiceCall": authkey_ready or bool(settings.voice_call_provider_api_key),
        },
    }
