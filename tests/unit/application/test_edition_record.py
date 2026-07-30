"""Unit tests for the edition use-case input record."""

from datetime import date

import pytest

from yellowmind.application.dto import EditionRecord


def test_accepts_an_edition_spanning_two_months() -> None:
    """2020 ran from August into September."""
    record = EditionRecord(year=2020, start_date=date(2020, 8, 29), end_date=date(2020, 9, 20))

    assert record.start_date.month != record.end_date.month


def test_rejects_end_before_start() -> None:
    with pytest.raises(ValueError, match="ends before it starts"):
        EditionRecord(year=2023, start_date=date(2023, 7, 23), end_date=date(2023, 7, 1))


def test_rejects_end_date_in_another_year() -> None:
    """Guards against a parsed range being stored against the wrong edition."""
    with pytest.raises(ValueError, match="ends in 2022"):
        EditionRecord(year=2023, start_date=date(2022, 7, 1), end_date=date(2022, 7, 23))


def test_allows_a_single_day_edition() -> None:
    """Not a real Tour, but the record should not forbid it arbitrarily."""
    record = EditionRecord(year=2023, start_date=date(2023, 7, 1), end_date=date(2023, 7, 1))

    assert record.start_date == record.end_date
