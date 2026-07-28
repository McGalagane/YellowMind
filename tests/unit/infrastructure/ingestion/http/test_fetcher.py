"""Tests for the shared cached HTTP fetcher."""

from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from yellowmind.infrastructure.ingestion.http import (
    CachedHttpFetcher,
    FileResponseCache,
    HttpFetchError,
    RateLimiter,
)

BASE_URL = "https://example.test"


def build_fetcher(
    handler: Callable[[httpx.Request], httpx.Response],
    cache_dir: Path,
    *,
    max_retries: int = 2,
    sleeps: list[float] | None = None,
) -> CachedHttpFetcher:
    """Build a fetcher wired to a mock transport and an isolated cache."""
    recorded = sleeps if sleeps is not None else []
    return CachedHttpFetcher(
        base_url=BASE_URL,
        user_agent="TestAgent/1.0",
        cache=FileResponseCache(cache_dir),
        rate_limiter=RateLimiter(0),
        max_retries=max_retries,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=recorded.append,
    )


def test_build_url_joins_relative_path(tmp_path: Path) -> None:
    fetcher = build_fetcher(lambda _: httpx.Response(200), tmp_path)

    assert fetcher.build_url("page") == f"{BASE_URL}/page"
    assert fetcher.build_url("/page") == f"{BASE_URL}/page"


def test_build_url_passes_through_absolute_url(tmp_path: Path) -> None:
    fetcher = build_fetcher(lambda _: httpx.Response(200), tmp_path)

    assert fetcher.build_url("https://other.test/x") == "https://other.test/x"


def test_fetch_sends_configured_user_agent(tmp_path: Path) -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers["User-Agent"])
        return httpx.Response(200, text="<html>ok</html>")

    content = build_fetcher(handler, tmp_path).fetch("/page")

    assert content == "<html>ok</html>"
    assert seen == ["TestAgent/1.0"]


def test_fetch_returns_cached_response_without_http_call(tmp_path: Path) -> None:
    cache = FileResponseCache(tmp_path)
    cache.set(f"{BASE_URL}/page", "<html>cached</html>")

    requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return httpx.Response(200, text="<html>live</html>")

    content = build_fetcher(handler, tmp_path).fetch("/page")

    assert content == "<html>cached</html>"
    assert requests == 0


def test_fetch_caches_response_for_reuse(tmp_path: Path) -> None:
    requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return httpx.Response(200, text="<html>ok</html>")

    fetcher = build_fetcher(handler, tmp_path)

    assert fetcher.fetch("/page") == fetcher.fetch("/page")
    assert requests == 1


def test_fetch_retries_retryable_status(tmp_path: Path) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, text="unavailable")
        return httpx.Response(200, text="<html>ok</html>")

    sleeps: list[float] = []
    content = build_fetcher(handler, tmp_path, sleeps=sleeps).fetch("/page")

    assert content == "<html>ok</html>"
    assert attempts == 2
    assert sleeps == [1.0]


def test_fetch_honours_retry_after_header(tmp_path: Path) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, text="slow down", headers={"Retry-After": "7"})
        return httpx.Response(200, text="<html>ok</html>")

    sleeps: list[float] = []
    build_fetcher(handler, tmp_path, sleeps=sleeps).fetch("/page")

    assert sleeps == [7.0]


def test_fetch_ignores_unparsable_retry_after(tmp_path: Path) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            date_form = "Wed, 21 Oct 2015 07:28:00 GMT"
            return httpx.Response(429, headers={"Retry-After": date_form})
        return httpx.Response(200, text="<html>ok</html>")

    sleeps: list[float] = []
    build_fetcher(handler, tmp_path, sleeps=sleeps).fetch("/page")

    assert sleeps == [1.0]


def test_fetch_caps_excessive_retry_after(tmp_path: Path) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(429, headers={"Retry-After": "9999"})
        return httpx.Response(200, text="<html>ok</html>")

    sleeps: list[float] = []
    build_fetcher(handler, tmp_path, sleeps=sleeps).fetch("/page")

    assert sleeps == [60.0]


def test_fetch_raises_after_exhausting_retries(tmp_path: Path) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, text="unavailable")

    fetcher = build_fetcher(handler, tmp_path, max_retries=2)

    with pytest.raises(HttpFetchError, match="after 3 attempts"):
        fetcher.fetch("/page")

    assert attempts == 3


def test_fetch_does_not_retry_client_error(tmp_path: Path) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(404, text="not found")

    fetcher = build_fetcher(handler, tmp_path)

    with pytest.raises(HttpFetchError, match="HTTP 404"):
        fetcher.fetch("/page")

    assert attempts == 1


def test_fetch_retries_transport_error(tmp_path: Path) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ConnectTimeout("timed out", request=request)
        return httpx.Response(200, text="<html>ok</html>")

    assert build_fetcher(handler, tmp_path).fetch("/page") == "<html>ok</html>"
    assert attempts == 2


def test_fetch_raises_when_transport_error_persists(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out", request=request)

    fetcher = build_fetcher(handler, tmp_path, max_retries=1)

    with pytest.raises(HttpFetchError, match="after 2 attempts"):
        fetcher.fetch("/page")


def test_failed_fetch_is_not_cached(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    fetcher = build_fetcher(handler, tmp_path)
    with pytest.raises(HttpFetchError):
        fetcher.fetch("/page")

    assert FileResponseCache(tmp_path).get(f"{BASE_URL}/page") is None


def test_negative_max_retries_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="max_retries"):
        CachedHttpFetcher(
            base_url=BASE_URL,
            user_agent="TestAgent/1.0",
            cache=FileResponseCache(tmp_path),
            rate_limiter=RateLimiter(0),
            max_retries=-1,
        )


def test_context_manager_closes_owned_client(tmp_path: Path) -> None:
    with CachedHttpFetcher(
        base_url=BASE_URL,
        user_agent="TestAgent/1.0",
        cache=FileResponseCache(tmp_path),
        rate_limiter=RateLimiter(0),
    ) as fetcher:
        assert fetcher.build_url("/page") == f"{BASE_URL}/page"


def test_injected_client_is_left_open_for_its_owner(tmp_path: Path) -> None:
    http_client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200)))
    fetcher = CachedHttpFetcher(
        base_url=BASE_URL,
        user_agent="TestAgent/1.0",
        cache=FileResponseCache(tmp_path),
        rate_limiter=RateLimiter(0),
        http_client=http_client,
    )

    fetcher.close()

    assert not http_client.is_closed
