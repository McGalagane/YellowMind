"""Open-Meteo archive and geocoding client.

Weather for each stage is taken at the finish on the stage date. Mountain
finishes often miss Open-Meteo's geocoder; callers should fall back to Wikipedia
page coordinates using the course wikilink slug.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Final, cast

import httpx

from yellowmind.infrastructure.ingestion.http import (
    CachedHttpFetcher,
    FileResponseCache,
    RateLimiter,
)
from yellowmind.infrastructure.ingestion.open_meteo.config import OpenMeteoConfig
from yellowmind.infrastructure.ingestion.open_meteo.urls import (
    archive_daily_path,
    geocode_path,
)

# Prefer results in countries the Tour actually visits so ambiguous names
# (Nogaro FR vs IT) resolve to the race corridor. Lower rank wins when several
# corridor countries match; France is first because most finishes are there.
_COUNTRY_PRIORITY: Final[dict[str, int]] = {
    "FR": 0,
    "ES": 1,
    "IT": 2,
    "BE": 3,
    "NL": 4,
    "DK": 5,
    "CH": 6,
    "AD": 7,
    "DE": 8,
    "LU": 9,
    "MC": 10,
    "GB": 11,
    "PT": 12,
}


@dataclass(frozen=True, slots=True)
class GeoLocation:
    """A resolved place used as a weather sample point."""

    name: str
    latitude: float
    longitude: float
    country_code: str
    source: str


@dataclass(frozen=True, slots=True)
class DailyWeatherObservation:
    """Daily aggregates from the archive API."""

    temperature_c: float
    wind_speed_kmh: float
    precipitation_mm: float


class OpenMeteoError(Exception):
    """Raised when Open-Meteo returns an unusable payload."""


class OpenMeteoClient:
    """Cached client for Open-Meteo geocoding and historical weather."""

    def __init__(
        self,
        config: OpenMeteoConfig | None = None,
        *,
        http_client: httpx.Client | None = None,
        archive_fetcher: CachedHttpFetcher | None = None,
        geocoding_fetcher: CachedHttpFetcher | None = None,
    ) -> None:
        resolved = config or OpenMeteoConfig.from_env()

        shared_client = http_client
        owns_client = http_client is None
        if shared_client is None:
            shared_client = httpx.Client(
                timeout=resolved.timeout_seconds,
                follow_redirects=True,
            )

        self._owns_client = owns_client and archive_fetcher is None and geocoding_fetcher is None
        self._http_client = shared_client

        self._archive = archive_fetcher or CachedHttpFetcher(
            base_url=resolved.archive_base_url,
            user_agent=resolved.user_agent,
            cache=FileResponseCache(resolved.cache_dir / "archive"),
            rate_limiter=RateLimiter(resolved.rate_limit_seconds),
            max_retries=resolved.max_retries,
            timeout_seconds=resolved.timeout_seconds,
            http_client=shared_client,
        )
        self._geocoding = geocoding_fetcher or CachedHttpFetcher(
            base_url=resolved.geocoding_base_url,
            user_agent=resolved.user_agent,
            cache=FileResponseCache(resolved.cache_dir / "geocoding"),
            rate_limiter=RateLimiter(resolved.rate_limit_seconds),
            max_retries=resolved.max_retries,
            timeout_seconds=resolved.timeout_seconds,
            http_client=shared_client,
        )
        # When callers inject fetchers they own the HTTP lifecycle.
        if archive_fetcher is not None or geocoding_fetcher is not None:
            self._owns_client = False

    def geocode(self, name: str) -> GeoLocation | None:
        """Resolve a place name, preferring Tour-corridor countries."""
        payload = _json_object(self._geocoding.fetch(geocode_path(name)))
        results_raw = payload.get("results")
        if not isinstance(results_raw, list) or not results_raw:
            return None
        results = cast(list[object], results_raw)

        preferred: list[dict[str, object]] = []
        for row in results:
            mapped = _as_object_map(row)
            if mapped is None:
                continue
            if str(mapped.get("country_code", "")) in _COUNTRY_PRIORITY:
                preferred.append(mapped)

        chosen: dict[str, object] | None
        if preferred:
            preferred.sort(key=lambda row: _COUNTRY_PRIORITY[str(row.get("country_code", ""))])
            chosen = preferred[0]
        else:
            chosen = _as_object_map(results[0])
        if chosen is None:
            return None

        try:
            return GeoLocation(
                name=str(chosen["name"]),
                latitude=_as_float(chosen["latitude"]),
                longitude=_as_float(chosen["longitude"]),
                country_code=str(chosen.get("country_code", "")),
                source="open_meteo",
            )
        except (KeyError, TypeError, ValueError) as exc:
            msg = f"Unusable geocoding result for {name!r}"
            raise OpenMeteoError(msg) from exc

    def fetch_daily(self, latitude: float, longitude: float, day: date) -> DailyWeatherObservation:
        """Fetch daily mean temperature, precip sum, and max wind for ``day``."""
        payload = _json_object(self._archive.fetch(archive_daily_path(latitude, longitude, day)))
        daily_map = _as_object_map(payload.get("daily"))
        if daily_map is None:
            msg = f"Archive response missing daily block for {day.isoformat()}"
            raise OpenMeteoError(msg)

        try:
            temperature = _first_series_value(daily_map, "temperature_2m_mean")
            precipitation = _first_series_value(daily_map, "precipitation_sum")
            wind = _first_series_value(daily_map, "wind_speed_10m_max")
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            msg = f"Archive response missing daily values for {day.isoformat()}"
            raise OpenMeteoError(msg) from exc

        if temperature is None or precipitation is None or wind is None:
            msg = f"Archive returned null weather for {day.isoformat()} at {latitude},{longitude}"
            raise OpenMeteoError(msg)

        return DailyWeatherObservation(
            temperature_c=temperature,
            wind_speed_kmh=wind,
            precipitation_mm=precipitation,
        )

    def close(self) -> None:
        """Release HTTP resources owned by this client."""
        if self._owns_client:
            self._http_client.close()
        else:
            self._archive.close()
            self._geocoding.close()

    def __enter__(self) -> OpenMeteoClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def _json_object(text: str) -> dict[str, object]:
    """Parse a JSON object root into a string-keyed map."""
    mapped = _as_object_map(json.loads(text))
    if mapped is None:
        msg = "Expected a JSON object"
        raise OpenMeteoError(msg)
    return mapped


def _as_object_map(value: object) -> dict[str, object] | None:
    """Narrow a JSON value to a string-keyed object map."""
    if not isinstance(value, dict):
        return None
    typed = cast(dict[object, object], value)
    return {str(key): item for key, item in typed.items()}


def _first_series_value(daily: dict[str, object], key: str) -> float | None:
    """Return the first numeric value of a daily series."""
    series_raw = daily[key]
    if not isinstance(series_raw, list) or not series_raw:
        raise IndexError(key)
    value = cast(object, series_raw[0])
    if value is None:
        return None
    return _as_float(value)


def _as_float(value: object) -> float:
    """Coerce a JSON number to float."""
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        msg = f"Expected a number, got {type(value)!r}"
        raise TypeError(msg)
    return float(value)
