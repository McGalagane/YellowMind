"""URL helpers for Open-Meteo endpoints."""

from datetime import date
from urllib.parse import urlencode


def geocode_path(name: str, *, count: int = 5) -> str:
    """Relative path for a place-name search."""
    query = urlencode({"name": name, "count": count, "language": "en", "format": "json"})
    return f"/v1/search?{query}"


def archive_daily_path(
    latitude: float,
    longitude: float,
    day: date,
    *,
    timezone: str = "Europe/Paris",
) -> str:
    """Relative path for one day's archive weather at a point."""
    query = urlencode(
        {
            "latitude": f"{latitude:.5f}",
            "longitude": f"{longitude:.5f}",
            "start_date": day.isoformat(),
            "end_date": day.isoformat(),
            "daily": "temperature_2m_mean,precipitation_sum,wind_speed_10m_max",
            "timezone": timezone,
        }
    )
    return f"/v1/archive?{query}"
