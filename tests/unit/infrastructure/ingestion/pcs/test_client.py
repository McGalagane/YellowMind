"""Tests for PCS HTTP client."""

from pathlib import Path

import httpx
import pytest

from yellowmind.infrastructure.ingestion.pcs.cache import FileResponseCache
from yellowmind.infrastructure.ingestion.pcs.client import PCSClient, PCSClientError
from yellowmind.infrastructure.ingestion.pcs.config import PCSConfig
from yellowmind.infrastructure.ingestion.pcs.rate_limiter import RateLimiter
from yellowmind.infrastructure.ingestion.pcs.urls import tour_stage_path


@pytest.fixture
def cache_dir(tmp_path: Path) -> Path:
    return tmp_path / "pcs-cache"


@pytest.fixture
def config(cache_dir: Path) -> PCSConfig:
    return PCSConfig(
        rate_limit_seconds=0,
        max_retries=2,
        cache_dir=cache_dir,
    )


def test_tour_stage_path() -> None:
    path = tour_stage_path("tour-de-france", 2023, 1)
    assert path == "/race/tour-de-france/2023/stage-1"


def test_fetch_returns_cached_response_without_http_call(
    config: PCSConfig,
    cache_dir: Path,
) -> None:
    cache = FileResponseCache(cache_dir)
    url = "https://www.procyclingstats.com/race/tour-de-france/2023/stage-1"
    cache.set(url, "<html>cached</html>")

    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(200, text="<html>live</html>")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)

    client = PCSClient(config, http_client=http_client, cache=cache)
    content = client.fetch("/race/tour-de-france/2023/stage-1")

    assert content == "<html>cached</html>"
    assert request_count == 0


def test_fetch_makes_http_request_on_cache_miss(config: PCSConfig, cache_dir: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["User-Agent"] == config.user_agent
        return httpx.Response(200, text="<html>Tour de France</html>")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = PCSClient(config, http_client=http_client, cache=FileResponseCache(cache_dir))

    content = client.fetch("/race/tour-de-france/2023/stage-1")

    assert "Tour de France" in content
    assert client.fetch("/race/tour-de-france/2023/stage-1") == content


def test_fetch_retries_on_transient_error(config: PCSConfig, cache_dir: Path) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, text="unavailable")
        return httpx.Response(200, text="<html>ok</html>")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = PCSClient(config, http_client=http_client, cache=FileResponseCache(cache_dir))

    content = client.fetch("/race/tour-de-france/2023/stage-1")

    assert content == "<html>ok</html>"
    assert attempts == 2


def test_fetch_raises_on_client_error(config: PCSConfig, cache_dir: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = PCSClient(config, http_client=http_client, cache=FileResponseCache(cache_dir))

    with pytest.raises(PCSClientError):
        client.fetch("/race/tour-de-france/2023/stage-999")


def test_rate_limiter_rejects_negative_interval() -> None:
    with pytest.raises(ValueError, match="Rate limit"):
        RateLimiter(-0.1)


def test_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PCS_RATE_LIMIT_SECONDS", "2.5")
    monkeypatch.setenv("PCS_MAX_RETRIES", "5")
    monkeypatch.setenv("PCS_USER_AGENT", "TestAgent/1.0")

    config = PCSConfig.from_env()

    assert config.rate_limit_seconds == 2.5
    assert config.max_retries == 5
    assert config.user_agent == "TestAgent/1.0"
