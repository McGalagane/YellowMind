"""Unit tests for the startlist ingestion use case."""

from datetime import date
from uuid import uuid4

import pytest
from tests.unit.application.doubles import (
    InMemoryRiderParticipationRepository,
    InMemoryRiderRepository,
    InMemoryTeamRepository,
)

from yellowmind.application.dto import StartlistRecord
from yellowmind.application.use_cases import DuplicateRiderError, IngestStartlist
from yellowmind.domain.entities import TourEdition
from yellowmind.domain.value_objects import Abandonment, AbandonmentKind, StageNumber


def _edition(year: int = 2023) -> TourEdition:
    return TourEdition(
        id=uuid4(),
        year=year,
        name=f"Tour de France {year}",
        start_date=date(year, 7, 1),
        end_date=date(year, 7, 23),
    )


def _record(
    *,
    bib_number: int = 1,
    rider_name: str = "Jonas Vingegaard",
    rider_slug: str = "Jonas_Vingegaard",
    nationality: str = "Denmark",
    team_name: str = "Team Jumbo-Visma",
    team_slug: str = "Visma-Lease_a_Bike",
    age: int | None = 26,
    final_gc_position: int | None = 1,
    abandonment: Abandonment | None = None,
    is_young_rider: bool = False,
) -> StartlistRecord:
    return StartlistRecord(
        bib_number=bib_number,
        rider_name=rider_name,
        rider_slug=rider_slug,
        nationality=nationality,
        team_name=team_name,
        team_slug=team_slug,
        age=age,
        final_gc_position=final_gc_position,
        abandonment=abandonment,
        is_young_rider=is_young_rider,
    )


class _Fixture:
    """A use case wired to fresh in-memory repositories."""

    def __init__(self) -> None:
        self.riders = InMemoryRiderRepository()
        self.teams = InMemoryTeamRepository()
        self.participations = InMemoryRiderParticipationRepository()
        self.use_case = IngestStartlist(self.riders, self.teams, self.participations)


def test_stores_rider_team_and_participation() -> None:
    fixture = _Fixture()
    edition = _edition()

    summary = fixture.use_case.execute(edition, [_record()])

    assert summary.riders_created == 1
    assert summary.teams_created == 1
    assert summary.participations == 1
    assert len(fixture.riders.rows) == 1
    assert len(fixture.teams.rows) == 1

    stored = fixture.participations.list_by_edition(edition.id)
    assert len(stored) == 1
    assert stored[0].bib_number == 1
    assert stored[0].final_gc_position == 1


def test_riders_on_the_same_team_share_one_team_row() -> None:
    fixture = _Fixture()

    summary = fixture.use_case.execute(
        _edition(),
        [
            _record(bib_number=1, rider_slug="rider-a", final_gc_position=1),
            _record(bib_number=2, rider_slug="rider-b", final_gc_position=2),
            _record(bib_number=3, rider_slug="rider-c", final_gc_position=3),
        ],
    )

    assert summary.riders_created == 3
    assert summary.teams_created == 1
    assert len(fixture.teams.rows) == 1


def test_team_is_looked_up_once_per_team_not_per_rider() -> None:
    """An edition has eight riders per team; repeating the query would be waste."""
    fixture = _Fixture()
    records = [
        _record(bib_number=i, rider_slug=f"rider-{i}", final_gc_position=i) for i in range(1, 9)
    ]

    fixture.use_case.execute(_edition(), records)

    assert fixture.teams.slug_lookups == 1


def test_rider_in_two_editions_yields_one_rider_and_two_participations() -> None:
    """The point of separating identity from participation."""
    fixture = _Fixture()

    fixture.use_case.execute(_edition(2023), [_record(final_gc_position=1)])
    fixture.use_case.execute(_edition(2024), [_record(final_gc_position=2)])

    assert len(fixture.riders.rows) == 1
    rider = next(iter(fixture.riders.rows.values()))
    history = fixture.participations.list_by_rider(rider.id)
    assert len(history) == 2
    assert {p.final_gc_position for p in history} == {1, 2}


def test_second_edition_reuses_the_stored_rider() -> None:
    fixture = _Fixture()

    first = fixture.use_case.execute(_edition(2023), [_record()])
    second = fixture.use_case.execute(_edition(2024), [_record()])

    assert first.riders_created == 1
    assert second.riders_created == 0
    assert second.riders_reused == 1


def test_same_team_in_two_editions_gets_a_row_each() -> None:
    """Teams are scoped to an edition, so each appearance is its own row."""
    fixture = _Fixture()
    edition_2023 = _edition(2023)
    edition_2024 = _edition(2024)

    fixture.use_case.execute(edition_2023, [_record(team_name="Team Jumbo-Visma")])
    fixture.use_case.execute(edition_2024, [_record(team_name="Team Visma-Lease a Bike")])

    assert len(fixture.teams.rows) == 2
    in_2023 = fixture.teams.get_by_edition_and_slug(edition_2023.id, "Visma-Lease_a_Bike")
    in_2024 = fixture.teams.get_by_edition_and_slug(edition_2024.id, "Visma-Lease_a_Bike")
    assert in_2023 is not None
    assert in_2024 is not None
    assert in_2023.name == "Team Jumbo-Visma"
    assert in_2024.name == "Team Visma-Lease a Bike"


def test_rerunning_an_edition_creates_nothing_new() -> None:
    fixture = _Fixture()
    edition = _edition()
    records = [_record(bib_number=i, rider_slug=f"rider-{i}", final_gc_position=i) for i in (1, 2)]

    fixture.use_case.execute(edition, records)
    summary = fixture.use_case.execute(edition, records)

    assert summary.riders_created == 0
    assert summary.teams_created == 0
    assert len(fixture.riders.rows) == 2
    assert len(fixture.teams.rows) == 1
    assert len(fixture.participations.list_by_edition(edition.id)) == 2


def test_rerunning_keeps_participation_identity() -> None:
    fixture = _Fixture()
    edition = _edition()

    fixture.use_case.execute(edition, [_record()])
    first = fixture.participations.list_by_edition(edition.id)[0]
    fixture.use_case.execute(edition, [_record()])
    second = fixture.participations.list_by_edition(edition.id)[0]

    assert second.id == first.id


def test_corrected_details_are_applied_on_reingest() -> None:
    """A re-run should pick up an article that has since been fixed."""
    fixture = _Fixture()
    edition = _edition()
    fixture.use_case.execute(edition, [_record(final_gc_position=5)])

    fixture.use_case.execute(edition, [_record(final_gc_position=4, age=27)])

    stored = fixture.participations.list_by_edition(edition.id)[0]
    assert stored.final_gc_position == 4
    assert stored.age == 27


def test_abandonment_is_carried_through() -> None:
    fixture = _Fixture()
    edition = _edition()

    fixture.use_case.execute(
        edition,
        [
            _record(
                final_gc_position=None,
                abandonment=Abandonment(AbandonmentKind.DID_NOT_FINISH, StageNumber(14)),
            )
        ],
    )

    stored = fixture.participations.list_by_edition(edition.id)[0]
    assert stored.finished is False
    assert stored.abandonment is not None
    assert stored.abandonment.kind is AbandonmentKind.DID_NOT_FINISH
    assert stored.abandonment.stage_number == StageNumber(14)


def test_young_rider_flag_is_carried_through() -> None:
    fixture = _Fixture()
    edition = _edition()

    fixture.use_case.execute(edition, [_record(is_young_rider=True)])

    assert fixture.participations.list_by_edition(edition.id)[0].is_young_rider is True


def test_duplicate_rider_in_one_startlist_is_reported() -> None:
    """Either the source or the parser is wrong; keeping the last row would hide it."""
    fixture = _Fixture()

    with pytest.raises(DuplicateRiderError, match="appears more than once"):
        fixture.use_case.execute(
            _edition(),
            [
                _record(bib_number=1, final_gc_position=1),
                _record(bib_number=2, final_gc_position=2),
            ],
        )


def test_summary_totals_the_field() -> None:
    fixture = _Fixture()
    records = [
        _record(bib_number=i, rider_slug=f"rider-{i}", final_gc_position=i) for i in range(1, 5)
    ]

    summary = fixture.use_case.execute(_edition(), records)

    assert summary.edition_year == 2023
    assert summary.riders_total == 4
    assert summary.participations == 4


def test_empty_startlist_stores_nothing() -> None:
    fixture = _Fixture()

    summary = fixture.use_case.execute(_edition(), [])

    assert summary.participations == 0
    assert not fixture.riders.rows
    assert not fixture.teams.rows
