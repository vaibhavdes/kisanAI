from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    google_ready = bool(settings.enable_google_integrations and settings.google_cloud_project)
    return {
        "status": True,
        "checkedAt": datetime.now(UTC).isoformat(),
        "services": {
            "api": True,
            "database": True,
            "gemini": google_ready and bool(settings.gemini_api_key),
            "earthEngine": google_ready,
            "speechToText": google_ready,
            "textToSpeech": google_ready,
            "sms": bool(settings.sms_provider_api_key),
            "whatsappBusiness": bool(settings.whatsapp_business_token),
            "voiceCall": bool(settings.voice_call_provider_api_key),
        },
    }
