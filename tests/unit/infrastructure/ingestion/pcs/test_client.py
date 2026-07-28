"""Tests for the PCS client.

Transport behaviour is covered once against the shared fetcher in
``tests/unit/infrastructure/ingestion/http``; these tests cover PCS-specific
configuration, URL building, and delegation.
"""

from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from yellowmind.application.ports.cycling_data_source import CyclingDataSource
from yellowmind.infrastructure.ingestion.http import (
    CachedHttpFetcher,
    FileResponseCache,
    RateLimiter,
)
from yellowmind.infrastructure.ingestion.pcs import PCSClient, PCSConfig, tour_stage_path

BASE_URL = "https://www.procyclingstats.com"


def build_client(
    handler: Callable[[httpx.Request], httpx.Response],
    cache_dir: Path,
) -> PCSClient:
    """Build a client whose fetcher is wired to a mock transport."""
    fetcher = CachedHttpFetcher(
        base_url=BASE_URL,
        user_agent="TestAgent/1.0",
        cache=FileResponseCache(cache_dir),
        rate_limiter=RateLimiter(0),
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
    )
    return PCSClient(fetcher=fetcher)


def test_client_implements_data_source_port() -> None:
    assert issubclass(PCSClient, CyclingDataSource)


def test_tour_stage_path() -> None:
    assert tour_stage_path("tour-de-france", 2023, 1) == "/race/tour-de-france/2023/stage-1"


def test_fetch_delegates_to_fetcher(tmp_path: Path) -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        return httpx.Response(200, text="<html>stage</html>")

    content = build_client(handler, tmp_path).fetch(tour_stage_path("tour-de-france", 2023, 1))

    assert content == "<html>stage</html>"
    assert paths == ["/race/tour-de-france/2023/stage-1"]


def test_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PCS_RATE_LIMIT_SECONDS", "2.5")
    monkeypatch.setenv("PCS_MAX_RETRIES", "5")
    monkeypatch.setenv("PCS_USER_AGENT", "TestAgent/1.0")

    config = PCSConfig.from_env()

    assert config.rate_limit_seconds == 2.5
    assert config.max_retries == 5
    assert config.user_agent == "TestAgent/1.0"


def test_default_config_targets_pcs() -> None:
    assert PCSConfig().base_url == BASE_URL
