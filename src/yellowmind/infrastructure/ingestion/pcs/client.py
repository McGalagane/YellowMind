"""ProCyclingStats HTTP client.

.. warning::
   PCS is behind Cloudflare bot protection and returns HTTP 403 to automated
   clients. This adapter is retained as an opt-in, local-only data source and is
   never enabled in CI or Docker defaults. See ADR-008.
"""

import httpx

from yellowmind.application.ports.cycling_data_source import CyclingDataSource
from yellowmind.infrastructure.ingestion.http import (
    CachedHttpFetcher,
    FileResponseCache,
    RateLimiter,
)
from yellowmind.infrastructure.ingestion.pcs.config import PCSConfig


class PCSClient(CyclingDataSource):
    """Rate-limited, cached HTTP client for ProCyclingStats."""

    def __init__(
        self,
        config: PCSConfig | None = None,
        *,
        http_client: httpx.Client | None = None,
        fetcher: CachedHttpFetcher | None = None,
    ) -> None:
        resolved = config or PCSConfig.from_env()
        self._fetcher = fetcher or CachedHttpFetcher(
            base_url=resolved.base_url,
            user_agent=resolved.user_agent,
            cache=FileResponseCache(resolved.cache_dir),
            rate_limiter=RateLimiter(resolved.rate_limit_seconds),
            max_retries=resolved.max_retries,
            timeout_seconds=resolved.timeout_seconds,
            http_client=http_client,
        )

    def fetch(self, path: str) -> str:
        """Fetch a PCS page by relative path or absolute URL."""
        return self._fetcher.fetch(path)

    def close(self) -> None:
        """Release the underlying HTTP resources."""
        self._fetcher.close()

    def __enter__(self) -> "PCSClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
