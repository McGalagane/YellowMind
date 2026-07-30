"""Map the parsers' source-shaped records onto use-case inputs.

Keeping this step in the adapter is what lets the application layer stay free of
any knowledge of Wikipedia's markup or notation.
"""

from collections.abc import Iterable

from yellowmind.application.dto import StartlistRecord
from yellowmind.domain.value_objects import Abandonment, StageNumber
from yellowmind.infrastructure.ingestion.wikipedia.dto import ParsedAbandonment, StartlistEntry


def startlist_entry_to_record(entry: StartlistEntry) -> StartlistRecord:
    """Convert one parsed startlist row into a use-case input."""
    return StartlistRecord(
        bib_number=entry.bib_number,
        rider_name=entry.rider_name,
        rider_slug=entry.rider_slug,
        nationality=entry.nationality,
        team_name=entry.team_name,
        team_slug=entry.team_slug,
        age=entry.age,
        final_gc_position=entry.final_gc_position,
        abandonment=_abandonment_to_domain(entry.abandonment),
        is_young_rider=entry.is_young_rider,
    )


def startlist_entries_to_records(entries: Iterable[StartlistEntry]) -> list[StartlistRecord]:
    """Convert a whole startlist into use-case inputs."""
    return [startlist_entry_to_record(entry) for entry in entries]


def _abandonment_to_domain(parsed: ParsedAbandonment | None) -> Abandonment | None:
    """Narrow a parsed marker to the domain value object.

    The raw source token is dropped here: it exists to keep `HD` and `OTL`
    distinguishable while parsing, and to make an unrecognised marker
    diagnosable, neither of which anything downstream needs.
    """
    if parsed is None:
        return None
    return Abandonment(
        kind=parsed.kind,
        stage_number=(
            StageNumber(parsed.stage_number) if parsed.stage_number is not None else None
        ),
    )
