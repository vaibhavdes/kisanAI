from common import print_ok, require_package

require_package("requests", "pip install -r requirements.txt")

from app.models.schemas import WeatherContextRequest
from app.services.weather_context_service import WeatherContextService


context = WeatherContextService().get_context(
    WeatherContextRequest(latitude=18.5204, longitude=73.8567, days=3)
)

if not context.daily:
    raise RuntimeError("Open-Meteo weather context did not include daily forecast")

print_ok(
    f"Weather context responded from {context.source.value}; "
    f"fallback={context.fallback_used}; days={len(context.daily)}"
)
