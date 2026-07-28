"""Wikipedia ingestion adapter."""

from yellowmind.infrastructure.ingestion.wikipedia.client import WikipediaClient
from yellowmind.infrastructure.ingestion.wikipedia.config import WikipediaConfig
from yellowmind.infrastructure.ingestion.wikipedia.urls import (
    edition_title,
    rest_html_path,
    stage_range_title,
    stage_range_titles,
)

__all__ = [
    "WikipediaClient",
    "WikipediaConfig",
    "edition_title",
    "rest_html_path",
    "stage_range_title",
    "stage_range_titles",
]
