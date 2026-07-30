"""Wikipedia ingestion adapter."""

from yellowmind.infrastructure.ingestion.wikipedia.client import WikipediaClient
from yellowmind.infrastructure.ingestion.wikipedia.config import WikipediaConfig
from yellowmind.infrastructure.ingestion.wikipedia.dto import (
    Abandonment,
    AbandonmentKind,
    StartlistEntry,
)
from yellowmind.infrastructure.ingestion.wikipedia.parsing import (
    TableNotFoundError,
    parse_startlist,
)
from yellowmind.infrastructure.ingestion.wikipedia.urls import (
    edition_title,
    rest_html_path,
    stage_range_title,
    stage_range_titles,
    startlist_title,
)

__all__ = [
    "Abandonment",
    "AbandonmentKind",
    "StartlistEntry",
    "TableNotFoundError",
    "WikipediaClient",
    "WikipediaConfig",
    "edition_title",
    "parse_startlist",
    "rest_html_path",
    "stage_range_title",
    "stage_range_titles",
    "startlist_title",
]
