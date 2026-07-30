"""Unit tests for the stage use-case input record."""

from datetime import date

import pytest

from yellowmind.application.dto import StageRecord
from yellowmind.domain.entities import StageType


def _record(number: int = 1, distance_km: float = 182.0) -> StageRecord:
    return StageRecord(
        number=number,
        date=date(2023, 7, 1),
        stage_type=StageType.FLAT,
        distance_km=distance_km,
    )


@pytest.mark.parametrize("number", [0, 22, -1])
def test_rejects_a_number_outside_the_tour(number: int) -> None:
    """The Tour has run 21 stages in every edition since 2015."""
    with pytest.raises(ValueError, match="Stage number must be between 1 and 21"):
        _record(number=number)


def test_accepts_the_first_and_last_stage() -> None:
    assert _record(number=1).number == 1
    assert _record(number=21).number == 21


@pytest.mark.parametrize("distance_km", [0.0, -5.0])
def test_rejects_a_non_positive_distance(distance_km: float) -> None:
    with pytest.raises(ValueError, match="Stage distance must be positive"):
        _record(distance_km=distance_km)


def test_accepts_a_short_prologue_distance() -> None:
    """Opening time trials can be under 15 km."""
    assert _record(distance_km=13.8).distance_km == 13.8
