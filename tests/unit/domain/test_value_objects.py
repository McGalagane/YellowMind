"""Tests for domain value objects."""

import pytest

from yellowmind.domain.value_objects import Distance, Probability, StageNumber


def test_stage_number_valid() -> None:
    stage = StageNumber(10)
    assert stage.value == 10


@pytest.mark.parametrize("value", [0, 22, -1])
def test_stage_number_invalid(value: int) -> None:
    with pytest.raises(ValueError, match="Stage number"):
        StageNumber(value)


def test_probability_valid() -> None:
    prob = Probability(0.5)
    assert prob.value == 0.5


@pytest.mark.parametrize("value", [-0.1, 1.1])
def test_probability_invalid(value: float) -> None:
    with pytest.raises(ValueError, match="Probability"):
        Probability(value)


def test_distance_valid() -> None:
    distance = Distance(182.5)
    assert distance.kilometres == 182.5


def test_distance_invalid() -> None:
    with pytest.raises(ValueError, match="Distance"):
        Distance(0)
