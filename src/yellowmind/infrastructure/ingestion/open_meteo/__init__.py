"""Open-Meteo historical weather adapter."""

from yellowmind.infrastructure.ingestion.open_meteo.client import (
    DailyWeatherObservation,
    GeoLocation,
    OpenMeteoClient,
    OpenMeteoError,
)
from yellowmind.infrastructure.ingestion.open_meteo.config import OpenMeteoConfig
from yellowmind.infrastructure.ingestion.open_meteo.urls import (
    archive_daily_path,
    geocode_path,
)

__all__ = [
    "DailyWeatherObservation",
    "GeoLocation",
    "OpenMeteoClient",
    "OpenMeteoConfig",
    "OpenMeteoError",
    "archive_daily_path",
    "geocode_path",
]
