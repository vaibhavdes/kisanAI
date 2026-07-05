from app.services.providers.authkey_client import AuthkeyClient


def test_authkey_dry_run_masks_key_and_builds_sms_request() -> None:
    result = AuthkeyClient("secret-key").send_sms(
        mobile="9970000000",
        country_code="91",
        sms="Test alert",
        sender="KISAN",
    )

    assert result.dry_run is True
    assert result.sent is False
    assert result.params["authkey"] == "***hidden***"
    assert result.params["sms"] == "Test alert"


def test_authkey_dry_run_builds_voice_fallback_payload() -> None:
    client = AuthkeyClient("secret-key")

    fallback = client.send_voice_with_sms_fallback(
        mobile="9970000000",
        country_code="91",
        voice="Voice alert",
        fallback_sms="SMS fallback",
        sender="KISAN",
    )

    assert fallback.params["fb1sms"] == "SMS fallback"
    assert fallback.params["authkey"] == "***hidden***"
