"""Unit tests for the rider participation entity and abandonment value object."""

from uuid import uuid4

import pytest

from yellowmind.domain.entities import RiderParticipation
from yellowmind.domain.value_objects import Abandonment, AbandonmentKind, StageNumber


def _participation(
    *,
    bib_number: int = 1,
    age: int | None = None,
    final_gc_position: int | None = None,
    abandonment: Abandonment | None = None,
    is_young_rider: bool = False,
) -> RiderParticipation:
    """Build a valid participation, overriding only the field under test."""
    return RiderParticipation(
        id=uuid4(),
        tour_edition_id=uuid4(),
        rider_id=uuid4(),
        team_id=uuid4(),
        bib_number=bib_number,
        age=age,
        final_gc_position=final_gc_position,
        abandonment=abandonment,
        is_young_rider=is_young_rider,
    )


def test_participation_defaults_to_unfinished_with_no_outcome() -> None:
    participation = _participation()

    assert participation.finished is False
    assert participation.abandonment is None
    assert participation.is_young_rider is False


def test_finisher_reports_finished() -> None:
    participation = _participation(final_gc_position=1)

    assert participation.finished is True


def test_abandonment_does_not_count_as_finished() -> None:
    participation = _participation(
        abandonment=Abandonment(AbandonmentKind.DID_NOT_FINISH, StageNumber(14))
    )

    assert participation.finished is False


def test_rider_cannot_both_place_and_abandon() -> None:
    with pytest.raises(ValueError, match="cannot both place"):
        _participation(
            final_gc_position=5,
            abandonment=Abandonment(AbandonmentKind.DID_NOT_FINISH),
        )


@pytest.mark.parametrize("bib_number", [0, -1])
def test_bib_number_must_be_positive(bib_number: int) -> None:
    with pytest.raises(ValueError, match="Bib number must be positive"):
        _participation(bib_number=bib_number)


@pytest.mark.parametrize("age", [0, -3])
def test_age_must_be_positive(age: int) -> None:
    with pytest.raises(ValueError, match="Age must be positive"):
        _participation(age=age)


def test_age_may_be_unknown() -> None:
    """Some editions omit age for a rider."""
    assert _participation(age=None).age is None


def test_gc_position_must_be_positive() -> None:
    with pytest.raises(ValueError, match="GC position must be positive"):
        _participation(final_gc_position=0)


def test_abandonment_stage_is_optional() -> None:
    """A did-not-start is not tied to a stage."""
    abandonment = Abandonment(AbandonmentKind.DID_NOT_START)

    assert abandonment.stage_number is None


def test_abandonment_rejects_out_of_range_stage() -> None:
    with pytest.raises(ValueError, match="Stage number must be between"):
        Abandonment(AbandonmentKind.DID_NOT_FINISH, StageNumber(22))


def test_abandonment_kind_values_are_stable() -> None:
    """Kinds are persisted as strings, so their values are part of the schema."""
    assert AbandonmentKind.OUTSIDE_TIME_LIMIT == "outside_time_limit"
    assert AbandonmentKind.COVID_WITHDRAWAL == "covid_withdrawal"
    assert AbandonmentKind.UNKNOWN == "unknown"
