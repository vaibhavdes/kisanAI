from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    google_ready = bool(settings.enable_google_integrations and settings.google_cloud_project)
    authkey_ready = bool(settings.authkey_api_key)
    twilio_sandbox_sender = settings.twilio_whatsapp_from == "whatsapp:+14155238886"
    twilio_ready = bool(
        settings.twilio_account_sid
        and settings.twilio_auth_token
        and settings.twilio_whatsapp_from
        and not (settings.environment == "production" and settings.twilio_enable_live_send and twilio_sandbox_sender)
    )
    sarvam_ready = bool(settings.sarvam_api_key)
    return {
        "status": True,
        "checkedAt": datetime.now(UTC).isoformat(),
        "services": {
            "api": True,
            "database": True,
            "vertexAi": google_ready,
            "gemini": bool(settings.gemini_api_key),
            "earthEngine": google_ready,
            "speechToText": google_ready or sarvam_ready,
            "textToSpeech": google_ready or sarvam_ready,
            "translation": google_ready or sarvam_ready,
            "dialogflow": bool(
                settings.enable_google_integrations
                and settings.dialogflow_routing_enabled
                and settings.dialogflow_agent_id
            ),
            "sms": authkey_ready or bool(settings.sms_provider_api_key),
            "whatsappBusiness": authkey_ready or twilio_ready or bool(settings.whatsapp_business_token),
            "voiceCall": authkey_ready or bool(settings.voice_call_provider_api_key),
        },
    }
