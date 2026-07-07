import base64
import json
from binascii import Error as BinasciiError
from dataclasses import dataclass
from datetime import timedelta
from html import escape
from secrets import token_urlsafe
from time import time
from typing import Any
from urllib.parse import quote, urlencode, urlsplit, urlunsplit

import requests

from app.core.config import settings
from app.models.schemas import ChannelDeliveryResult, WhatsAppWebhookRequest, WhatsAppWebhookResponse
from app.utils.phone import normalize_phone


@dataclass(frozen=True)
class StoredTwilioMedia:
    content: bytes
    content_type: str
    filename: str
    created_at: float


class TwilioMediaStore:
    def __init__(self) -> None:
        self._items: dict[str, StoredTwilioMedia] = {}

    def save_base64(self, audio_base64: str, content_type: str) -> str:
        return self.save_bytes(base64.b64decode(audio_base64, validate=True), content_type)

    def save_bytes(self, content: bytes, content_type: str) -> str:
        self._prune_expired()
        media_id = token_urlsafe(18)
        extension = self._extension(content_type)
        self._items[media_id] = StoredTwilioMedia(
            content=content,
            content_type=content_type,
            filename=f"reply.{extension}",
            created_at=time(),
        )
        return media_id

    def get(self, media_id: str) -> StoredTwilioMedia | None:
        self._prune_expired()
        return self._items.get(media_id)

    def _prune_expired(self) -> None:
        ttl_seconds = max(settings.twilio_media_memory_ttl_seconds, 60)
        expires_before = time() - ttl_seconds
        for media_id, media in list(self._items.items()):
            if media.created_at < expires_before:
                self._items.pop(media_id, None)

    def _extension(self, content_type: str) -> str:
        normalized = content_type.split(";", 1)[0].strip().lower()
        if normalized == "audio/mpeg":
            return "mp3"
        if normalized == "audio/ogg":
            return "ogg"
        if normalized == "audio/wav":
            return "wav"
        return "bin"


twilio_media_store = TwilioMediaStore()


class TwilioWhatsAppService:
    def validate_webhook(self, url: str, form: dict[str, str], signature: str | None) -> bool:
        if not settings.twilio_validate_webhooks:
            return True
        if not settings.twilio_auth_token or not signature:
            return False
        try:
            from twilio.request_validator import RequestValidator
        except ImportError:
            return False
        validator = RequestValidator(settings.twilio_auth_token)
        return any(validator.validate(candidate, form, signature) for candidate in self._validation_urls(url))

    def inbound_payload(self, form: dict[str, str]) -> WhatsAppWebhookRequest:
        media = self._first_media(form)
        latitude = self._float_or_none(form.get("Latitude"))
        longitude = self._float_or_none(form.get("Longitude"))
        text = self._text(form)
        media_type = self._media_type(media.content_type if media else None)

        payload: dict[str, Any] = {
            "from_phone": self.clean_channel_phone(form.get("From", "")),
            "message_id": form.get("MessageSid") or form.get("SmsMessageSid"),
            "text": text,
            "media_mime_type": media.content_type if media and media_type != "audio" else None,
            "media_type": media_type,
            "latitude": latitude,
            "longitude": longitude,
            "location_label": form.get("Label") or form.get("Address"),
            "language": form.get("Language") or None,
        }
        if media:
            if media_type == "audio":
                payload["audio_uri"] = media.url
                payload["audio_mime_type"] = media.content_type or "audio/ogg"
            else:
                payload["media_uri"] = media.url
        return WhatsAppWebhookRequest(**payload)

    def twiml_response(
        self,
        response: WhatsAppWebhookResponse,
        *,
        base_url: str,
        status_callback_url: str | None,
    ) -> str:
        return self.messaging_twiml(
            body=response.reply,
            status_callback_url=status_callback_url,
        )

    def send_response_media_followups(
        self,
        *,
        to_phone: str,
        response: WhatsAppWebhookResponse,
        base_url: str,
        dry_run: bool,
    ) -> list[ChannelDeliveryResult]:
        media_items = []
        if response.media_url:
            media_items.append(("Farm health image", response.media_url))
        audio_url = self._response_audio_url(response, base_url=base_url)
        if audio_url:
            media_items.append(("Voice reply", audio_url))
        return [
            self.send_whatsapp(
                to_phone=to_phone,
                body=caption,
                media_url=url,
                dry_run=dry_run,
            )
            for caption, url in media_items
        ]

    def messaging_twiml(
        self,
        *,
        body: str,
        media_url: str | None = None,
        media_urls: list[str] | None = None,
        status_callback_url: str | None = None,
    ) -> str:
        attrs = ""
        if status_callback_url:
            safe_callback = escape(status_callback_url, quote=True)
            attrs = f' statusCallback="{safe_callback}"'
        all_media_urls = media_urls or ([media_url] if media_url else [])
        if all_media_urls:
            # WhatsApp can drop body text when media is attached, so each payload is a separate reply.
            media_messages = "".join(
                f"<Message{attrs}><Media>{escape(url)}</Media></Message>" for url in all_media_urls if url
            )
            return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message{attrs}>{escape(body)}</Message>{media_messages}</Response>'
        return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message{attrs}>{escape(body)}</Message></Response>'

    def send_whatsapp(
        self,
        *,
        to_phone: str,
        body: str,
        media_url: str | None = None,
        content_sid: str | None = None,
        content_variables: dict[str, str] | None = None,
        persistent_action: str | None = None,
        dry_run: bool = True,
    ) -> ChannelDeliveryResult:
        payload = self._message_payload(
            to_phone=to_phone,
            body=body,
            media_url=media_url,
            content_sid=content_sid,
            content_variables=content_variables,
            persistent_action=persistent_action,
        )
        if dry_run:
            content_variable_keys = ",".join(sorted((content_variables or {}).keys()))
            return ChannelDeliveryResult(
                channel="whatsapp",
                provider="twilio",
                operation=self._operation(payload),
                status="dry_run",
                dry_run=True,
                metadata={
                    "method": "POST",
                    "to": payload.get("To"),
                    "from": payload.get("From") or payload.get("MessagingServiceSid"),
                    "hasMedia": bool(media_url),
                    "hasContentTemplate": bool(content_sid),
                    "contentVariableKeys": content_variable_keys or None,
                },
            )

        if not settings.twilio_account_sid or not settings.twilio_auth_token:
            return ChannelDeliveryResult(
                channel="whatsapp",
                provider="twilio",
                operation=self._operation(payload),
                status="skipped_no_twilio_credentials",
                retryable=True,
            )

        try:
            response = requests.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json",
                data=payload,
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            response_text = exc.response.text[:800] if exc.response is not None else None
            return ChannelDeliveryResult(
                channel="whatsapp",
                provider="twilio",
                operation=self._operation(payload),
                status="failed",
                retryable=True,
                metadata={"method": "POST", "httpStatus": status_code},
                raw_status=response_text,
                error=response_text or str(exc),
            )

        status = str(data.get("status") or "accepted")
        sent = status in {"sent", "delivered"}
        accepted = sent or status in {"accepted", "queued", "sending", "scheduled"}
        error_message = data.get("error_message") or data.get("message")
        return ChannelDeliveryResult(
            channel="whatsapp",
            provider="twilio",
            operation=self._operation(payload),
            status=status,
            sent=sent,
            provider_message_id=data.get("sid"),
            retryable=not accepted,
            raw_status=json.dumps({key: data.get(key) for key in ["sid", "status", "error_code", "error_message"]}),
            metadata={"method": "POST", "accepted": accepted},
            error=str(error_message) if error_message else None,
        )

    def status_callback_url(self, base_url: str) -> str | None:
        if settings.twilio_status_callback_url:
            return settings.twilio_status_callback_url
        if settings.twilio_public_base_url:
            return f"{settings.twilio_public_base_url.rstrip('/')}/api/v1/twilio/status"
        if base_url:
            return f"{base_url.rstrip('/')}/api/v1/twilio/status"
        return None

    def public_base_url(self, request_base_url: str) -> str:
        return (settings.twilio_public_base_url or request_base_url).rstrip("/")

    def _validation_urls(self, request_url: str) -> list[str]:
        urls = [request_url]
        if not settings.twilio_public_base_url:
            return urls

        request_parts = urlsplit(request_url)
        public_parts = urlsplit(settings.twilio_public_base_url)
        if not public_parts.scheme or not public_parts.netloc:
            return urls

        public_path = public_parts.path.rstrip("/")
        request_path = request_parts.path
        if public_path and request_path.startswith(public_path):
            canonical_path = request_path
        else:
            canonical_path = f"{public_path}{request_path}"
        canonical = urlunsplit(
            (
                public_parts.scheme,
                public_parts.netloc,
                canonical_path,
                request_parts.query,
                "",
            )
        )
        if canonical not in urls:
            urls.insert(0, canonical)
        return urls

    def clean_channel_phone(self, value: str) -> str:
        return value.removeprefix("whatsapp:").strip()

    def _message_payload(
        self,
        *,
        to_phone: str,
        body: str,
        media_url: str | None,
        content_sid: str | None,
        content_variables: dict[str, str] | None,
        persistent_action: str | None,
    ) -> dict[str, str]:
        payload = {
            "To": self._whatsapp_phone(to_phone),
            "StatusCallback": self.status_callback_url(settings.twilio_public_base_url or ""),
        }
        if settings.twilio_messaging_service_sid:
            payload["MessagingServiceSid"] = settings.twilio_messaging_service_sid
        else:
            payload["From"] = settings.twilio_whatsapp_from
        if content_sid:
            payload["ContentSid"] = content_sid
            if content_variables:
                payload["ContentVariables"] = json.dumps(content_variables)
        else:
            payload["Body"] = body
            if media_url:
                payload["MediaUrl"] = media_url
            if persistent_action:
                payload["PersistentAction"] = persistent_action
        return {key: value for key, value in payload.items() if value}

    def _whatsapp_phone(self, value: str) -> str:
        if value.startswith("whatsapp:"):
            return value
        normalized = normalize_phone(value)
        return f"whatsapp:+{normalized}"

    def _operation(self, payload: dict[str, str]) -> str:
        if "ContentSid" in payload:
            return "send_twilio_whatsapp_template"
        if "MediaUrl" in payload:
            return "send_twilio_whatsapp_media"
        if "PersistentAction" in payload:
            return "send_twilio_whatsapp_location"
        return "send_twilio_whatsapp_text"

    def _response_audio_url(self, response: WhatsAppWebhookResponse, *, base_url: str) -> str | None:
        if not response.response_audio_base64 or not response.response_audio_content_type:
            return None
        try:
            content = base64.b64decode(response.response_audio_base64, validate=True)
        except (BinasciiError, ValueError):
            return None
        content_type = self._clean_audio_content_type(response.response_audio_content_type)
        public_url = self._publish_response_media(content, content_type, base_url=base_url)
        if public_url:
            return public_url
        if not base_url:
            return None
        return self._memory_media_url(content, content_type, base_url=base_url)

    def _clean_audio_content_type(self, content_type: str) -> str:
        normalized = content_type.split(";", 1)[0].strip().lower()
        if normalized in {"audio/mpeg", "audio/mp3"}:
            return "audio/mpeg"
        if normalized in {"audio/ogg", "audio/opus"}:
            return "audio/ogg"
        if normalized in {"audio/wav", "audio/wave", "audio/x-wav"}:
            return "audio/wav"
        return normalized or "audio/mpeg"

    def _publish_response_media(self, content: bytes, content_type: str, *, base_url: str) -> str | None:
        bucket_name = settings.twilio_media_bucket or settings.storage_bucket
        if not bucket_name:
            return None
        try:
            from google.cloud import storage

            extension = twilio_media_store._extension(content_type)
            blob_name = f"twilio/replies/{token_urlsafe(18)}.{extension}"
            bucket = storage.Client(project=settings.google_cloud_project).bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.upload_from_string(content, content_type=content_type)
            if settings.twilio_media_public_base_url:
                return f"{settings.twilio_media_public_base_url.rstrip('/')}/{quote(blob_name, safe='/')}"
            if base_url:
                return f"{base_url.rstrip('/')}/api/v1/twilio/media/gcs/{quote(blob_name, safe='/')}"
            return blob.generate_signed_url(
                expiration=timedelta(minutes=max(settings.twilio_media_signed_url_minutes, 1)),
                method="GET",
            )
        except Exception:
            return None

    def _memory_media_url(self, content: bytes, content_type: str, *, base_url: str) -> str:
        media_id = twilio_media_store.save_bytes(content, content_type)
        media = twilio_media_store.get(media_id)
        filename = media.filename if media else f"reply.{twilio_media_store._extension(content_type)}"
        query = urlencode({"filename": filename})
        return f"{base_url.rstrip('/')}/api/v1/twilio/media/{media_id}?{query}"

    def _text(self, form: dict[str, str]) -> str | None:
        return form.get("Body") or form.get("ButtonText") or None

    @dataclass(frozen=True)
    class _InboundMedia:
        url: str
        content_type: str | None

    def _first_media(self, form: dict[str, str]) -> _InboundMedia | None:
        try:
            count = int(form.get("NumMedia") or 0)
        except ValueError:
            count = 0
        if count <= 0 and not form.get("MediaUrl0"):
            return None
        url = form.get("MediaUrl0")
        if not url:
            return None
        return self._InboundMedia(url=url, content_type=form.get("MediaContentType0"))

    def _media_type(self, content_type: str | None) -> str | None:
        if not content_type:
            return None
        lowered = content_type.lower()
        if lowered.startswith("image/"):
            return "image"
        if lowered.startswith("audio/"):
            return "audio"
        return "document"

    def _float_or_none(self, value: str | None) -> float | None:
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None
