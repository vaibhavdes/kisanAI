from typing import Any

import requests

from app.core.config import settings
from app.models.schemas import (
    ProviderFeature,
    ProviderName,
    WeatherContextRequest,
    WeatherContextResponse,
    WeatherDailyForecast,
    WeatherProviderStatus,
)
from app.repositories.store import store
from app.services.service_audit_log_service import ServiceAuditLogService


class WeatherProviderUnavailable(RuntimeError):
    pass


class WeatherContextService:
    def get_context(self, payload: WeatherContextRequest) -> WeatherContextResponse:
        route = store.get_provider_route(ProviderFeature.weather)
        provider_order = [route.primary]
        if route.allow_fallback and route.secondary:
            provider_order.append(route.secondary)

        statuses: list[WeatherProviderStatus] = []
        last_error: str | None = None
        for index, provider in enumerate(provider_order):
            start = ServiceAuditLogService().start()
            try:
                context = self._fetch(provider, payload)
                ServiceAuditLogService().record(
                    service="weather",
                    operation="get_context",
                    provider=provider.value,
                    success=True,
                    duration_ms=ServiceAuditLogService().elapsed_ms(start),
                    request_body={"latitude": payload.latitude, "longitude": payload.longitude, "days": payload.days},
                    response_body={
                        "currentTemperatureC": context.current_temperature_c,
                        "dailyCount": len(context.daily),
                        "source": context.source.value,
                    },
                )
                statuses.append(WeatherProviderStatus(provider=provider, attempted=True, success=True))
                return context.model_copy(
                    update={
                        "fallback_used": index > 0,
                        "provider_statuses": statuses,
                    }
                )
            except Exception as exc:
                last_error = str(exc)
                ServiceAuditLogService().record(
                    service="weather",
                    operation="get_context",
                    provider=provider.value,
                    success=False,
                    duration_ms=ServiceAuditLogService().elapsed_ms(start),
                    request_body={"latitude": payload.latitude, "longitude": payload.longitude, "days": payload.days},
                    error=last_error,
                )
                statuses.append(
                    WeatherProviderStatus(
                        provider=provider,
                        attempted=True,
                        success=False,
                        error=last_error,
                    )
                )

        raise WeatherProviderUnavailable(last_error or "No weather provider returned data")

    def _fetch(self, provider: ProviderName, payload: WeatherContextRequest) -> WeatherContextResponse:
        if provider == ProviderName.imd:
            return self._fetch_imd(payload)
        if provider == ProviderName.open_meteo:
            return self._fetch_open_meteo(payload)
        raise WeatherProviderUnavailable(f"{provider.value} is not a weather provider")

    def _fetch_imd(self, payload: WeatherContextRequest) -> WeatherContextResponse:
        if not settings.imd_api_base_url or not settings.imd_api_key:
            raise WeatherProviderUnavailable("IMD API is not configured")

        response = requests.get(
            settings.imd_api_base_url,
            params={"lat": payload.latitude, "lon": payload.longitude, "days": payload.days},
            headers={"Authorization": f"Bearer {settings.imd_api_key}"},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        daily = data.get("daily") or []
        if not daily:
            raise WeatherProviderUnavailable("IMD API response did not include daily forecast")

        return WeatherContextResponse(
            latitude=payload.latitude,
            longitude=payload.longitude,
            source=ProviderName.imd,
            fallback_used=False,
            provider_statuses=[],
            current_temperature_c=self._float(data.get("current_temperature_c")),
            current_humidity_percent=self._float(data.get("current_humidity_percent")),
            current_wind_speed_kmph=self._float(data.get("current_wind_speed_kmph")),
            current_precipitation_mm=self._float(data.get("current_precipitation_mm")),
            current_weather_code=self._int(data.get("current_weather_code")),
            daily=[
                WeatherDailyForecast(
                    date=str(item.get("date")),
                    rainfall_mm=self._float(item.get("rainfall_mm")),
                    rainfall_probability_percent=self._float(item.get("rainfall_probability_percent")),
                    temperature_max_c=self._float(item.get("temperature_max_c")),
                    temperature_min_c=self._float(item.get("temperature_min_c")),
                    wind_speed_max_kmph=self._float(item.get("wind_speed_max_kmph")),
                    evapotranspiration_mm=self._float(item.get("evapotranspiration_mm")),
                )
                for item in daily[: payload.days]
            ],
        )

    def _fetch_open_meteo(self, payload: WeatherContextRequest) -> WeatherContextResponse:
        params = {
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "current": ",".join(
                [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "precipitation",
                    "weather_code",
                    "wind_speed_10m",
                ]
            ),
            "daily": ",".join(
                [
                    "precipitation_sum",
                    "precipitation_probability_max",
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "wind_speed_10m_max",
                    "et0_fao_evapotranspiration",
                ]
            ),
            "forecast_days": payload.days,
            "timezone": "auto",
        }
        if payload.include_hourly_soil:
            params["hourly"] = "soil_temperature_0cm,soil_moisture_0_to_1cm"

        response = requests.get(
            settings.open_meteo_base_url,
            params=params,
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        daily = data.get("daily") or {}
        dates = daily.get("time") or []
        if not dates:
            raise WeatherProviderUnavailable("Open-Meteo response did not include daily forecast")

        hourly = data.get("hourly") or {}
        current = data.get("current") or {}
        return WeatherContextResponse(
            latitude=payload.latitude,
            longitude=payload.longitude,
            source=ProviderName.open_meteo,
            fallback_used=False,
            provider_statuses=[],
            current_temperature_c=self._float(current.get("temperature_2m")),
            current_humidity_percent=self._float(current.get("relative_humidity_2m")),
            current_wind_speed_kmph=self._float(current.get("wind_speed_10m")),
            current_precipitation_mm=self._float(current.get("precipitation")),
            current_weather_code=self._int(current.get("weather_code")),
            soil_moisture=self._first_float(hourly.get("soil_moisture_0_to_1cm")),
            soil_temperature_c=self._first_float(hourly.get("soil_temperature_0cm")),
            daily=[
                WeatherDailyForecast(
                    date=str(date),
                    rainfall_mm=self._list_float(daily, "precipitation_sum", index),
                    rainfall_probability_percent=self._list_float(
                        daily, "precipitation_probability_max", index
                    ),
                    temperature_max_c=self._list_float(daily, "temperature_2m_max", index),
                    temperature_min_c=self._list_float(daily, "temperature_2m_min", index),
                    wind_speed_max_kmph=self._list_float(daily, "wind_speed_10m_max", index),
                    evapotranspiration_mm=self._list_float(
                        daily, "et0_fao_evapotranspiration", index
                    ),
                )
                for index, date in enumerate(dates)
            ],
        )

    def _float(self, value: Any) -> float | None:
        return float(value) if value is not None else None

    def _int(self, value: Any) -> int | None:
        return int(value) if value is not None else None

    def _first_float(self, values: list[Any] | None) -> float | None:
        if not values:
            return None
        return self._float(values[0])

    def _list_float(self, data: dict[str, list[Any]], key: str, index: int) -> float | None:
        values = data.get(key) or []
        if index >= len(values):
            return None
        return self._float(values[index])
