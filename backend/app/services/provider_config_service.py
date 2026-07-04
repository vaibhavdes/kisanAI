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
    ProviderFeature.sms_voice: {ProviderName.authkey},
}


class ProviderConfigService:
    def get_config(self) -> ProviderConfigResponse:
        return ProviderConfigResponse(
            routes=self._normalized_routes(),
            updated_at=store.provider_routes_updated_at,
        )

    def update_config(self, payload: ProviderConfigUpdate) -> ProviderConfigResponse:
        for feature, update in payload.routes.items():
            current = store.get_provider_route(feature)
            primary = update.primary or current.primary
            secondary = update.secondary if "secondary" in update.model_fields_set else current.secondary
            if feature == ProviderFeature.sms_voice:
                secondary = update.secondary
            self._validate_route(feature, primary, secondary)

            route = ProviderRoute(
                feature=feature,
                primary=primary,
                secondary=secondary,
                allow_fallback=(
                    update.allow_fallback if "allow_fallback" in update.model_fields_set else current.allow_fallback
                ),
                enabled=update.enabled if "enabled" in update.model_fields_set else current.enabled,
                note=update.note if "note" in update.model_fields_set else current.note,
            )
            if feature == ProviderFeature.satellite:
                route.allow_fallback = False
                route.secondary = None
            if feature == ProviderFeature.sms_voice:
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

    def _normalized_routes(self) -> list[ProviderRoute]:
        routes = []
        for route in store.list_provider_routes():
            if route.feature == ProviderFeature.sms_voice and (
                route.primary != ProviderName.authkey
                or route.secondary is not None
                or route.allow_fallback
            ):
                route = ProviderRoute(
                    feature=ProviderFeature.sms_voice,
                    primary=ProviderName.authkey,
                    secondary=None,
                    allow_fallback=False,
                    enabled=route.enabled,
                    note=route.note
                    or "Outbound SMS and voice-call delivery uses Authkey; Twilio SMS/voice endpoints are inbound webhooks.",
                )
                store.save_provider_route(route)
            routes.append(route)
        return routes
