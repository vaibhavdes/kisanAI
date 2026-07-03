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
    data_store_provider: str = "firestore"
    firestore_database: str = "(default)"
    bigquery_public_dataset: str = "kisan_ai_curated"
    imd_api_base_url: str | None = None
    imd_api_key: str | None = None
    open_meteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    vertex_ai_model: str = "gemini-2.5-flash"
    storage_bucket: str | None = None
    pubsub_alert_topic: str = "kisan-alerts"
    sms_provider_api_key: str | None = None
    whatsapp_business_token: str | None = None
    voice_call_provider_api_key: str | None = None
    authkey_api_key: str | None = None
    authkey_test_mobile: str | None = None
    authkey_test_country_code: str = "91"
    authkey_sms_sender: str | None = None
    authkey_whatsapp_template_id: str | None = None
    authkey_whatsapp_media_template_id: str | None = None
    authkey_send_enabled: bool = False
    sarvam_api_key: str | None = None
    sarvam_api_base_url: str = "https://api.sarvam.ai"
    sarvam_stt_model: str = "saaras:v3"
    rythu_seva_default_center: str = "RSK Demo Center"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
