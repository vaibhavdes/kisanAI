from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Kisan Alert"
    environment: str = "local"
    default_language: str = "hi-IN"
    enable_google_integrations: bool = False
    google_cloud_project: str | None = None
    gemini_api_key: str | None = None
    sms_provider_api_key: str | None = None
    whatsapp_business_token: str | None = None
    voice_call_provider_api_key: str | None = None
    rythu_seva_default_center: str = "RSK Demo Center"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
