from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Kisan Alert"
    environment: str = "local"
    default_language: str = "hi-IN"
    enable_google_integrations: bool = False
    google_cloud_project: str | None = None
    google_cloud_location: str = "global"
    gcp_region: str = "asia-south1"
    vertex_ai_location: str | None = None
    speech_location: str = "global"
    translation_location: str = "global"
    data_store_provider: str = "firestore"
    firestore_database: str = "(default)"
    bigquery_public_dataset: str = "kisan_ai_curated"
    imd_api_base_url: str | None = None
    imd_api_key: str | None = None
    open_meteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    maps_api_key: str | None = None
    geocoding_request_timeout_seconds: int = 15
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    vertex_ai_model: str = "gemini-2.5-flash"
    gemini_fallback_models: str = "gemini-2.5-flash"
    vertex_ai_fallback_models: str = "gemini-2.5-flash"
    gemini_live_model: str = "gemini-3.1-flash-live-preview"
    storage_bucket: str | None = None
    pubsub_alert_topic: str = "kisan-alerts"
    dialogflow_routing_enabled: bool = False
    dialogflow_agent_id: str | None = None
    dialogflow_location: str | None = None
    dialogflow_environment_id: str | None = None
    dialogflow_confidence_threshold: float = 0.45
    sms_provider_api_key: str | None = None
    whatsapp_business_token: str | None = None
    voice_call_provider_api_key: str | None = None
    authkey_api_key: str | None = None
    authkey_test_mobile: str | None = None
    authkey_test_country_code: str = "91"
    authkey_sms_sender: str | None = None
    authkey_send_enabled: bool = False
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_whatsapp_from: str = "whatsapp:+14155238886"
    twilio_messaging_service_sid: str | None = None
    twilio_content_sid: str | None = None
    twilio_content_variables: str | None = None
    twilio_status_callback_url: str | None = None
    twilio_public_base_url: str | None = None
    twilio_media_bucket: str | None = None
    twilio_media_public_base_url: str | None = None
    twilio_media_signed_url_minutes: int = 15
    twilio_media_memory_ttl_seconds: int = 600
    twilio_validate_webhooks: bool = False
    twilio_enable_live_send: bool = False
    sarvam_api_key: str | None = None
    sarvam_api_base_url: str = "https://api.sarvam.ai"
    sarvam_stt_model: str = "saaras:v3"
    sarvam_translate_model: str = "mayura:v1"
    rythu_seva_default_center: str = "RSK Demo Center"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
