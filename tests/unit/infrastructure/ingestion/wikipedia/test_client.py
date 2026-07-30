"""Tests for the Wikipedia REST API client."""

from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from yellowmind.application.ports.cycling_data_source import CyclingDataSource
from yellowmind.infrastructure.ingestion.http import (
    CachedHttpFetcher,
    FileResponseCache,
    HttpFetchError,
    RateLimiter,
)
from yellowmind.infrastructure.ingestion.wikipedia import WikipediaClient, WikipediaConfig

BASE_URL = "https://en.wikipedia.org"


def build_client(
    handler: Callable[[httpx.Request], httpx.Response],
    cache_dir: Path,
    *,
    max_retries: int = 2,
) -> WikipediaClient:
    """Build a client whose fetcher is wired to a mock transport."""
    fetcher = CachedHttpFetcher(
        base_url=BASE_URL,
        user_agent="TestAgent/1.0",
        cache=FileResponseCache(cache_dir),
        rate_limiter=RateLimiter(0),
        max_retries=max_retries,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
    )
    return WikipediaClient(fetcher=fetcher)


def test_client_implements_data_source_port() -> None:
    assert issubclass(WikipediaClient, CyclingDataSource)


def test_fetch_edition_page_requests_expected_path(tmp_path: Path) -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        return httpx.Response(200, text="<html>edition</html>")

    content = build_client(handler, tmp_path).fetch_edition_page(2023)

    assert content == "<html>edition</html>"
    assert paths == ["/api/rest_v1/page/html/2023_Tour_de_France"]


def test_fetch_stage_pages_requests_both_articles(tmp_path: Path) -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        return httpx.Response(200, text="<html>stages</html>")

    first, second = build_client(handler, tmp_path).fetch_stage_pages(2023)

    assert first == second == "<html>stages</html>"
    assert paths == [
        "/api/rest_v1/page/html/2023_Tour_de_France,_Stage_1_to_Stage_11",
        "/api/rest_v1/page/html/2023_Tour_de_France,_Stage_12_to_Stage_21",
    ]


def test_fetch_startlist_page_requests_expected_path(tmp_path: Path) -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        return httpx.Response(200, text="<html>startlist</html>")

    content = build_client(handler, tmp_path).fetch_startlist_page(2023)

    assert content == "<html>startlist</html>"
    assert paths == ["/api/rest_v1/page/html/List_of_teams_and_cyclists_in_the_2023_Tour_de_France"]


def test_repeated_fetch_is_served_from_cache(tmp_path: Path) -> None:
    requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return httpx.Response(200, text="<html>edition</html>")

    client = build_client(handler, tmp_path)
    client.fetch_edition_page(2023)
    client.fetch_edition_page(2023)

    assert requests == 1


def test_burst_throttling_is_retried(tmp_path: Path) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, headers={"Retry-After": "1"})
        return httpx.Response(200, text="<html>edition</html>")

    content = build_client(handler, tmp_path).fetch_edition_page(2023)

    assert content == "<html>edition</html>"
    assert attempts == 2


def test_missing_article_raises(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    with pytest.raises(HttpFetchError, match="HTTP 404"):
        build_client(handler, tmp_path).fetch_edition_page(1904)


def test_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WIKIPEDIA_RATE_LIMIT_SECONDS", "2.5")
    monkeypatch.setenv("WIKIPEDIA_MAX_RETRIES", "5")
    monkeypatch.setenv("WIKIPEDIA_USER_AGENT", "TestAgent/1.0")

    config = WikipediaConfig.from_env()

    assert config.rate_limit_seconds == 2.5
    assert config.max_retries == 5
    assert config.user_agent == "TestAgent/1.0"


def test_default_config_identifies_the_project() -> None:
    # Wikipedia's API etiquette requires a descriptive, traceable User-Agent.
    assert "YellowMind" in WikipediaConfig().user_agent
    assert "github.com" in WikipediaConfig().user_agent
