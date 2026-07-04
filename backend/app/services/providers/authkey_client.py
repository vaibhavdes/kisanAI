from dataclasses import dataclass, field
from typing import Any

import requests


@dataclass(frozen=True)
class AuthkeyResult:
    provider: str
    channel: str
    operation: str
    sent: bool
    dry_run: bool
    method: str
    url: str
    status_code: int | None = None
    response_text: str | None = None
    payload: dict[str, Any] | None = None
    params: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class AuthkeyClient:
    request_base_url = "https://api.authkey.io/request"
    rest_base_url = "https://console.authkey.io/restapi"

    def __init__(
        self,
        authkey: str,
        *,
        timeout_seconds: int = 20,
        session: requests.Session | None = None,
    ) -> None:
        self.authkey = authkey
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    def get_balance(self) -> AuthkeyResult:
        url = f"{self.rest_base_url}/getbalance.php"
        return self._get("account", "balance", url, {"authkey": self.authkey}, dry_run=False)

    def send_sms(
        self,
        *,
        mobile: str,
        country_code: str,
        sms: str,
        sender: str,
        dry_run: bool = True,
    ) -> AuthkeyResult:
        params = {
            "authkey": self.authkey,
            "mobile": mobile,
            "country_code": country_code,
            "sms": sms,
            "sender": sender,
        }
        return self._get("sms", "send_sms", self.request_base_url, params, dry_run=dry_run)

    def send_voice(
        self,
        *,
        mobile: str,
        country_code: str,
        voice: str,
        dry_run: bool = True,
    ) -> AuthkeyResult:
        params = {
            "authkey": self.authkey,
            "mobile": mobile,
            "country_code": country_code,
            "voice": voice,
        }
        return self._get("voice", "send_voice", self.request_base_url, params, dry_run=dry_run)

    def send_parallel_sms_voice(
        self,
        *,
        mobile: str,
        country_code: str,
        sms: str,
        voice: str,
        sender: str,
        dry_run: bool = True,
    ) -> AuthkeyResult:
        params = {
            "authkey": self.authkey,
            "mobile": mobile,
            "country_code": country_code,
            "sms": sms,
            "voice": voice,
            "sender": sender,
        }
        return self._get("multi", "send_parallel_sms_voice", self.request_base_url, params, dry_run=dry_run)

    def send_voice_with_sms_fallback(
        self,
        *,
        mobile: str,
        country_code: str,
        voice: str,
        fallback_sms: str,
        sender: str,
        dry_run: bool = True,
    ) -> AuthkeyResult:
        params = {
            "authkey": self.authkey,
            "mobile": mobile,
            "country_code": country_code,
            "voice": voice,
            "sender": sender,
            "fb1sms": fallback_sms,
        }
        return self._get("multi", "send_voice_with_sms_fallback", self.request_base_url, params, dry_run=dry_run)

    def send_whatsapp_template_get(
        self,
        *,
        mobile: str,
        country_code: str,
        template_id: str,
        body_values: dict[str, str] | None = None,
        dry_run: bool = True,
    ) -> AuthkeyResult:
        params: dict[str, Any] = {
            "authkey": self.authkey,
            "mobile": mobile,
            "country_code": country_code,
            "wid": template_id,
        }
        params.update(body_values or {})
        return self._get("whatsapp", "send_whatsapp_template_get", self.request_base_url, params, dry_run=dry_run)

    def send_whatsapp_media_template_get(
        self,
        *,
        mobile: str,
        country_code: str,
        template_id: str,
        header_data_url: str,
        header_file_name: str | None = None,
        dry_run: bool = True,
    ) -> AuthkeyResult:
        params: dict[str, Any] = {
            "authkey": self.authkey,
            "mobile": mobile,
            "country_code": country_code,
            "wid": template_id,
            "template_type": "media",
            "headerData": header_data_url,
        }
        if header_file_name:
            params["headerFileName"] = header_file_name
        return self._get(
            "whatsapp",
            "send_whatsapp_media_template_get",
            f"{self.rest_base_url}/request.php",
            params,
            dry_run=dry_run,
        )

    def send_whatsapp_template_json(
        self,
        *,
        mobile: str,
        country_code: str,
        template_id: str,
        body_values: dict[str, str] | None = None,
        header_values: dict[str, str] | None = None,
        template_type: str = "text",
        dry_run: bool = True,
    ) -> AuthkeyResult:
        payload: dict[str, Any] = {
            "country_code": country_code,
            "mobile": mobile,
            "wid": template_id,
            "type": template_type,
        }
        if body_values:
            payload["bodyValues"] = body_values
        if header_values:
            payload["headerValues"] = header_values
        return self._post_json(
            "whatsapp",
            "send_whatsapp_template_json",
            f"{self.rest_base_url}/requestjson.php",
            payload,
            dry_run=dry_run,
        )

    def send_whatsapp_bulk_template_json(
        self,
        *,
        mobiles: list[str],
        country_code: str,
        template_id: str,
        template_type: str = "text",
        body_values: dict[str, str] | None = None,
        dry_run: bool = True,
    ) -> AuthkeyResult:
        data: list[dict[str, Any]] = []
        for mobile in mobiles[:200]:
            row: dict[str, Any] = {"mobile": mobile}
            if body_values:
                row["bodyValues"] = body_values
            data.append(row)

        payload = {
            "version": "2.0",
            "country_code": country_code,
            "wid": template_id,
            "type": template_type,
            "data": data,
        }
        return self._post_json(
            "whatsapp",
            "send_whatsapp_bulk_template_json",
            f"{self.rest_base_url}/requestjson_v2.0.php",
            payload,
            dry_run=dry_run,
        )

    def _get(
        self,
        channel: str,
        operation: str,
        url: str,
        params: dict[str, Any],
        *,
        dry_run: bool,
    ) -> AuthkeyResult:
        safe_params = self._safe_params(params)
        if dry_run:
            return AuthkeyResult(
                provider="authkey",
                channel=channel,
                operation=operation,
                sent=False,
                dry_run=True,
                method="GET",
                url=url,
                params=safe_params,
            )

        try:
            response = self.session.get(url, params=params, timeout=self.timeout_seconds)
        except requests.RequestException as exc:
            return AuthkeyResult(
                provider="authkey",
                channel=channel,
                operation=operation,
                sent=False,
                dry_run=False,
                method="GET",
                url=url,
                params=safe_params,
                error=str(exc),
            )

        return AuthkeyResult(
            provider="authkey",
            channel=channel,
            operation=operation,
            sent=response.ok,
            dry_run=False,
            method="GET",
            url=url,
            status_code=response.status_code,
            response_text=response.text[:500],
            params=safe_params,
            error=None if response.ok else response.text[:500],
        )

    def _post_json(
        self,
        channel: str,
        operation: str,
        url: str,
        payload: dict[str, Any],
        *,
        dry_run: bool,
    ) -> AuthkeyResult:
        if dry_run:
            return AuthkeyResult(
                provider="authkey",
                channel=channel,
                operation=operation,
                sent=False,
                dry_run=True,
                method="POST",
                url=url,
                payload=payload,
            )

        try:
            response = self.session.post(
                url,
                json=payload,
                headers={"Authorization": f"Basic {self.authkey}", "Content-Type": "application/json"},
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            return AuthkeyResult(
                provider="authkey",
                channel=channel,
                operation=operation,
                sent=False,
                dry_run=False,
                method="POST",
                url=url,
                payload=payload,
                error=str(exc),
            )

        return AuthkeyResult(
            provider="authkey",
            channel=channel,
            operation=operation,
            sent=response.ok,
            dry_run=False,
            method="POST",
            url=url,
            status_code=response.status_code,
            response_text=response.text[:500],
            payload=payload,
            error=None if response.ok else response.text[:500],
        )

    def _safe_params(self, params: dict[str, Any]) -> dict[str, Any]:
        return {key: ("***hidden***" if key == "authkey" else value) for key, value in params.items()}
