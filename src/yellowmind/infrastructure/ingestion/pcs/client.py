"""ProCyclingStats HTTP client."""

import time
from typing import Final, Self

import httpx

from yellowmind.application.ports.cycling_data_source import CyclingDataSource
from yellowmind.infrastructure.ingestion.pcs.cache import FileResponseCache
from yellowmind.infrastructure.ingestion.pcs.config import PCSConfig
from yellowmind.infrastructure.ingestion.pcs.rate_limiter import RateLimiter

_RETRYABLE_STATUS_CODES: Final[frozenset[int]] = frozenset({429, 502, 503, 504})


class PCSClientError(Exception):
    """Raised when a PCS request fails after retries."""


class PCSClient(CyclingDataSource):
    """Rate-limited, cached HTTP client for ProCyclingStats."""

    def __init__(
        self,
        config: PCSConfig | None = None,
        *,
        http_client: httpx.Client | None = None,
        cache: FileResponseCache | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self._config = config or PCSConfig.from_env()
        self._http_client = http_client or httpx.Client(
            headers={"User-Agent": self._config.user_agent},
            timeout=self._config.timeout_seconds,
            follow_redirects=True,
        )
        self._owns_client = http_client is None
        self._cache = cache or FileResponseCache(self._config.cache_dir)
        self._rate_limiter = rate_limiter or RateLimiter(self._config.rate_limit_seconds)

    def fetch(self, path: str) -> str:
        """Fetch a PCS page by relative path or absolute URL."""
        url = self._build_url(path)

        cached = self._cache.get(url)
        if cached is not None:
            return cached

        self._rate_limiter.wait()
        content = self._request_with_retries(url)
        self._cache.set(url, content)
        return content

    def close(self) -> None:
        """Close the underlying HTTP client if owned by this instance."""
        if self._owns_client:
            self._http_client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _build_url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        normalized = path if path.startswith("/") else f"/{path}"
        return f"{self._config.base_url.rstrip('/')}{normalized}"

    def _request_with_retries(self, url: str) -> str:
        last_error: Exception | None = None

        for attempt in range(self._config.max_retries + 1):
            try:
                response = self._http_client.get(
                    url,
                    headers={"User-Agent": self._config.user_agent},
                )
                if response.status_code in _RETRYABLE_STATUS_CODES:
                    response.raise_for_status()
                response.raise_for_status()
                return response.text
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code not in _RETRYABLE_STATUS_CODES:
                    raise PCSClientError(f"PCS request failed: {url}") from exc
            except httpx.HTTPError as exc:
                last_error = exc
                raise PCSClientError(f"PCS request failed: {url}") from exc

            if attempt < self._config.max_retries:
                backoff = 2**attempt
                time.sleep(backoff)

        raise PCSClientError(f"PCS request failed after retries: {url}") from last_error
