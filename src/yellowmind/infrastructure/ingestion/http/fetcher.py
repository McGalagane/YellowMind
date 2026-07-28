"""Cached, rate-limited HTTP fetcher shared by ingestion adapters."""

import time
from collections.abc import Callable
from typing import Final, Self

import httpx

from yellowmind.infrastructure.ingestion.http.cache import FileResponseCache
from yellowmind.infrastructure.ingestion.http.rate_limiter import RateLimiter

RETRYABLE_STATUS_CODES: Final[frozenset[int]] = frozenset({429, 500, 502, 503, 504})

_MAX_RETRY_AFTER_SECONDS: Final[float] = 60.0


class HttpFetchError(Exception):
    """Raised when an HTTP request fails, including after exhausting retries."""


class CachedHttpFetcher:
    """Fetch pages over HTTP with caching, rate limiting, and bounded retries.

    Responses are cached on disk indefinitely: historical race data does not change,
    so a cache hit avoids re-requesting a page the provider has already served.
    """

    def __init__(
        self,
        *,
        base_url: str,
        user_agent: str,
        cache: FileResponseCache,
        rate_limiter: RateLimiter,
        max_retries: int = 3,
        timeout_seconds: float = 30.0,
        http_client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if max_retries < 0:
            msg = "max_retries cannot be negative"
            raise ValueError(msg)

        self._base_url = base_url.rstrip("/")
        self._user_agent = user_agent
        self._cache = cache
        self._rate_limiter = rate_limiter
        self._max_retries = max_retries
        self._sleep = sleep
        self._http_client = http_client or httpx.Client(
            timeout=timeout_seconds,
            follow_redirects=True,
        )
        self._owns_client = http_client is None

    def fetch(self, path: str) -> str:
        """Fetch a page by provider-relative path or absolute URL."""
        url = self.build_url(path)

        cached = self._cache.get(url)
        if cached is not None:
            return cached

        content = self._request_with_retries(url)
        self._cache.set(url, content)
        return content

    def build_url(self, path: str) -> str:
        """Resolve a relative path against the configured base URL."""
        if path.startswith(("http://", "https://")):
            return path
        normalized = path if path.startswith("/") else f"/{path}"
        return f"{self._base_url}{normalized}"

    def close(self) -> None:
        """Close the underlying HTTP client if this instance owns it."""
        if self._owns_client:
            self._http_client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request_with_retries(self, url: str) -> str:
        for attempt in range(self._max_retries + 1):
            self._rate_limiter.wait()

            try:
                response = self._http_client.get(
                    url,
                    headers={"User-Agent": self._user_agent},
                )
            except httpx.TransportError as exc:
                # Connection resets and timeouts are usually transient.
                if attempt >= self._max_retries:
                    msg = f"Request failed after {attempt + 1} attempts: {url}"
                    raise HttpFetchError(msg) from exc
                self._sleep(self._backoff_seconds(attempt, None))
                continue
            except httpx.HTTPError as exc:
                msg = f"Request failed: {url}"
                raise HttpFetchError(msg) from exc

            if response.status_code in RETRYABLE_STATUS_CODES:
                if attempt >= self._max_retries:
                    msg = (
                        f"Request failed after {attempt + 1} attempts "
                        f"(HTTP {response.status_code}): {url}"
                    )
                    raise HttpFetchError(msg)
                retry_after = _parse_retry_after(response.headers.get("Retry-After"))
                self._sleep(self._backoff_seconds(attempt, retry_after))
                continue

            if response.is_error:
                msg = f"Request failed (HTTP {response.status_code}): {url}"
                raise HttpFetchError(msg)

            return response.text

        # Unreachable: the loop either returns or raises on its final attempt.
        msg = f"Request failed: {url}"
        raise HttpFetchError(msg)

    @staticmethod
    def _backoff_seconds(attempt: int, retry_after: float | None) -> float:
        """Return the delay before the next attempt, preferring the server's hint."""
        if retry_after is not None:
            return min(retry_after, _MAX_RETRY_AFTER_SECONDS)
        return float(2**attempt)


def _parse_retry_after(value: str | None) -> float | None:
    """Parse a ``Retry-After`` header expressed in seconds.

    The HTTP-date form is ignored: providers used here send delta-seconds, and
    falling back to exponential backoff is a safe default.
    """
    if value is None:
        return None
    try:
        seconds = float(value)
    except ValueError:
        return None
    return seconds if seconds >= 0 else None
