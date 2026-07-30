"""Unit tests for cycling time-cell parsing."""

import pytest

from yellowmind.infrastructure.ingestion.wikipedia.parsing import (
    TimeParseError,
    parse_gap_seconds,
    parse_time_cell,
)
from yellowmind.infrastructure.ingestion.wikipedia.parsing.times import is_same_time


@pytest.mark.parametrize(
    ("raw", "seconds"),
    [
        ("4h 22' 49\"", 4 * 3600 + 22 * 60 + 49),
        ("14' 56\"", 14 * 60 + 56),
        ("45' 24\"", 45 * 60 + 24),
        ("83h 38' 56\"", 83 * 3600 + 38 * 60 + 56),
    ],
)
def test_parses_absolute_times(raw: str, seconds: int) -> None:
    display, value = parse_time_cell(raw)

    assert display == raw
    assert value == seconds
    assert parse_gap_seconds(raw) == 0


@pytest.mark.parametrize(
    ("raw", "seconds"),
    [
        ('+ 5"', 5),
        ('+ 0"', 0),
        ("+ 1' 10\"", 70),
        ('+ 10"', 10),
        ("+ 6' 17\"", 6 * 60 + 17),
    ],
)
def test_parses_gaps(raw: str, seconds: int) -> None:
    display, value = parse_time_cell(raw)

    assert display == raw
    assert value == seconds
    assert parse_gap_seconds(raw) == seconds


def test_accepts_typographic_primes() -> None:
    """Some editions use U+2032/U+2033 primes rather than ASCII quotes."""
    assert parse_gap_seconds("+ 1\u2032 10\u2033") == 70


def test_recognises_same_time_marker() -> None:
    assert is_same_time("s.t.")
    assert is_same_time("S.T.")
    assert not is_same_time('+ 0"')


def test_same_time_has_no_intrinsic_duration() -> None:
    with pytest.raises(TimeParseError, match="no intrinsic duration"):
        parse_time_cell("s.t.")


def test_rejects_unreadable_time() -> None:
    with pytest.raises(TimeParseError, match="Cannot read time"):
        parse_time_cell("soon")
