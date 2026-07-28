"""URL and page-title helpers for Tour de France Wikipedia articles.

Each edition spreads its data across three articles: an overview carrying the
route table and final classifications, and two stage-range articles carrying
per-stage results and the general classification after each stage.
"""

from urllib.parse import quote

_REST_HTML_PREFIX = "/api/rest_v1/page/html"

# Titles keep literal commas and underscores; percent-encoding them is accepted
# by the API but makes cache keys and logs harder to read.
_TITLE_SAFE_CHARS = ",_"

FIRST_STAGE_RANGE: tuple[int, int] = (1, 11)
SECOND_STAGE_RANGE: tuple[int, int] = (12, 21)


def edition_title(year: int) -> str:
    """Return the article title for an edition overview, e.g. ``2023_Tour_de_France``."""
    _validate_year(year)
    return f"{year}_Tour_de_France"


def stage_range_title(year: int, first_stage: int, last_stage: int) -> str:
    """Return the article title covering a contiguous range of stages."""
    _validate_year(year)
    if not 1 <= first_stage < last_stage:
        msg = f"Invalid stage range: {first_stage} to {last_stage}"
        raise ValueError(msg)
    return f"{year}_Tour_de_France,_Stage_{first_stage}_to_Stage_{last_stage}"


def stage_range_titles(year: int) -> tuple[str, str]:
    """Return both stage-range article titles for an edition."""
    return (
        stage_range_title(year, *FIRST_STAGE_RANGE),
        stage_range_title(year, *SECOND_STAGE_RANGE),
    )


def rest_html_path(title: str) -> str:
    """Return the REST API path serving an article's parsed HTML."""
    if not title:
        msg = "Article title cannot be empty"
        raise ValueError(msg)
    return f"{_REST_HTML_PREFIX}/{quote(title, safe=_TITLE_SAFE_CHARS)}"


def _validate_year(year: int) -> None:
    # The Tour began in 1903; anything earlier cannot have an article.
    if year < 1903:
        msg = f"Tour de France editions start in 1903, got {year}"
        raise ValueError(msg)
