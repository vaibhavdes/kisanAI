from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal


RegionalSourceType = Literal[
    "weather_forecast",
    "imd_warning",
    "agromet_advisory",
    "satellite_index",
    "maharain_dryspell",
    "maharain_heavy_rainfall",
    "groundwater",
    "soil_health",
    "crop_history",
]


@dataclass(frozen=True)
class RegionalCacheWindow:
    cache_key: str
    valid_from: datetime
    valid_until: datetime
    ttl_seconds: int


class RegionalCachePolicy:
    """Shared region cache policy for data that can serve many nearby farmers."""

    TTL_BY_SOURCE: dict[str, timedelta] = {
        "weather_forecast": timedelta(hours=3),
        "imd_warning": timedelta(hours=1),
        "agromet_advisory": timedelta(hours=24),
        "satellite_index": timedelta(days=7),
        "maharain_dryspell": timedelta(days=7),
        "maharain_heavy_rainfall": timedelta(days=7),
        "groundwater": timedelta(days=30),
        "soil_health": timedelta(days=90),
        "crop_history": timedelta(days=365),
    }

    def build_key(
        self,
        *,
        source_type: RegionalSourceType,
        provider: str,
        state: str | None = None,
        district: str | None = None,
        taluka: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        grid_precision: int = 2,
    ) -> RegionalCacheWindow:
        now = datetime.now(UTC)
        ttl = self.TTL_BY_SOURCE[source_type]
        location_parts = [
            self._clean(state),
            self._clean(district),
            self._clean(taluka),
        ]
        if latitude is not None and longitude is not None:
            location_parts.extend(
                [
                    f"lat:{round(latitude, grid_precision):.{grid_precision}f}",
                    f"lon:{round(longitude, grid_precision):.{grid_precision}f}",
                ]
            )
        key = "|".join([source_type, provider, *[part for part in location_parts if part]])
        return RegionalCacheWindow(
            cache_key=key,
            valid_from=now,
            valid_until=now + ttl,
            ttl_seconds=int(ttl.total_seconds()),
        )

    def _clean(self, value: str | None) -> str | None:
        if not value:
            return None
        return " ".join(value.strip().lower().split())
