from html import escape
from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.models.schemas import SmsWebhookRequest, VoiceCallWebhookRequest, WhatsAppWebhookRequest
from app.services.call_service import CallService
from app.services.sms_service import SmsService
from app.services.whatsapp_service import WhatsAppService

router = APIRouter()


@router.post("/whatsapp")
async def twilio_whatsapp_webhook(request: Request) -> Response:
    form = await _form_data(request)
    media_type, media_url, media_content_type = _twilio_media(form)
    response = WhatsAppService().handle_message(
        WhatsAppWebhookRequest(
            from_phone=_clean_channel_phone(_first(form, "From")),
            message_id=_first(form, "MessageSid") or _first(form, "SmsMessageSid"),
            text=_first(form, "Body") or None,
            media_uri=media_url,
            media_mime_type=media_content_type,
            media_type=media_type,
            latitude=_float_or_none(_first(form, "Latitude")),
            longitude=_float_or_none(_first(form, "Longitude")),
            location_label=_first(form, "Label") or _first(form, "Address"),
            language=_first(form, "Language") or None,
        ),
        channel="whatsapp",
        send_outbound=False,
    )
    return _messaging_twiml(response.reply)


@router.post("/sms")
async def twilio_sms_webhook(request: Request) -> Response:
    form = await _form_data(request)
    response = SmsService().handle_message(
        SmsWebhookRequest(
            from_phone=_clean_channel_phone(_first(form, "From")),
            text=_first(form, "Body") or "",
            language=_first(form, "Language") or "hi-IN",
        )
    )
    return _messaging_twiml(response.reply)


@router.post("/voice")
async def twilio_voice_webhook(request: Request) -> Response:
    form = await _form_data(request)
    language = _first(form, "Language") or "hi-IN"
    response = CallService().handle_call(
        VoiceCallWebhookRequest(
            from_phone=_clean_channel_phone(_first(form, "From")),
            call_id=_first(form, "CallSid") or _first(form, "CallUUID") or "twilio-call",
            transcript=_first(form, "SpeechResult") or None,
            dtmf_digit=_first(form, "Digits") or None,
            language=language,
        )
    )
    return _voice_twiml(response.spoken_reply, language=language)


async def _form_data(request: Request) -> dict[str, str]:
    body = (await request.body()).decode("utf-8")
    parsed = parse_qs(body, keep_blank_values=True)
    return {key: values[-1] for key, values in parsed.items()}


def _twilio_media(form: dict[str, str]) -> tuple[str | None, str | None, str | None]:
    media_url = _first(form, "MediaUrl0")
    media_content_type = _first(form, "MediaContentType0")
    if not media_url:
        return None, None, None
    if (media_content_type or "").startswith("image/"):
        return "image", media_url, media_content_type
    if (media_content_type or "").startswith("audio/"):
        return "audio", None, media_content_type
    return "document", media_url, media_content_type


def _first(form: dict[str, str], key: str) -> str:
    return (form.get(key) or "").strip()


def _float_or_none(value: str) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _clean_channel_phone(value: str) -> str:
    return value.removeprefix("whatsapp:").strip()


def _messaging_twiml(message: str) -> Response:
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escape(message)}</Message></Response>'
    return Response(content=xml, media_type="text/xml")


def _voice_twiml(message: str, *, language: str) -> Response:
    safe_message = escape(message)
    safe_language = escape(language)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        f'<Gather input="speech dtmf" action="/api/v1/twilio/voice" method="POST" language="{safe_language}">'
        f"<Say>{safe_message}</Say>"
        "</Gather>"
        f"<Say>{safe_message}</Say>"
        "</Response>"
    )
    return Response(content=xml, media_type="text/xml")
