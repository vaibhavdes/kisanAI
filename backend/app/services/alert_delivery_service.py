import json

from app.core.config import settings
from app.models.schemas import (
    AlertDeliveryRequest,
    AlertDeliveryResponse,
    ChannelDeliveryResult,
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
            return self._send_whatsapp(farmer.phone, payload)
        if channel == "sms":
            return self._send_sms(farmer.phone, payload.message)
        if channel == "voice_call":
            return self._send_voice_call(farmer.phone, payload.message)
        return ChannelDeliveryResult(channel=channel, status="unsupported_channel")

    def _send_whatsapp(self, phone: str, payload: AlertDeliveryRequest) -> ChannelDeliveryResult:
        route = store.get_provider_route(ProviderFeature.whatsapp)
        if not route.enabled:
            return ChannelDeliveryResult(channel="whatsapp", provider=str(route.primary), status="provider_disabled")
        providers = [route.primary]
        if route.allow_fallback and route.secondary:
            providers.append(route.secondary)

        result: ChannelDeliveryResult | None = None
        attempts: list[str] = []
        for provider in providers:
            result = self._send_whatsapp_with_provider(provider, phone, payload)
            if attempts:
                result.metadata = {
                    **result.metadata,
                    "fallback": True,
                    "fallbackFrom": ";".join(attempts),
                }
            if not self._should_try_whatsapp_fallback(result):
                return result
            attempts.append(f"{provider.value}:{result.status}")
        return result or ChannelDeliveryResult(channel="whatsapp", status="unsupported_provider")

    def _send_whatsapp_with_provider(
        self,
        provider: ProviderName,
        phone: str,
        payload: AlertDeliveryRequest,
    ) -> ChannelDeliveryResult:
        if provider == ProviderName.twilio:
            return self._send_twilio_whatsapp(phone, payload)
        if provider == ProviderName.authkey:
            return self._send_authkey_whatsapp(phone, payload)
        return ChannelDeliveryResult(channel="whatsapp", provider=str(provider), status="unsupported_provider")

    def _send_authkey_whatsapp(self, phone: str, payload: AlertDeliveryRequest) -> ChannelDeliveryResult:
        if not settings.authkey_api_key:
            return ChannelDeliveryResult(channel="whatsapp", provider="authkey", status="skipped_no_authkey")
        client = AuthkeyClient(settings.authkey_api_key)
        if payload.media_url and settings.authkey_whatsapp_media_template_id:
            result = client.send_whatsapp_media_template_get(
                mobile=phone,
                country_code=settings.authkey_test_country_code,
                template_id=settings.authkey_whatsapp_media_template_id,
                header_data_url=payload.media_url,
                header_file_name=payload.media_file_name,
                dry_run=not settings.authkey_send_enabled,
            )
        else:
            if not settings.authkey_whatsapp_template_id:
                return ChannelDeliveryResult(channel="whatsapp", provider="authkey", status="skipped_no_template")
            result = client.send_whatsapp_template_get(
                mobile=phone,
                country_code=settings.authkey_test_country_code,
                template_id=settings.authkey_whatsapp_template_id,
                body_values={"message": payload.message},
                dry_run=not settings.authkey_send_enabled,
            )
        return self._from_authkey("whatsapp", result)

    def _send_twilio_whatsapp(self, phone: str, payload: AlertDeliveryRequest) -> ChannelDeliveryResult:
        content_sid = settings.twilio_content_sid
        return TwilioWhatsAppService().send_whatsapp(
            to_phone=phone,
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

    def _should_try_whatsapp_fallback(self, result: ChannelDeliveryResult) -> bool:
        if result.sent or result.dry_run:
            return False
        if result.status in {"accepted", "queued", "sending", "sent", "delivered"}:
            return False
        return result.retryable or result.status.startswith("skipped") or result.status in {
            "failed",
            "unsupported_provider",
        }

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
