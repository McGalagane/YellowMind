"""Tests for the startlist record invariants."""

import pytest

from yellowmind.infrastructure.ingestion.wikipedia.dto import (
    AbandonmentKind,
    ParsedAbandonment,
    StartlistEntry,
)


def make_entry(**overrides: object) -> StartlistEntry:
    """Build a valid entry, overriding individual fields per test."""
    fields: dict[str, object] = {
        "bib_number": 1,
        "rider_name": "Jonas Vingegaard",
        "rider_slug": "Jonas_Vingegaard",
        "nationality": "Denmark",
        "team_name": "Team Jumbo\u2013Visma",
        "team_slug": "Visma\u2013Lease_a_Bike_(men's_team)",
        "age": 26,
        "final_gc_position": 1,
        "abandonment": None,
        "is_young_rider": False,
    }
    fields.update(overrides)
    return StartlistEntry(**fields)  # pyright: ignore[reportArgumentType]


def test_finisher_reports_finished() -> None:
    assert make_entry().finished is True


def test_abandoning_rider_reports_not_finished() -> None:
    entry = make_entry(
        final_gc_position=None,
        abandonment=ParsedAbandonment(
            kind=AbandonmentKind.DID_NOT_FINISH, stage_number=8, raw_code="DNF"
        ),
    )

    assert entry.finished is False


def test_rider_cannot_both_place_and_abandon() -> None:
    with pytest.raises(ValueError, match="cannot both place and abandon"):
        make_entry(
            final_gc_position=3,
            abandonment=ParsedAbandonment(
                kind=AbandonmentKind.DID_NOT_FINISH, stage_number=8, raw_code="DNF"
            ),
        )


@pytest.mark.parametrize("bib", [0, -1])
def test_bib_number_must_be_positive(bib: int) -> None:
    with pytest.raises(ValueError, match="Bib number"):
        make_entry(bib_number=bib)


def test_rider_name_is_required() -> None:
    with pytest.raises(ValueError, match="Rider name"):
        make_entry(rider_name="")


def test_gc_position_must_be_positive() -> None:
    with pytest.raises(ValueError, match="GC position"):
        make_entry(final_gc_position=0)


def test_abandonment_stage_must_be_positive() -> None:
    with pytest.raises(ValueError, match="Stage number"):
        ParsedAbandonment(kind=AbandonmentKind.DID_NOT_FINISH, stage_number=0, raw_code="DNF")


def test_abandonment_requires_a_raw_code() -> None:
    with pytest.raises(ValueError, match="raw_code"):
        ParsedAbandonment(kind=AbandonmentKind.UNKNOWN, stage_number=None, raw_code="")


def test_abandonment_allows_absent_stage() -> None:
    abandonment = ParsedAbandonment(
        kind=AbandonmentKind.DISQUALIFIED, stage_number=None, raw_code="DSQ"
    )

    assert abandonment.stage_number is None
