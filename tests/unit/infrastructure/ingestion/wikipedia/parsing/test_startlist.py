"""Tests for the startlist parser."""

from pathlib import Path

import pytest

from yellowmind.infrastructure.ingestion.wikipedia.dto import (
    AbandonmentKind,
    StartlistEntry,
)
from yellowmind.infrastructure.ingestion.wikipedia.parsing import (
    TableNotFoundError,
    parse_startlist,
)
from yellowmind.infrastructure.ingestion.wikipedia.parsing.startlist import (
    parse_abandonment,
)

FIXTURE = Path(__file__).parents[5] / "fixtures" / "wikipedia" / "startlist_sample.html"


@pytest.fixture(scope="module")
def entries() -> list[StartlistEntry]:
    return parse_startlist(FIXTURE.read_text(encoding="utf-8"))


def by_bib(entries: list[StartlistEntry], bib: int) -> StartlistEntry:
    return next(entry for entry in entries if entry.bib_number == bib)


def test_parses_every_rider_row(entries: list[StartlistEntry]) -> None:
    assert len(entries) == 10


def test_skips_rows_without_a_rider(entries: list[StartlistEntry]) -> None:
    # The legend table and the "UCI WorldTeams" grouping row share the markup.
    assert all(entry.rider_name for entry in entries)
    assert "UCI WorldTeams" not in {entry.rider_name for entry in entries}


def test_parses_a_finisher(entries: list[StartlistEntry]) -> None:
    winner = by_bib(entries, 1)

    assert winner.rider_name == "Jonas Vingegaard"
    assert winner.rider_slug == "Jonas_Vingegaard"
    assert winner.nationality == "Denmark"
    assert winner.age == 26
    assert winner.final_gc_position == 1
    assert winner.abandonment is None
    assert winner.finished is True


def test_keeps_historical_team_name_and_current_slug(entries: list[StartlistEntry]) -> None:
    # The 2023 article prints the name used that year but links the article's
    # present title, so both are needed.
    winner = by_bib(entries, 1)

    assert winner.team_name == "Team Jumbo\u2013Visma"
    assert winner.team_slug == "Visma\u2013Lease_a_Bike_(men's_team)"


def test_strips_footnote_markers_from_cells(entries: list[StartlistEntry]) -> None:
    disqualified = by_bib(entries, 88)

    assert disqualified.abandonment is not None
    assert disqualified.abandonment.raw_code == "DSQ"
    assert disqualified.abandonment.stage_number == 15


def test_detects_young_rider_marker(entries: list[StartlistEntry]) -> None:
    marked = by_bib(entries, 76)

    assert marked.is_young_rider is True
    # The dagger must not survive into the name.
    assert marked.rider_name == "Ben Turner"


def test_unmarked_rider_is_not_flagged_young(entries: list[StartlistEntry]) -> None:
    assert by_bib(entries, 1).is_young_rider is False


def test_parses_did_not_finish(entries: list[StartlistEntry]) -> None:
    cavendish = by_bib(entries, 131)

    assert cavendish.final_gc_position is None
    assert cavendish.finished is False
    assert cavendish.abandonment is not None
    assert cavendish.abandonment.kind is AbandonmentKind.DID_NOT_FINISH
    assert cavendish.abandonment.stage_number == 8


def test_parses_did_not_start(entries: list[StartlistEntry]) -> None:
    van_aert = by_bib(entries, 5)

    assert van_aert.abandonment is not None
    assert van_aert.abandonment.kind is AbandonmentKind.DID_NOT_START
    assert van_aert.abandonment.stage_number == 18


def test_hd_and_otl_share_one_kind_but_keep_their_codes(
    entries: list[StartlistEntry],
) -> None:
    hors_delai = by_bib(entries, 92)
    outside_limit = by_bib(entries, 93)

    assert hors_delai.abandonment is not None
    assert outside_limit.abandonment is not None
    assert hors_delai.abandonment.kind is AbandonmentKind.OUTSIDE_TIME_LIMIT
    assert outside_limit.abandonment.kind is AbandonmentKind.OUTSIDE_TIME_LIMIT
    assert hors_delai.abandonment.raw_code == "HD"
    assert outside_limit.abandonment.raw_code == "OTL"


def test_parses_covid_withdrawal(entries: list[StartlistEntry]) -> None:
    covid = by_bib(entries, 94)

    assert covid.abandonment is not None
    assert covid.abandonment.kind is AbandonmentKind.COVID_WITHDRAWAL
    assert covid.abandonment.stage_number == 9


def test_marker_without_a_stage_number(entries: list[StartlistEntry]) -> None:
    bare = by_bib(entries, 95)

    assert bare.abandonment is not None
    assert bare.abandonment.kind is AbandonmentKind.DISQUALIFIED
    assert bare.abandonment.stage_number is None


def test_missing_age_is_none(entries: list[StartlistEntry]) -> None:
    assert by_bib(entries, 92).age is None


def test_raises_when_no_startlist_table_present() -> None:
    with pytest.raises(TableNotFoundError, match="No table found"):
        parse_startlist("<html><body><p>No tables here.</p></body></html>")


@pytest.mark.parametrize(
    ("marker", "kind", "stage"),
    [
        ("DNF-14", AbandonmentKind.DID_NOT_FINISH, 14),
        ("DNS-18", AbandonmentKind.DID_NOT_START, 18),
        ("HD-3", AbandonmentKind.OUTSIDE_TIME_LIMIT, 3),
        ("OTL-7", AbandonmentKind.OUTSIDE_TIME_LIMIT, 7),
        ("COV-9", AbandonmentKind.COVID_WITHDRAWAL, 9),
        ("DSQ", AbandonmentKind.DISQUALIFIED, None),
        # En dash separator appears in some editions.
        ("DNF\u201321", AbandonmentKind.DID_NOT_FINISH, 21),
    ],
)
def test_parse_abandonment_known_markers(
    marker: str,
    kind: AbandonmentKind,
    stage: int | None,
) -> None:
    result = parse_abandonment(marker)

    assert result is not None
    assert result.kind is kind
    assert result.stage_number == stage


def test_parse_abandonment_unrecognised_code_is_preserved() -> None:
    result = parse_abandonment("XYZ-5")

    assert result is not None
    assert result.kind is AbandonmentKind.UNKNOWN
    assert result.raw_code == "XYZ"
    assert result.stage_number == 5


@pytest.mark.parametrize("value", ["", "   ", "12", "+ 4'"])
def test_parse_abandonment_returns_none_for_non_markers(value: str) -> None:
    assert parse_abandonment(value) is None
