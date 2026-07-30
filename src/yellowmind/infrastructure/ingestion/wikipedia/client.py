"""Wikipedia REST API client.

Primary data source for historical Tour de France results, per ADR-008. The REST
HTML endpoint is preferred over raw wikitext because its markup is normalised and
therefore far more stable to parse.
"""

import httpx

from yellowmind.application.ports.cycling_data_source import CyclingDataSource
from yellowmind.infrastructure.ingestion.http import (
    CachedHttpFetcher,
    FileResponseCache,
    RateLimiter,
)
from yellowmind.infrastructure.ingestion.wikipedia.config import WikipediaConfig
from yellowmind.infrastructure.ingestion.wikipedia.urls import (
    edition_title,
    rest_html_path,
    stage_range_titles,
    startlist_title,
)


class WikipediaClient(CyclingDataSource):
    """Rate-limited, cached client for the Wikipedia REST API.

    Rate limiting is required rather than merely polite: the API answers burst
    traffic with HTTP 429.
    """

    def __init__(
        self,
        config: WikipediaConfig | None = None,
        *,
        http_client: httpx.Client | None = None,
        fetcher: CachedHttpFetcher | None = None,
    ) -> None:
        resolved = config or WikipediaConfig.from_env()
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
        """Fetch a page by relative path or absolute URL."""
        return self._fetcher.fetch(path)

    def fetch_article(self, title: str) -> str:
        """Fetch an article's parsed HTML by title."""
        return self.fetch(rest_html_path(title))

    def fetch_edition_page(self, year: int) -> str:
        """Fetch the overview article for a Tour de France edition."""
        return self.fetch_article(edition_title(year))

    def fetch_startlist_page(self, year: int) -> str:
        """Fetch the article listing every team and rider for an edition."""
        return self.fetch_article(startlist_title(year))

    def fetch_stage_pages(self, year: int) -> tuple[str, str]:
        """Fetch both stage-range articles for an edition."""
        first, second = stage_range_titles(year)
        return self.fetch_article(first), self.fetch_article(second)

    def close(self) -> None:
        """Release the underlying HTTP resources."""
        self._fetcher.close()

    def __enter__(self) -> "WikipediaClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
