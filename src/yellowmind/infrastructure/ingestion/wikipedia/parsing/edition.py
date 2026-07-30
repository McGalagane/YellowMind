"""Parser for an edition's overview article.

Edition dates come from the infobox rather than the `Route and stages` table,
so this stays independent of stage ingestion.
"""

import re
from datetime import date
from typing import Final

from yellowmind.application.dto import EditionRecord
from yellowmind.infrastructure.ingestion.wikipedia.parsing.html import (
    TableNotFoundError,
    find_infobox,
    infobox_value,
    parse_html,
)

_DATES_LABEL: Final[str] = "Dates"

# Month names are mapped explicitly rather than parsed with `strptime("%B")`,
# which resolves against the active locale and would fail wherever the process
# does not run in English.
_MONTHS: Final[dict[str, int]] = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

# Editions separate their two dates with an en dash, an em dash, or a plain
# hyphen depending on who last edited the article; 2020 uses an em dash while
# every other edition between 2015 and 2024 uses an en dash.
_RANGE_SEPARATOR: Final[re.Pattern[str]] = re.compile(r"\s*[\u2013\u2014-]\s*")

# The closing date always carries day, month and year. The opening date carries
# a day, and a month only when the edition spans two of them.
_END_DATE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<day>\d{1,2})\s+(?P<month>[A-Za-z]+)\s+(?P<year>\d{4})$"
)
_START_DATE: Final[re.Pattern[str]] = re.compile(r"^(?P<day>\d{1,2})(?:\s+(?P<month>[A-Za-z]+))?$")


class EditionParseError(Exception):
    """Raised when an overview article's dates cannot be read."""


def parse_edition(html: str) -> EditionRecord:
    """Read an edition's year and duration from its overview article.

    Raises:
        EditionParseError: If the infobox has no readable date range.
    """
    soup = parse_html(html)
    try:
        infobox = find_infobox(soup)
    except TableNotFoundError as exc:
        msg = "Overview article has no infobox"
        raise EditionParseError(msg) from exc

    raw_dates = infobox_value(infobox, _DATES_LABEL)
    if not raw_dates:
        msg = "Infobox has no 'Dates' row"
        raise EditionParseError(msg)

    start_date, end_date = _parse_date_range(raw_dates)
    # The year is taken from the closing date rather than supplied by the
    # caller, so a mismatched or misfetched article surfaces as a validation
    # error instead of being stored against the wrong edition.
    return EditionRecord(year=end_date.year, start_date=start_date, end_date=end_date)


def _parse_date_range(value: str) -> tuple[date, date]:
    """Split a range such as ``29 August - 20 September 2020`` into two dates."""
    parts = _RANGE_SEPARATOR.split(value.strip())
    if len(parts) != 2:
        msg = f"Expected a date range, got {value!r}"
        raise EditionParseError(msg)

    start_text, end_text = parts

    end_match = _END_DATE.match(end_text)
    if end_match is None:
        msg = f"Cannot read closing date from {value!r}"
        raise EditionParseError(msg)
    end_date = _build_date(
        day=int(end_match["day"]),
        month_name=end_match["month"],
        year=int(end_match["year"]),
        source=value,
    )

    start_match = _START_DATE.match(start_text)
    if start_match is None:
        msg = f"Cannot read opening date from {value!r}"
        raise EditionParseError(msg)
    # An omitted month means the edition begins and ends in the same one.
    start_date = _build_date(
        day=int(start_match["day"]),
        month_name=start_match["month"] or end_match["month"],
        year=end_date.year,
        source=value,
    )

    return start_date, end_date


def _build_date(*, day: int, month_name: str, year: int, source: str) -> date:
    """Assemble a date from its parts, reporting the original text on failure."""
    month = _MONTHS.get(month_name.lower())
    if month is None:
        msg = f"Unrecognised month {month_name!r} in {source!r}"
        raise EditionParseError(msg)

    try:
        return date(year, month, day)
    except ValueError as exc:
        msg = f"Invalid date in {source!r}: {exc}"
        raise EditionParseError(msg) from exc
