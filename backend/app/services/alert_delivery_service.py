import json
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.models.schemas import (
    AlertDeliveryRequest,
    AlertDeliveryResponse,
    ChannelDeliveryResult,
    ConversationRole,
    FarmerResponse,
    ProviderFeature,
    ProviderName,
)
from app.repositories.store import store
from app.services.providers.authkey_client import AuthkeyClient, AuthkeyResult
from app.services.twilio_whatsapp_service import TwilioWhatsAppService


class AlertDeliveryService:
    def deliver(self, farmer: FarmerResponse, payload: AlertDeliveryRequest) -> AlertDeliveryResponse:
        results = [self._deliver_channel(farmer, channel, payload) for channel in payload.alert_plan.channels]
        return AlertDeliveryResponse(
            farmer_id=farmer.id,
            priority=payload.alert_plan.priority,
            message=payload.message,
            results=results,
            overall_status=self._overall_status(results),
        )

    def _deliver_channel(self, farmer: FarmerResponse, channel: str, payload: AlertDeliveryRequest) -> ChannelDeliveryResult:
        if channel == "whatsapp":
            return self._send_whatsapp(farmer, payload)
        if channel == "sms":
            return self._send_sms(farmer.phone, payload.message)
        if channel == "voice_call":
            return self._send_voice_call(farmer.phone, payload.message)
        return ChannelDeliveryResult(channel=channel, status="unsupported_channel")

    def _send_whatsapp(self, farmer: FarmerResponse, payload: AlertDeliveryRequest) -> ChannelDeliveryResult:
        route = store.get_provider_route(ProviderFeature.whatsapp)
        if not route.enabled:
            return ChannelDeliveryResult(channel="whatsapp", provider=str(route.primary), status="provider_disabled")
        if route.primary != ProviderName.twilio:
            return ChannelDeliveryResult(channel="whatsapp", provider=str(route.primary), status="unsupported_provider")
        return self._send_twilio_whatsapp(farmer, payload)

    def _send_twilio_whatsapp(self, farmer: FarmerResponse, payload: AlertDeliveryRequest) -> ChannelDeliveryResult:
        content_sid = settings.twilio_content_sid
        if payload.requires_whatsapp_template and not content_sid and not self._has_active_whatsapp_session(farmer.id):
            return ChannelDeliveryResult(
                channel="whatsapp",
                provider="twilio",
                operation="send_twilio_whatsapp_template",
                status="skipped_no_twilio_template",
                retryable=False,
                metadata={"templateRequired": True},
            )
        return TwilioWhatsAppService().send_whatsapp(
            to_phone=farmer.phone,
            body=payload.message,
            media_url=payload.media_url if not content_sid else None,
            content_sid=content_sid,
            content_variables=(
                self._twilio_content_variables(
                    payload.message,
                    media_url=payload.media_url,
                    media_file_name=payload.media_file_name,
                )
                if content_sid
                else None
            ),
            dry_run=not settings.twilio_enable_live_send,
        )

    def _has_active_whatsapp_session(self, farmer_id: str) -> bool:
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        return any(
            message.role == ConversationRole.farmer
            and message.channel == "whatsapp"
            and message.created_at >= cutoff
            for message in store.list_conversation_messages(farmer_id, limit=50)
        )

    def _send_sms(self, phone: str, message: str) -> ChannelDeliveryResult:
        route = store.get_provider_route(ProviderFeature.sms_voice)
        if not route.enabled:
            return ChannelDeliveryResult(channel="sms", provider=str(route.primary), status="provider_disabled")
        if route.primary != ProviderName.authkey:
            return ChannelDeliveryResult(channel="sms", provider=str(route.primary), status="unsupported_provider")
        if not settings.authkey_api_key:
            return ChannelDeliveryResult(channel="sms", provider="authkey", status="skipped_no_authkey")
        if not settings.authkey_sms_sender:
            return ChannelDeliveryResult(channel="sms", provider="authkey", status="skipped_no_sender")

        result = AuthkeyClient(settings.authkey_api_key).send_sms(
            mobile=phone,
            country_code=settings.authkey_test_country_code,
            sms=message,
            sender=settings.authkey_sms_sender,
            dry_run=not settings.authkey_send_enabled,
        )
        return self._from_authkey("sms", result)

    def _send_voice_call(self, phone: str, message: str) -> ChannelDeliveryResult:
        route = store.get_provider_route(ProviderFeature.sms_voice)
        if not route.enabled:
            return ChannelDeliveryResult(channel="voice_call", provider=str(route.primary), status="provider_disabled")
        if route.primary != ProviderName.authkey:
            return ChannelDeliveryResult(channel="voice_call", provider=str(route.primary), status="unsupported_provider")
        if not settings.authkey_api_key:
            return ChannelDeliveryResult(channel="voice_call", provider="authkey", status="skipped_no_authkey")

        client = AuthkeyClient(settings.authkey_api_key)
        if settings.authkey_sms_sender:
            result = client.send_voice_with_sms_fallback(
                mobile=phone,
                country_code=settings.authkey_test_country_code,
                voice=message,
                fallback_sms=message,
                sender=settings.authkey_sms_sender,
                dry_run=not settings.authkey_send_enabled,
            )
        else:
            result = client.send_voice(
                mobile=phone,
                country_code=settings.authkey_test_country_code,
                voice=message,
                dry_run=not settings.authkey_send_enabled,
            )
        return self._from_authkey("voice_call", result)

    def _from_authkey(self, channel: str, result: AuthkeyResult) -> ChannelDeliveryResult:
        if result.dry_run:
            status = "dry_run"
        elif result.sent:
            status = "sent"
        else:
            status = "failed"
        return ChannelDeliveryResult(
            channel=channel,
            provider=result.provider,
            operation=result.operation,
            status=status,
            sent=result.sent,
            dry_run=result.dry_run,
            retryable=status == "failed",
            raw_status=result.response_text,
            metadata={
                "httpStatus": result.status_code,
                "method": result.method,
            },
            error=result.error,
        )

    def _twilio_content_variables(
        self,
        message: str,
        *,
        media_url: str | None = None,
        media_file_name: str | None = None,
    ) -> dict[str, str]:
        replacements = {
            "{message}": message,
            "{media_url}": media_url or "",
            "{media_file_name}": media_file_name or "",
        }
        if not settings.twilio_content_variables:
            variables = {"1": message}
            if media_url:
                variables["2"] = media_url
            if media_file_name:
                variables["3"] = media_file_name
            return variables
        try:
            parsed = json.loads(settings.twilio_content_variables)
        except json.JSONDecodeError:
            return {"1": message}
        if not isinstance(parsed, dict):
            return {"1": message}
        return {
            str(key): self._replace_twilio_template_vars(str(value), replacements)
            for key, value in parsed.items()
        }

    def _replace_twilio_template_vars(self, value: str, replacements: dict[str, str]) -> str:
        for token, replacement in replacements.items():
            value = value.replace(token, replacement)
        return value

    def _overall_status(self, results: list[ChannelDeliveryResult]) -> str:
        if any(result.sent for result in results):
            return "sent"
        if results and all(result.dry_run for result in results):
            return "dry_run"
        if any(result.status in {"accepted", "queued", "sending"} for result in results):
            return "accepted"
        if any(result.status.startswith("skipped") for result in results):
            return "partial_or_skipped"
        if any(result.status == "failed" for result in results):
            return "failed"
        return "not_sent"
