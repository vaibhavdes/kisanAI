from html import escape
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from app.core.config import settings
from app.models.schemas import (
    ChannelReceiptRequest,
    ChannelReceiptResponse,
    SmsWebhookRequest,
    VoiceCallWebhookRequest,
)
from app.services.call_service import CallService
from app.services.channel_receipt_service import ChannelReceiptService
from app.services.service_audit_log_service import ServiceAuditLogService
from app.services.sms_service import SmsService
from app.services.twilio_whatsapp_service import TwilioWhatsAppService, twilio_media_store
from app.services.whatsapp_service import WhatsAppService

router = APIRouter()


@router.post("/whatsapp")
async def twilio_whatsapp_webhook(request: Request) -> Response:
    form = await _form_data(request)
    service = TwilioWhatsAppService()
    if not service.validate_webhook(str(request.url), form, request.headers.get("X-Twilio-Signature")):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    payload = service.inbound_payload(form)
    response = WhatsAppService().handle_message(
        payload,
        channel="whatsapp",
        send_outbound=False,
    )
    base_url = service.public_base_url(str(request.base_url))
    followup_results = service.send_response_media_followups(
        to_phone=payload.from_phone,
        response=response,
        base_url=base_url,
        dry_run=not settings.twilio_enable_live_send,
    )
    _record_twilio_followup_audits(response.farmer_id, payload.from_phone, followup_results)
    return Response(
        content=service.twiml_response(
            response,
            base_url=base_url,
            status_callback_url=None,
        ),
        media_type="text/xml",
    )


@router.post("/sms")
async def twilio_sms_webhook(request: Request) -> Response:
    form = await _form_data(request)
    service = TwilioWhatsAppService()
    if not service.validate_webhook(str(request.url), form, request.headers.get("X-Twilio-Signature")):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
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
    service = TwilioWhatsAppService()
    if not service.validate_webhook(str(request.url), form, request.headers.get("X-Twilio-Signature")):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
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


@router.post("/status", response_model=ChannelReceiptResponse)
async def twilio_status_callback(request: Request) -> ChannelReceiptResponse:
    form = await _form_data(request)
    service = TwilioWhatsAppService()
    if not service.validate_webhook(str(request.url), form, request.headers.get("X-Twilio-Signature")):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    channel = "whatsapp" if (
        _first(form, "To").startswith("whatsapp:")
        or _first(form, "From").startswith("whatsapp:")
    ) else "sms"
    return ChannelReceiptService().save_receipt(
        ChannelReceiptRequest(
            provider="twilio",
            channel=channel,
            provider_message_id=_first(form, "MessageSid") or _first(form, "SmsSid") or None,
            message_id=_first(form, "MessageSid") or _first(form, "SmsSid") or None,
            phone=service.clean_channel_phone(_first(form, "To") or _first(form, "From")),
            status=_first(form, "MessageStatus") or _first(form, "SmsStatus") or "unknown",
            event_type="twilio_status_callback",
            raw_payload=form,
        ),
        channel=channel,
    )


@router.get("/media/{media_id}")
def twilio_media(media_id: str) -> Response:
    media = twilio_media_store.get(media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return Response(
        content=media.content,
        media_type=media.content_type,
        headers={"Content-Disposition": f'inline; filename="{media.filename}"'},
    )


@router.get("/media/gcs/{blob_path:path}")
def twilio_gcs_media(blob_path: str) -> Response:
    bucket_name = settings.twilio_media_bucket or settings.storage_bucket
    if not bucket_name:
        raise HTTPException(status_code=404, detail="Media bucket not configured")
    try:
        from google.cloud import storage

        blob = storage.Client(project=settings.google_cloud_project).bucket(bucket_name).blob(blob_path)
        if not blob.exists():
            raise HTTPException(status_code=404, detail="Media not found")
        content = blob.download_as_bytes()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Media fetch failed: {exc}") from exc
    content_type = blob.content_type or "application/octet-stream"
    filename = blob_path.rsplit("/", 1)[-1] or "reply.bin"
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


async def _form_data(request: Request) -> dict[str, str]:
    body = (await request.body()).decode("utf-8")
    parsed = parse_qs(body, keep_blank_values=True)
    return {key: values[-1] for key, values in parsed.items()}


def _first(form: dict[str, str], key: str) -> str:
    return (form.get(key) or "").strip()


def _clean_channel_phone(value: str) -> str:
    return value.removeprefix("whatsapp:").strip()


def _messaging_twiml(message: str) -> Response:
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escape(message)}</Message></Response>'
    return Response(content=xml, media_type="text/xml")


def _record_twilio_followup_audits(farmer_id: str | None, phone: str, results) -> None:
    audit = ServiceAuditLogService()
    for result in results:
        audit.record(
            farmer_id=farmer_id,
            channel="whatsapp",
            service="channel_delivery",
            operation=result.operation or "send_twilio_whatsapp_followup",
            provider=result.provider,
            success=result.status in {"sent", "delivered", "queued", "accepted", "sending", "scheduled", "dry_run"},
            request_body={
                "phone": phone,
                "channel": "whatsapp",
                "dryRun": result.dry_run,
                "followup": True,
            },
            response_body={
                "status": result.status,
                "sent": result.sent,
                "providerMessageId": result.provider_message_id,
                "accepted": (result.metadata or {}).get("accepted"),
            },
            error=result.error,
        )


def _voice_twiml(message: str, *, language: str) -> Response:
    safe_message = escape(message)
    safe_language = escape(language)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Gather input="speech dtmf" action="/api/v1/twilio/voice" method="POST" language="{safe_language}">'
        f"<Say>{safe_message}</Say>"
        "</Gather>"
        f"<Say>{safe_message}</Say>"
        "</Response>"
    )
    return Response(content=xml, media_type="text/xml")
