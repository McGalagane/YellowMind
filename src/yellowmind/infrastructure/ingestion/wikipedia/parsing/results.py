"""Parser for stage results and GC standings on stage-range articles.

Stage-range pages nest a real results table inside a wrapper that dumps the
same content into one cell. Only leaf tables (no nested ``table``) are read.

How a table is classified depends on the edition:

* **2018-2024** — captions ``Stage N Result`` / ``General classification after
  Stage N`` (casing varies).
* **2017** — same idea, plus a combined caption when stage 1 is an ITT:
  ``Stage 1 result & General classification after Stage 1``.
* **2015-2016** — no captions. Tables sit under a ``Stage N`` heading; the
  first rider-table is the stage result, the second is GC. A lone table
  (ITT) is both.

Team time trials use ``Rank | Team | Time`` and have no rider column. Their
stage results are skipped (``RaceResult`` requires a rider); GC after a TTT
is still rider-based and is kept.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final

from bs4 import BeautifulSoup, Tag

from yellowmind.application.dto import GcStandingRecord, StageResultRecord
from yellowmind.infrastructure.ingestion.wikipedia.parsing.html import (
    element_text,
    parse_html,
    parse_optional_int,
    row_cells,
    row_texts,
    wikilink_slug,
)
from yellowmind.infrastructure.ingestion.wikipedia.parsing.times import (
    TimeParseError,
    is_same_time,
    parse_gap_seconds,
    parse_time_cell,
)

_STAGE_RESULT_CAPTION: Final[re.Pattern[str]] = re.compile(
    r"^Stage\s+(?P<number>\d+)\s+result$", re.IGNORECASE
)
_GC_CAPTION: Final[re.Pattern[str]] = re.compile(
    r"^General classification after\s+[Ss]tage\s+(?P<number>\d+)$"
)
_COMBINED_CAPTION: Final[re.Pattern[str]] = re.compile(
    r"^Stage\s+(?P<number>\d+)\s+result\s*&"
    r"\s*General classification after\s+[Ss]tage\s+(?P=number)$",
    re.IGNORECASE,
)
_STAGE_HEADING: Final[re.Pattern[str]] = re.compile(r"^Stage\s+(?P<number>\d+)$", re.IGNORECASE)

_RIDER_HEADERS: Final[set[str]] = {"Rank", "Rider", "Team", "Time"}
_TEAM_HEADERS: Final[set[str]] = {"Rank", "Team", "Time"}


class ResultsParseError(Exception):
    """Raised when a results table cannot be read."""


@dataclass(frozen=True, slots=True)
class StageBoard:
    """Everything parsed for one stage from a stage-range page."""

    stage_number: int
    results: tuple[StageResultRecord, ...]
    gc: tuple[GcStandingRecord, ...]
    #: Why stage results were skipped, if they were (e.g. team time trial).
    results_skipped: str | None = None


@dataclass
class _StageAccumulator:
    """Mutable collector while walking the page's leaf tables."""

    results: list[StageResultRecord] = field(default_factory=list[StageResultRecord])
    gc: list[GcStandingRecord] = field(default_factory=list[GcStandingRecord])
    results_skipped: str | None = None


def parse_stage_boards(html: str) -> list[StageBoard]:
    """Parse every stage board from one stage-range article."""
    soup = parse_html(html)
    by_stage: dict[int, _StageAccumulator] = {}

    for table in _leaf_tables(soup):
        kind, number = _classify_table(table)
        if kind is None or number is None:
            continue

        acc = by_stage.setdefault(number, _StageAccumulator())
        headers = set(row_texts(table.find_all("tr")[0]))

        is_team_table = _TEAM_HEADERS.issubset(headers) and "Rider" not in headers
        if kind in {"result", "both"}:
            if is_team_table:
                acc.results_skipped = "team_time_trial"
            else:
                acc.results = _parse_result_rows(table, number)
                acc.results_skipped = None
        if kind in {"gc", "both"} and not is_team_table:
            # A combined ITT caption ("result & GC") uses one rider table for both.
            acc.gc = _parse_gc_rows(table, number)

    # Heading-based fallback for captionless editions (2015-2016): group leaf
    # rider-tables under each Stage N heading in document order.
    if not by_stage:
        by_stage = _parse_by_heading(soup)

    return [
        StageBoard(
            stage_number=number,
            results=tuple(acc.results),
            gc=tuple(acc.gc),
            results_skipped=acc.results_skipped,
        )
        for number, acc in sorted(by_stage.items())
    ]


def _leaf_tables(soup: BeautifulSoup) -> list[Tag]:
    """Return tables that contain no nested table."""
    return [t for t in soup.find_all("table") if t.find("table") is None]


def _previous_heading_text(table: Tag) -> str:
    """Return the text of the nearest preceding heading, if it is a tag."""
    prev = table.find_previous(["h2", "h3", "h4"])
    return element_text(prev) if isinstance(prev, Tag) else ""


def _classify_table(table: Tag) -> tuple[str | None, int | None]:
    """Return ``(kind, stage_number)`` from a caption, if any.

    ``kind`` is ``result``, ``gc``, ``both``, or ``None`` when the caption is
    absent or unrecognised (caller may fall back to headings).
    """
    caption = table.find("caption")
    if not isinstance(caption, Tag):
        return None, None
    text = element_text(caption)
    if not text:
        return None, None

    combined = _COMBINED_CAPTION.match(text)
    if combined is not None:
        return "both", int(combined.group("number"))

    result = _STAGE_RESULT_CAPTION.match(text)
    if result is not None:
        return "result", int(result.group("number"))

    gc = _GC_CAPTION.match(text)
    if gc is not None:
        return "gc", int(gc.group("number"))

    return None, None


def _parse_by_heading(soup: BeautifulSoup) -> dict[int, _StageAccumulator]:
    """Group captionless leaf rider-tables under each ``Stage N`` heading."""
    by_stage: dict[int, _StageAccumulator] = {}
    for table in _leaf_tables(soup):
        rows = table.find_all("tr")
        if not rows:
            continue
        headers = set(row_texts(rows[0]))
        if not _RIDER_HEADERS.issubset(headers):
            # TTT under a heading: record the skip, do not invent riders.
            if _TEAM_HEADERS.issubset(headers):
                match = _STAGE_HEADING.match(_previous_heading_text(table))
                if match is not None:
                    number = int(match.group("number"))
                    acc = by_stage.setdefault(number, _StageAccumulator())
                    # Only mark the skip when no rider result has been stored
                    # yet; some stages carry both a team table and a rider
                    # table under the same heading.
                    if not acc.results:
                        acc.results_skipped = "team_time_trial"
            continue

        match = _STAGE_HEADING.match(_previous_heading_text(table))
        if match is None:
            continue
        number = int(match.group("number"))
        acc = by_stage.setdefault(number, _StageAccumulator())
        parsed_results = _parse_result_rows(table, number)
        if not acc.results:
            acc.results = parsed_results
            acc.results_skipped = None
            # A lone table under the heading is an ITT: result = GC.
            acc.gc = [
                GcStandingRecord(
                    stage_number=r.stage_number,
                    rank=r.rank,
                    rider_name=r.rider_name,
                    rider_slug=r.rider_slug,
                    time=r.time,
                    time_gap_seconds=r.time_gap_seconds,
                )
                for r in parsed_results
            ]
        else:
            # Second table replaces the provisional GC copied from results.
            acc.gc = _parse_gc_rows(table, number)
    return by_stage


def _parse_result_rows(table: Tag, stage_number: int) -> list[StageResultRecord]:
    return [
        StageResultRecord(
            stage_number=stage_number,
            rank=row.rank,
            rider_name=row.name,
            rider_slug=row.slug,
            time=row.time,
            time_gap_seconds=row.gap_seconds,
        )
        for row in _iter_rider_rows(table)
    ]


def _parse_gc_rows(table: Tag, stage_number: int) -> list[GcStandingRecord]:
    return [
        GcStandingRecord(
            stage_number=stage_number,
            rank=row.rank,
            rider_name=row.name,
            rider_slug=row.slug,
            time=row.time,
            time_gap_seconds=row.gap_seconds,
        )
        for row in _iter_rider_rows(table)
    ]


@dataclass(frozen=True, slots=True)
class _RiderRow:
    rank: int
    name: str
    slug: str
    time: str
    gap_seconds: int


def _iter_rider_rows(table: Tag) -> list[_RiderRow]:
    """Yield ranked rider rows, skipping blanks and repeated headers."""
    rows = table.find_all("tr")
    if not rows:
        return []

    headers = row_texts(rows[0])
    try:
        rank_i = headers.index("Rank")
        rider_i = headers.index("Rider")
        time_i = headers.index("Time")
    except ValueError as exc:
        msg = f"Results table missing expected headers: {headers}"
        raise ResultsParseError(msg) from exc

    parsed: list[_RiderRow] = []
    previous_gap = 0
    for row in rows[1:]:
        cells = row_cells(row)
        if max(rank_i, rider_i, time_i) >= len(cells):
            continue
        rank = parse_optional_int(element_text(cells[rank_i]))
        if rank is None:
            continue
        name = _strip_nationality(element_text(cells[rider_i]))
        slug = wikilink_slug(cells[rider_i])
        if not slug:
            msg = f"Rank {rank} has no rider slug ({name!r})"
            raise ResultsParseError(msg)
        raw_time = element_text(cells[time_i])
        if is_same_time(raw_time):
            # 2016 prints ``s.t.`` for riders finishing on the same time as the
            # rider above; the gap is therefore unchanged.
            display, gap = "s.t.", previous_gap
        else:
            try:
                display, _ = parse_time_cell(raw_time)
                gap = parse_gap_seconds(raw_time)
            except TimeParseError as exc:
                msg = f"Rank {rank}: {exc}"
                raise ResultsParseError(msg) from exc
        previous_gap = gap
        parsed.append(_RiderRow(rank=rank, name=name, slug=slug, time=display, gap_seconds=gap))
    return parsed


def _strip_nationality(name: str) -> str:
    """Drop a trailing ``( GBR )`` nationality marker from a rider cell."""
    return re.sub(r"\s*\(\s*[A-Z]{3}\s*\)\s*$", "", name).strip()
