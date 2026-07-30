"""Tests for the Open-Meteo client."""

import json
from collections.abc import Callable
from datetime import date
from pathlib import Path

import httpx
import pytest

from yellowmind.infrastructure.ingestion.http import (
    CachedHttpFetcher,
    FileResponseCache,
    RateLimiter,
)
from yellowmind.infrastructure.ingestion.open_meteo import (
    OpenMeteoClient,
    OpenMeteoConfig,
    OpenMeteoError,
    archive_daily_path,
    geocode_path,
)

ARCHIVE = "https://archive-api.open-meteo.com"
GEOCODING = "https://geocoding-api.open-meteo.com"


def _client(
    handler: Callable[[httpx.Request], httpx.Response],
    cache_dir: Path,
) -> OpenMeteoClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    archive = CachedHttpFetcher(
        base_url=ARCHIVE,
        user_agent="TestAgent/1.0",
        cache=FileResponseCache(cache_dir / "archive"),
        rate_limiter=RateLimiter(0),
        http_client=http_client,
        sleep=lambda _: None,
    )
    geocoding = CachedHttpFetcher(
        base_url=GEOCODING,
        user_agent="TestAgent/1.0",
        cache=FileResponseCache(cache_dir / "geocoding"),
        rate_limiter=RateLimiter(0),
        http_client=http_client,
        sleep=lambda _: None,
    )
    return OpenMeteoClient(
        OpenMeteoConfig(user_agent="TestAgent/1.0"),
        archive_fetcher=archive,
        geocoding_fetcher=geocoding,
    )


def test_geocode_prefers_tour_corridor_country(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "geocoding-api.open-meteo.com"
        body = {
            "results": [
                {
                    "name": "Nogaro",
                    "latitude": 45.82,
                    "longitude": 13.22,
                    "country_code": "IT",
                },
                {
                    "name": "Nogaro",
                    "latitude": 43.76,
                    "longitude": -0.03,
                    "country_code": "FR",
                },
            ]
        }
        return httpx.Response(200, text=json.dumps(body))

    location = _client(handler, tmp_path).geocode("Nogaro")

    assert location is not None
    assert location.country_code == "FR"
    assert location.latitude == 43.76
    assert location.longitude == -0.03


def test_geocode_returns_none_when_empty(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=json.dumps({"results": []}))

    assert _client(handler, tmp_path).geocode("Nowhereville") is None


def test_fetch_daily_reads_archive_fields(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "archive-api.open-meteo.com"
        body = {
            "daily": {
                "time": ["2023-07-01"],
                "temperature_2m_mean": [24.5],
                "precipitation_sum": [1.2],
                "wind_speed_10m_max": [18.0],
            }
        }
        return httpx.Response(200, text=json.dumps(body))

    observation = _client(handler, tmp_path).fetch_daily(43.26, -2.92, date(2023, 7, 1))

    assert observation.temperature_c == 24.5
    assert observation.precipitation_mm == 1.2
    assert observation.wind_speed_kmh == 18.0


def test_fetch_daily_rejects_null_values(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = {
            "daily": {
                "time": ["2023-07-01"],
                "temperature_2m_mean": [None],
                "precipitation_sum": [0.0],
                "wind_speed_10m_max": [10.0],
            }
        }
        return httpx.Response(200, text=json.dumps(body))

    with pytest.raises(OpenMeteoError, match="null weather"):
        _client(handler, tmp_path).fetch_daily(43.26, -2.92, date(2023, 7, 1))


def test_url_helpers() -> None:
    assert "name=Bilbao" in geocode_path("Bilbao")
    assert "2023-07-01" in archive_daily_path(43.0, -2.0, date(2023, 7, 1))


def test_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPEN_METEO_RATE_LIMIT_SECONDS", "0.5")
    monkeypatch.setenv("OPEN_METEO_MAX_RETRIES", "5")

    config = OpenMeteoConfig.from_env()

    assert config.rate_limit_seconds == 0.5
    assert config.max_retries == 5
