from dataclasses import dataclass
from typing import Any

import requests

from app.core.config import settings
from app.models.schemas import FarmerResponse, ProviderFeature, ProviderName
from app.repositories.store import store


class GeocodingProviderUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class LocationResolution:
    source: str
    latitude: float | None = None
    longitude: float | None = None
    village: str | None = None
    taluka: str | None = None
    district: str | None = None
    state: str | None = None
    pincode: str | None = None
    formatted_address: str | None = None


class GeocodingService:
    def resolve_coordinates(self, latitude: float, longitude: float) -> LocationResolution:
        errors: list[str] = []
        for provider in self._provider_order():
            try:
                if provider == ProviderName.google_maps:
                    return self._reverse_google(latitude, longitude)
                if provider == ProviderName.osm_nominatim:
                    return self._reverse_nominatim(latitude, longitude)
            except Exception as exc:
                errors.append(f"{provider.value}:{exc}")
        return LocationResolution(source="coordinates", latitude=latitude, longitude=longitude)

    def resolve_text(self, text: str) -> LocationResolution:
        query = text.strip()
        if not query:
            raise GeocodingProviderUnavailable("Location text is empty.")
        if query.isdigit() and len(query) == 6:
            postal = self._resolve_india_post_pincode(query)
            if postal.district or postal.state:
                geocoded = self._safe_resolve_address(f"{query}, India")
                return self._merge(postal, geocoded)
            return self._merge(self._maharashtra_pincode_fallback(query), self._safe_resolve_address(f"{query}, India"))
        return self._resolve_address_with_providers(query)

    def apply_to_farmer(self, farmer: FarmerResponse, resolution: LocationResolution) -> FarmerResponse:
        data = farmer.model_dump()
        if resolution.village:
            data["village"] = resolution.village
        if resolution.taluka:
            data["taluka"] = resolution.taluka
        if resolution.district:
            data["district"] = resolution.district
        if resolution.state:
            data["state"] = resolution.state
        if resolution.pincode:
            data["pincode"] = resolution.pincode
        farm = farmer.farm.model_dump()
        if resolution.latitude is not None:
            farm["latitude"] = resolution.latitude
        if resolution.longitude is not None:
            farm["longitude"] = resolution.longitude
        data["farm"] = farm
        return store.save_farmer(FarmerResponse(**data))

    def _resolve_address_with_providers(self, query: str) -> LocationResolution:
        errors: list[str] = []
        for provider in self._provider_order():
            try:
                if provider == ProviderName.google_maps:
                    return self._geocode_google(query)
                if provider == ProviderName.osm_nominatim:
                    return self._geocode_nominatim(query)
            except Exception as exc:
                errors.append(f"{provider.value}:{exc}")
        fallback = self._maharashtra_text_fallback(query)
        if fallback.district or fallback.state:
            return fallback
        raise GeocodingProviderUnavailable("; ".join(errors) or "No geocoding provider returned a result.")

    def _safe_resolve_address(self, query: str) -> LocationResolution:
        try:
            return self._resolve_address_with_providers(query)
        except GeocodingProviderUnavailable:
            return LocationResolution(source="geocoding_unavailable", formatted_address=query)

    def _geocode_google(self, query: str) -> LocationResolution:
        if not settings.maps_api_key:
            raise GeocodingProviderUnavailable("MAPS_API_KEY is not configured.")
        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": query, "key": settings.maps_api_key},
            timeout=settings.geocoding_request_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results") or []
        if not results:
            raise GeocodingProviderUnavailable("Google Maps returned no geocoding results.")
        return self._google_result_to_resolution(results[0], source=ProviderName.google_maps.value)

    def _reverse_google(self, latitude: float, longitude: float) -> LocationResolution:
        if not settings.maps_api_key:
            raise GeocodingProviderUnavailable("MAPS_API_KEY is not configured.")
        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"latlng": f"{latitude},{longitude}", "key": settings.maps_api_key},
            timeout=settings.geocoding_request_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results") or []
        if not results:
            raise GeocodingProviderUnavailable("Google Maps returned no reverse geocoding results.")
        resolution = self._google_result_to_resolution(results[0], source=ProviderName.google_maps.value)
        return LocationResolution(**{**resolution.__dict__, "latitude": latitude, "longitude": longitude})

    def _geocode_nominatim(self, query: str) -> LocationResolution:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "countrycodes": "in", "format": "jsonv2", "addressdetails": 1, "limit": 1},
            headers={"User-Agent": "KisanAI-Hackathon/1.0"},
            timeout=settings.geocoding_request_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            raise GeocodingProviderUnavailable("Nominatim returned no geocoding results.")
        item = data[0]
        return self._nominatim_result_to_resolution(item, source=ProviderName.osm_nominatim.value)

    def _reverse_nominatim(self, latitude: float, longitude: float) -> LocationResolution:
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": latitude, "lon": longitude, "format": "jsonv2", "addressdetails": 1},
            headers={"User-Agent": "KisanAI-Hackathon/1.0"},
            timeout=settings.geocoding_request_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            raise GeocodingProviderUnavailable("Nominatim returned no reverse geocoding result.")
        resolution = self._nominatim_result_to_resolution(data, source=ProviderName.osm_nominatim.value)
        return LocationResolution(**{**resolution.__dict__, "latitude": latitude, "longitude": longitude})

    def _resolve_india_post_pincode(self, pincode: str) -> LocationResolution:
        try:
            response = requests.get(
                f"https://api.postalpincode.in/pincode/{pincode}",
                timeout=settings.geocoding_request_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            offices = (data[0] or {}).get("PostOffice") if data else None
            if not offices:
                return self._maharashtra_pincode_fallback(pincode)
            office = offices[0]
            return LocationResolution(
                source="india_post_pincode",
                village=office.get("Name"),
                taluka=office.get("Block") or office.get("Taluk"),
                district=office.get("District"),
                state=office.get("State"),
                pincode=pincode,
                formatted_address=", ".join(
                    str(part)
                    for part in [office.get("Name"), office.get("Block"), office.get("District"), office.get("State"), pincode]
                    if part
                ),
            )
        except Exception:
            return self._maharashtra_pincode_fallback(pincode)

    def _google_result_to_resolution(self, result: dict[str, Any], *, source: str) -> LocationResolution:
        components = result.get("address_components") or []
        geometry = result.get("geometry") or {}
        location = geometry.get("location") or {}
        return LocationResolution(
            source=source,
            latitude=self._float(location.get("lat")),
            longitude=self._float(location.get("lng")),
            village=self._component(components, "locality") or self._component(components, "sublocality") or self._component(components, "administrative_area_level_3"),
            taluka=self._component(components, "administrative_area_level_3"),
            district=self._component(components, "administrative_area_level_2"),
            state=self._component(components, "administrative_area_level_1"),
            pincode=self._component(components, "postal_code"),
            formatted_address=result.get("formatted_address"),
        )

    def _nominatim_result_to_resolution(self, result: dict[str, Any], *, source: str) -> LocationResolution:
        address = result.get("address") or {}
        return LocationResolution(
            source=source,
            latitude=self._float(result.get("lat")),
            longitude=self._float(result.get("lon")),
            village=address.get("village") or address.get("town") or address.get("city") or address.get("suburb"),
            taluka=address.get("county") or address.get("state_district"),
            district=address.get("state_district") or address.get("county"),
            state=address.get("state"),
            pincode=address.get("postcode"),
            formatted_address=result.get("display_name"),
        )

    def _component(self, components: list[dict[str, Any]], target_type: str) -> str | None:
        for component in components:
            if target_type in component.get("types", []):
                return component.get("long_name")
        return None

    def _maharashtra_pincode_fallback(self, pincode: str) -> LocationResolution:
        if pincode.startswith(("413", "414")):
            return LocationResolution(
                source="maharashtra_pincode_prefix_fallback",
                district="Ahilyanagar",
                state="Maharashtra",
                pincode=pincode,
                formatted_address=f"Pincode {pincode}, Ahilyanagar, Maharashtra",
            )
        if pincode.startswith("411"):
            return LocationResolution(
                source="maharashtra_pincode_prefix_fallback",
                district="Pune",
                state="Maharashtra",
                pincode=pincode,
                formatted_address=f"Pincode {pincode}, Pune, Maharashtra",
            )
        return LocationResolution(source="pincode_unresolved", pincode=pincode)

    def _maharashtra_text_fallback(self, query: str) -> LocationResolution:
        normalized = query.lower()
        if any(token in normalized for token in ["ahilyanagar", "ahmednagar", "अहिल्यानगर", "अहमदनगर"]):
            return LocationResolution(source="maharashtra_text_fallback", district="Ahilyanagar", state="Maharashtra", formatted_address=query)
        if "pune" in normalized or "पुणे" in normalized:
            return LocationResolution(source="maharashtra_text_fallback", district="Pune", state="Maharashtra", formatted_address=query)
        return LocationResolution(source="text_unresolved", formatted_address=query)

    def _merge(self, primary: LocationResolution, secondary: LocationResolution) -> LocationResolution:
        return LocationResolution(
            source=f"{primary.source}+{secondary.source}",
            latitude=secondary.latitude or primary.latitude,
            longitude=secondary.longitude or primary.longitude,
            village=primary.village or secondary.village,
            taluka=primary.taluka or secondary.taluka,
            district=primary.district or secondary.district,
            state=primary.state or secondary.state,
            pincode=primary.pincode or secondary.pincode,
            formatted_address=primary.formatted_address or secondary.formatted_address,
        )

    def _provider_order(self) -> list[ProviderName]:
        route = store.get_provider_route(ProviderFeature.geocoding_maps)
        if not route.enabled:
            return []
        providers = [route.primary]
        if route.allow_fallback and route.secondary:
            providers.append(route.secondary)
        return providers

    def _float(self, value: Any) -> float | None:
        return float(value) if value is not None else None
