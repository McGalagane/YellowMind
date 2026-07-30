"""Unit tests for mapping parsed startlist rows onto use-case inputs."""

from yellowmind.domain.value_objects import AbandonmentKind, StageNumber
from yellowmind.infrastructure.ingestion.wikipedia.dto import ParsedAbandonment, StartlistEntry
from yellowmind.infrastructure.ingestion.wikipedia.records import (
    startlist_entries_to_records,
    startlist_entry_to_record,
)


def _entry(
    *,
    final_gc_position: int | None = 1,
    abandonment: ParsedAbandonment | None = None,
) -> StartlistEntry:
    return StartlistEntry(
        bib_number=11,
        rider_name="Tadej Pogacar",
        rider_slug="Tadej_Poga\u010dar",
        nationality="Slovenia",
        team_name="UAE Team Emirates",
        team_slug="UAE_Team_Emirates",
        age=24,
        final_gc_position=final_gc_position,
        abandonment=abandonment,
        is_young_rider=True,
    )


def test_carries_every_field_across() -> None:
    record = startlist_entry_to_record(_entry())

    assert record.bib_number == 11
    assert record.rider_name == "Tadej Pogacar"
    assert record.rider_slug == "Tadej_Poga\u010dar"
    assert record.nationality == "Slovenia"
    assert record.team_name == "UAE Team Emirates"
    assert record.team_slug == "UAE_Team_Emirates"
    assert record.age == 24
    assert record.final_gc_position == 1
    assert record.is_young_rider is True


def test_narrows_abandonment_to_the_domain_value_object() -> None:
    entry = _entry(
        final_gc_position=None,
        abandonment=ParsedAbandonment(
            kind=AbandonmentKind.OUTSIDE_TIME_LIMIT, stage_number=17, raw_code="HD"
        ),
    )

    record = startlist_entry_to_record(entry)

    assert record.abandonment is not None
    assert record.abandonment.kind is AbandonmentKind.OUTSIDE_TIME_LIMIT
    assert record.abandonment.stage_number == StageNumber(17)


def test_drops_the_raw_source_token() -> None:
    """`HD` and `OTL` mean the same outcome; only the meaning travels onward."""
    hd = ParsedAbandonment(kind=AbandonmentKind.OUTSIDE_TIME_LIMIT, stage_number=9, raw_code="HD")
    otl = ParsedAbandonment(kind=AbandonmentKind.OUTSIDE_TIME_LIMIT, stage_number=9, raw_code="OTL")

    from_hd = startlist_entry_to_record(_entry(final_gc_position=None, abandonment=hd))
    from_otl = startlist_entry_to_record(_entry(final_gc_position=None, abandonment=otl))

    assert from_hd.abandonment == from_otl.abandonment


def test_abandonment_without_a_stage_stays_unset() -> None:
    entry = _entry(
        final_gc_position=None,
        abandonment=ParsedAbandonment(
            kind=AbandonmentKind.DID_NOT_START, stage_number=None, raw_code="DNS"
        ),
    )

    record = startlist_entry_to_record(entry)

    assert record.abandonment is not None
    assert record.abandonment.stage_number is None


def test_finisher_has_no_abandonment() -> None:
    assert startlist_entry_to_record(_entry()).abandonment is None


def test_maps_a_whole_startlist() -> None:
    records = startlist_entries_to_records([_entry(), _entry()])

    assert len(records) == 2
