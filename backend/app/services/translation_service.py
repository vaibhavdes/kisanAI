import requests

from app.core.config import settings
from app.models.schemas import (
    DetectLanguageRequest,
    DetectLanguageResponse,
    ProviderFeature,
    ProviderName,
    TranslateTextRequest,
    TranslateTextResponse,
)
from app.repositories.store import store


class TranslationProviderUnavailable(RuntimeError):
    pass


class TranslationService:
    def translate(self, payload: TranslateTextRequest) -> TranslateTextResponse:
        errors: list[str] = []
        for provider in self._provider_order():
            try:
                if provider == ProviderName.google_translate:
                    return self._translate_with_google(payload)
                if provider == ProviderName.sarvam_translate:
                    return self._translate_with_sarvam(payload)
            except Exception as exc:
                errors.append(f"{provider.value}:{exc.__class__.__name__}:{exc}")
        raise TranslationProviderUnavailable("; ".join(errors) or "No translation provider is configured.")

    def detect_language(self, payload: DetectLanguageRequest) -> DetectLanguageResponse:
        errors: list[str] = []
        for provider in self._provider_order():
            try:
                if provider == ProviderName.google_translate:
                    return self._detect_with_google(payload)
                if provider == ProviderName.sarvam_translate:
                    return self._detect_with_sarvam(payload)
            except Exception as exc:
                errors.append(f"{provider.value}:{exc.__class__.__name__}:{exc}")
        raise TranslationProviderUnavailable(
            "; ".join(errors) or "No language detection provider is configured."
        )

    def _translate_with_google(self, payload: TranslateTextRequest) -> TranslateTextResponse:
        from google.cloud import translate_v3 as translate

        if not settings.google_cloud_project:
            raise TranslationProviderUnavailable("GOOGLE_CLOUD_PROJECT is required for Google Translate.")

        client = translate.TranslationServiceClient()
        request = {
            "parent": self._google_parent(),
            "contents": [payload.text],
            "mime_type": payload.mime_type,
            "target_language_code": self._google_language(payload.target_language),
        }
        if payload.source_language:
            request["source_language_code"] = self._google_language(payload.source_language)

        response = client.translate_text(request=request)
        if not response.translations:
            raise TranslationProviderUnavailable("Google Translate returned no translations.")
        translation = response.translations[0]
        return TranslateTextResponse(
            translated_text=translation.translated_text,
            source_language=self._bcp47_language(
                translation.detected_language_code or payload.source_language
            ),
            target_language=self._bcp47_language(payload.target_language),
            provider=ProviderName.google_translate.value,
        )

    def _translate_with_sarvam(self, payload: TranslateTextRequest) -> TranslateTextResponse:
        if not settings.sarvam_api_key:
            raise TranslationProviderUnavailable("SARVAM_API_KEY is required for Sarvam Translate.")

        source_language = payload.source_language or "auto"
        response = requests.post(
            f"{settings.sarvam_api_base_url.rstrip('/')}/translate",
            headers={
                "api-subscription-key": settings.sarvam_api_key,
                "Content-Type": "application/json",
            },
            json={
                "input": payload.text,
                "source_language_code": source_language,
                "target_language_code": self._bcp47_language(payload.target_language),
                "model": settings.sarvam_translate_model,
                "mode": "formal",
                "numerals_format": "international",
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        translated_text = str(data.get("translated_text") or "").strip()
        if not translated_text:
            raise TranslationProviderUnavailable("Sarvam Translate returned no translated_text.")
        return TranslateTextResponse(
            translated_text=translated_text,
            source_language=data.get("source_language_code") or payload.source_language,
            target_language=self._bcp47_language(payload.target_language),
            provider=ProviderName.sarvam_translate.value,
        )

    def _detect_with_google(self, payload: DetectLanguageRequest) -> DetectLanguageResponse:
        from google.cloud import translate_v3 as translate

        if not settings.google_cloud_project:
            raise TranslationProviderUnavailable("GOOGLE_CLOUD_PROJECT is required for Google Translate.")

        client = translate.TranslationServiceClient()
        response = client.detect_language(
            request={
                "parent": self._google_parent(),
                "content": payload.text,
                "mime_type": "text/plain",
            }
        )
        if not response.languages:
            raise TranslationProviderUnavailable("Google Translate returned no language detection result.")
        language = response.languages[0]
        return DetectLanguageResponse(
            language=self._bcp47_language(language.language_code),
            script=None,
            provider=ProviderName.google_translate.value,
            confidence=language.confidence,
        )

    def _detect_with_sarvam(self, payload: DetectLanguageRequest) -> DetectLanguageResponse:
        if not settings.sarvam_api_key:
            raise TranslationProviderUnavailable("SARVAM_API_KEY is required for Sarvam language detection.")

        response = requests.post(
            f"{settings.sarvam_api_base_url.rstrip('/')}/text-lid",
            headers={
                "api-subscription-key": settings.sarvam_api_key,
                "Content-Type": "application/json",
            },
            json={"input": payload.text},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return DetectLanguageResponse(
            language=data.get("language_code"),
            script=data.get("script_code"),
            provider=ProviderName.sarvam_translate.value,
            confidence=None,
        )

    def _provider_order(self) -> list[ProviderName]:
        route = store.get_provider_route(ProviderFeature.translation)
        if not route.enabled:
            return []

        providers = [route.primary]
        if route.allow_fallback and route.secondary:
            providers.append(route.secondary)
        return providers

    def _google_parent(self) -> str:
        return f"projects/{settings.google_cloud_project}/locations/{settings.translation_location}"

    def _google_language(self, value: str) -> str:
        return value.split("-", 1)[0].lower()

    def _bcp47_language(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if "-" in normalized:
            lang, region = normalized.split("-", 1)
            return f"{lang.lower()}-{region.upper()}"
        return f"{normalized.lower()}-IN"
