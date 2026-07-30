"""Parser for an edition's startlist article.

The article ``List of teams and cyclists in the {year} Tour de France`` carries
the complete field in one flat table, including each rider's team, nationality,
final placing, and — for those who did not reach Paris — why and when they left.
"""

import re
from dataclasses import dataclass
from typing import Final

from bs4 import BeautifulSoup, Tag

from yellowmind.infrastructure.ingestion.wikipedia.dto import (
    ABANDONMENT_CODES,
    AbandonmentKind,
    ParsedAbandonment,
    StartlistEntry,
)
from yellowmind.infrastructure.ingestion.wikipedia.parsing.html import (
    clean_text,
    element_text,
    find_table_by_headers,
    header_index,
    parse_html,
    parse_optional_int,
    row_cells,
    wikilink_slug,
)

# Identifies the flat startlist table. Deliberately a subset of the real header
# row so the match survives trailing columns changing name between editions.
_STARTLIST_HEADERS: Final[set[str]] = {"No.", "Name", "Nationality", "Team"}

# A `Pos.` marker such as `DNF-14`, `DNS-18`, or a bare `DSQ`. The stage number
# is separated by a hyphen or an en dash depending on the edition.
_ABANDONMENT: Final[re.Pattern[str]] = re.compile(
    r"^(?P<code>[A-Za-z]+)(?:[-\u2013](?P<stage>\d+))?$"
)

# Marks riders eligible for the young rider classification.
_YOUNG_RIDER_MARKER: Final[str] = "\u2021"


def parse_startlist(html: str) -> list[StartlistEntry]:
    """Parse every rider from a startlist article.

    Rows without a usable bib number are skipped: the table's own legend and
    grouping rows share its markup but carry no rider.
    """
    soup: BeautifulSoup = parse_html(html)
    table = find_table_by_headers(soup, _STARTLIST_HEADERS)

    columns = _StartlistColumns.from_table(table)
    rows = table.find_all("tr")

    entries: list[StartlistEntry] = []
    for row in rows[1:]:
        entry = _parse_row(row, columns)
        if entry is not None:
            entries.append(entry)
    return entries


@dataclass(frozen=True, slots=True)
class _StartlistColumns:
    """Resolved column positions for one startlist table."""

    bib: int
    name: int
    nationality: int
    team: int
    age: int
    position: int

    @classmethod
    def from_table(cls, table: Tag) -> "_StartlistColumns":
        """Locate each needed column by its header text."""
        return cls(
            bib=header_index(table, "No."),
            name=header_index(table, "Name"),
            nationality=header_index(table, "Nationality"),
            team=header_index(table, "Team"),
            age=header_index(table, "Age"),
            position=header_index(table, "Pos."),
        )

    @property
    def highest_index(self) -> int:
        """Largest column index this parser reads."""
        return max(self.bib, self.name, self.nationality, self.team, self.age, self.position)


def _parse_row(row: Tag, columns: _StartlistColumns) -> StartlistEntry | None:
    cells = row_cells(row)
    if len(cells) <= columns.highest_index:
        return None

    bib = parse_optional_int(element_text(cells[columns.bib]))
    if bib is None:
        return None

    raw_name = element_text(cells[columns.name])
    position_text = element_text(cells[columns.position])
    final_position = parse_optional_int(position_text)

    return StartlistEntry(
        bib_number=bib,
        rider_name=_strip_markers(raw_name),
        rider_slug=wikilink_slug(cells[columns.name]),
        nationality=element_text(cells[columns.nationality]),
        team_name=element_text(cells[columns.team]),
        team_slug=wikilink_slug(cells[columns.team]),
        age=parse_optional_int(element_text(cells[columns.age])),
        final_gc_position=final_position,
        # A rider either has a placing or a reason for not having one.
        abandonment=None if final_position is not None else parse_abandonment(position_text),
        is_young_rider=_YOUNG_RIDER_MARKER in raw_name,
    )


def parse_abandonment(value: str) -> ParsedAbandonment | None:
    """Parse a `Pos.` marker into an abandonment, or None if it is not one."""
    text = clean_text(value)
    if not text:
        return None

    match = _ABANDONMENT.match(text)
    if match is None:
        return None

    code = match.group("code").upper()
    stage = match.group("stage")
    return ParsedAbandonment(
        kind=ABANDONMENT_CODES.get(code, AbandonmentKind.UNKNOWN),
        stage_number=int(stage) if stage is not None else None,
        raw_code=code,
    )


def _strip_markers(name: str) -> str:
    """Remove classification markers from a rider's name."""
    return clean_text(name.replace(_YOUNG_RIDER_MARKER, " "))
