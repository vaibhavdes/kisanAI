from app.models.schemas import (
    ProviderConfigResponse,
    ProviderConfigUpdate,
    ProviderFeature,
    ProviderName,
    ProviderRoute,
)
from app.repositories.store import store


ALLOWED_PROVIDERS: dict[ProviderFeature, set[ProviderName]] = {
    ProviderFeature.weather: {ProviderName.imd, ProviderName.open_meteo},
    ProviderFeature.stt: {ProviderName.google_stt, ProviderName.sarvam_stt},
    ProviderFeature.tts: {ProviderName.google_tts, ProviderName.sarvam_tts},
    ProviderFeature.translation: {ProviderName.google_translate, ProviderName.sarvam_translate},
    ProviderFeature.llm_advisory: {ProviderName.gemini, ProviderName.vertex_ai},
    ProviderFeature.vision_ocr: {ProviderName.gemini_vision, ProviderName.vertex_ai_vision},
    ProviderFeature.satellite: {ProviderName.earth_engine},
    ProviderFeature.geocoding_maps: {ProviderName.google_maps, ProviderName.osm_nominatim},
    ProviderFeature.whatsapp: {ProviderName.authkey, ProviderName.twilio},
    ProviderFeature.sms_voice: {ProviderName.authkey, ProviderName.twilio},
}


class ProviderConfigService:
    def get_config(self) -> ProviderConfigResponse:
        return ProviderConfigResponse(
            routes=store.list_provider_routes(),
            updated_at=store.provider_routes_updated_at,
        )

    def update_config(self, payload: ProviderConfigUpdate) -> ProviderConfigResponse:
        for feature, update in payload.routes.items():
            current = store.get_provider_route(feature)
            primary = update.primary or current.primary
            secondary = update.secondary if update.secondary is not None else current.secondary
            self._validate_route(feature, primary, secondary)

            route = ProviderRoute(
                feature=feature,
                primary=primary,
                secondary=secondary,
                allow_fallback=current.allow_fallback if update.allow_fallback is None else update.allow_fallback,
                enabled=current.enabled if update.enabled is None else update.enabled,
                note=current.note if update.note is None else update.note,
            )
            if feature == ProviderFeature.satellite:
                route.allow_fallback = False
                route.secondary = None
            store.save_provider_route(route)
        return self.get_config()

    def _validate_route(
        self,
        feature: ProviderFeature,
        primary: ProviderName,
        secondary: ProviderName | None,
    ) -> None:
        allowed = ALLOWED_PROVIDERS[feature]
        if primary not in allowed:
            raise ValueError(f"{primary.value} is not valid for {feature.value}")
        if secondary is not None and secondary not in allowed:
            raise ValueError(f"{secondary.value} is not valid for {feature.value}")
        if secondary == primary:
            raise ValueError(f"{feature.value} primary and secondary providers must differ")
