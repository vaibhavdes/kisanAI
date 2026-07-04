from common import optional_env, print_ok, require_env, require_package

require_package("requests", "pip install -r requirements.txt")

from app.services.providers.authkey_client import AuthkeyClient


def enabled(name: str) -> bool:
    return (optional_env(name, "false") or "").strip().lower() in {"1", "true", "yes", "on"}


authkey = require_env("AUTHKEY_API_KEY")
mobile = require_env("AUTHKEY_TEST_MOBILE")
country_code = optional_env("AUTHKEY_TEST_COUNTRY_CODE", "91") or "91"
sender = optional_env("AUTHKEY_SMS_SENDER", "KISAN") or "KISAN"
template_id = optional_env("AUTHKEY_WHATSAPP_TEMPLATE_ID", "101") or "101"
media_template_id = optional_env("AUTHKEY_WHATSAPP_MEDIA_TEMPLATE_ID", template_id) or template_id
send_enabled = enabled("AUTHKEY_SEND_ENABLED")

client = AuthkeyClient(authkey)
message = "KISAN-AI test alert: heavy rain expected. Avoid spraying today."
voice_message = "KISAN AI test call. Heavy rain is expected. Avoid spraying today."

results = [
    client.send_sms(
        mobile=mobile,
        country_code=country_code,
        sms=message,
        sender=sender,
        dry_run=not send_enabled,
    ),
    client.send_voice(
        mobile=mobile,
        country_code=country_code,
        voice=voice_message,
        dry_run=not send_enabled,
    ),
    client.send_parallel_sms_voice(
        mobile=mobile,
        country_code=country_code,
        sms=message,
        voice=voice_message,
        sender=sender,
        dry_run=not send_enabled,
    ),
    client.send_voice_with_sms_fallback(
        mobile=mobile,
        country_code=country_code,
        voice=voice_message,
        fallback_sms=message,
        sender=sender,
        dry_run=not send_enabled,
    ),
    client.send_whatsapp_template_get(
        mobile=mobile,
        country_code=country_code,
        template_id=template_id,
        body_values={"1": "Vaibhav", "2": "Heavy rain alert"},
        dry_run=not send_enabled,
    ),
    client.send_whatsapp_template_json(
        mobile=mobile,
        country_code=country_code,
        template_id=template_id,
        body_values={"1": "Vaibhav", "2": "Heavy rain alert"},
        dry_run=not send_enabled,
    ),
    client.send_whatsapp_media_template_get(
        mobile=mobile,
        country_code=country_code,
        template_id=media_template_id,
        header_file_name="KisanAlert",
        header_data_url="https://www.gstatic.com/webp/gallery/1.jpg",
        dry_run=not send_enabled,
    ),
    client.send_whatsapp_bulk_template_json(
        mobiles=[mobile],
        country_code=country_code,
        template_id=template_id,
        body_values={"1": "Vaibhav"},
        dry_run=not send_enabled,
    ),
]

failed = [result for result in results if send_enabled and not result.sent]
if failed:
    details = "; ".join(f"{item.operation}: {item.status_code} {item.error}" for item in failed)
    raise RuntimeError(f"Authkey send scenario failed: {details}")

mode = "real send" if send_enabled else "dry-run build"
operations = ", ".join(result.operation for result in results)
print_ok(f"Authkey {mode} scenarios covered: {operations}")
