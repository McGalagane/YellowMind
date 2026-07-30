"""Parser for an edition's `Route and stages` table."""

import re
from datetime import date
from typing import Final

from bs4 import Tag

from yellowmind.application.dto import StageRecord
from yellowmind.domain.entities import StageType
from yellowmind.infrastructure.ingestion.wikipedia.parsing.html import (
    element_text,
    find_table_by_headers,
    header_index,
    header_span,
    parse_html,
    parse_optional_int,
    row_cells,
    span_text,
)

_ROUTE_HEADERS: Final[set[str]] = {"Stage", "Date", "Course", "Distance"}

# Terrain wording drifted over the decade: `Hilly stage` and `Medium mountain
# stage` name the same category, and 2023 hyphenates it. Every spelling below
# was collected from the ten editions 2015-2024 rather than assumed, and the
# counts accounted for all 210 stages.
_STAGE_TYPES: Final[dict[str, StageType]] = {
    "flat": StageType.FLAT,
    "flat stage": StageType.FLAT,
    "hilly stage": StageType.HILLY,
    "medium mountain stage": StageType.HILLY,
    "medium-mountain stage": StageType.HILLY,
    "mountain stage": StageType.MOUNTAIN,
    "high mountain stage": StageType.MOUNTAIN,
    "individual time trial": StageType.INDIVIDUAL_TT,
    "team time trial": StageType.TEAM_TT,
    "mountain time trial": StageType.MOUNTAIN_TT,
}

# Leading kilometre figure of a cell such as `193.5 km (120.2 mi)`. The comma
# group appears in the table's total row, which is not a stage.
_DISTANCE_KM: Final[re.Pattern[str]] = re.compile(r"([\d,]+(?:\.\d+)?)\s*km")

# A stage date carries a day and month but no year, e.g. `29 August`.
_DAY_AND_MONTH: Final[re.Pattern[str]] = re.compile(r"^(?P<day>\d{1,2})\s+(?P<month>[A-Za-z]+)$")

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


class StageParseError(Exception):
    """Raised when a stage row cannot be read."""


def parse_stages(html: str, year: int) -> list[StageRecord]:
    """Parse every stage from an edition's overview article.

    The year is supplied because the table's dates omit it.

    Rows that are not stages are skipped: rest days and the closing distance
    total share the table's markup but carry no stage number.

    Raises:
        StageParseError: If a stage row has an unreadable terrain, distance, or
            date. Skipping such a row would leave a gap that looks like the Tour
            simply had fewer stages.
    """
    table = find_table_by_headers(parse_html(html), _ROUTE_HEADERS)

    number_column = header_index(table, "Stage")
    date_column = header_index(table, "Date")
    distance_column = header_index(table, "Distance")
    # Named `Stage type` in 2018 and `Type` elsewhere, and spanning an icon cell
    # as well as a label cell in every edition.
    type_start, type_width = header_span(table, "Type", "Stage type")

    records: list[StageRecord] = []
    for row in table.find_all("tr")[1:]:
        cells = row_cells(row)
        number = _stage_number(cells, number_column)
        if number is None:
            continue

        records.append(
            StageRecord(
                number=number,
                date=_parse_stage_date(element_text(cells[date_column]), year, number),
                stage_type=_parse_stage_type(span_text(cells, type_start, type_width), number),
                distance_km=_parse_distance_km(element_text(cells[distance_column]), number),
            )
        )
    return records


def _stage_number(cells: list[Tag], column: int) -> int | None:
    """Return the row's stage number, or None when the row is not a stage."""
    if column >= len(cells):
        return None
    return parse_optional_int(element_text(cells[column]))


def _parse_stage_type(value: str, number: int) -> StageType:
    """Map a terrain label onto a stage type.

    Raises:
        StageParseError: If the label is unrecognised. Guessing would quietly
            mislabel terrain, which is a primary predictor of who wins.
    """
    stage_type = _STAGE_TYPES.get(value.strip().lower())
    if stage_type is None:
        msg = f"Unrecognised stage type {value!r} for stage {number}"
        raise StageParseError(msg)
    return stage_type


def _parse_distance_km(value: str, number: int) -> float:
    """Read the kilometre figure from a distance cell.

    Raises:
        StageParseError: If no kilometre figure is present.
    """
    match = _DISTANCE_KM.search(value)
    if match is None:
        msg = f"Cannot read distance from {value!r} for stage {number}"
        raise StageParseError(msg)
    return float(match.group(1).replace(",", ""))


def _parse_stage_date(value: str, year: int, number: int) -> date:
    """Resolve a day-and-month cell against the edition's year.

    Raises:
        StageParseError: If the cell is not a day and month.
    """
    match = _DAY_AND_MONTH.match(value.strip())
    if match is None:
        msg = f"Cannot read date from {value!r} for stage {number}"
        raise StageParseError(msg)

    month = _MONTHS.get(match["month"].lower())
    if month is None:
        msg = f"Unrecognised month {match['month']!r} for stage {number}"
        raise StageParseError(msg)

    try:
        return date(year, month, int(match["day"]))
    except ValueError as exc:
        msg = f"Invalid date {value!r} for stage {number}: {exc}"
        raise StageParseError(msg) from exc
