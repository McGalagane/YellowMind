"""Integration tests for persistence layer."""

from collections.abc import Generator
from datetime import date
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from yellowmind.domain.entities import (
    RaceResult,
    ResultStatus,
    Rider,
    RiderParticipation,
    Stage,
    StageType,
    Team,
)
from yellowmind.domain.value_objects import (
    Abandonment,
    AbandonmentKind,
    Distance,
    StageNumber,
)
from yellowmind.infrastructure.persistence.base import Base
from yellowmind.infrastructure.persistence.models import TourEditionModel
from yellowmind.infrastructure.persistence.repositories import (
    SqlAlchemyRaceResultRepository,
    SqlAlchemyRiderParticipationRepository,
    SqlAlchemyRiderRepository,
    SqlAlchemyStageRepository,
    SqlAlchemyTeamRepository,
)


@pytest.fixture
def db_session() -> Generator[Session]:
    """Provide an in-memory SQLite session with full schema."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    try:
        yield session
        session.commit()
    finally:
        session.close()


def _seed_edition(session: Session, year: int = 2024) -> UUID:
    edition_id = uuid4()
    session.add(
        TourEditionModel(
            id=edition_id,
            year=year,
            name=f"Tour de France {year}",
            start_date=date(year, 6, 29),
            end_date=date(year, 7, 21),
        )
    )
    session.flush()
    return edition_id


def _save_team(session: Session, edition_id: UUID, slug: str = "uae-team-emirates") -> UUID:
    team = Team(
        id=uuid4(),
        tour_edition_id=edition_id,
        name="UAE Team Emirates",
        source_slug=slug,
    )
    SqlAlchemyTeamRepository(session).save(team)
    session.flush()
    return team.id


def test_rider_stage_and_result_round_trip(db_session: Session) -> None:
    edition_id = _seed_edition(db_session)

    rider_id = uuid4()
    stage_id = uuid4()
    result_id = uuid4()

    rider = Rider(
        id=rider_id,
        name="Tadej Pogacar",
        nationality="Slovenia",
        source_slug="tadej-pogacar",
    )
    stage = Stage(
        id=stage_id,
        tour_edition_id=edition_id,
        number=StageNumber(1),
        date=date(2024, 6, 29),
        stage_type=StageType.FLAT,
        distance=Distance(185.0),
    )
    result = RaceResult(
        id=result_id,
        stage_id=stage_id,
        rider_id=rider_id,
        rank=1,
        time="4:00:00",
        time_gap_seconds=0,
        status=ResultStatus.FINISHED,
    )

    rider_repo = SqlAlchemyRiderRepository(db_session)
    stage_repo = SqlAlchemyStageRepository(db_session)
    result_repo = SqlAlchemyRaceResultRepository(db_session)

    rider_repo.save(rider)
    stage_repo.save(stage)
    result_repo.save(result)
    db_session.commit()

    loaded_rider = rider_repo.get_by_id(rider_id)
    loaded_stage = stage_repo.get_by_id(stage_id)
    loaded_result = result_repo.get_by_id(result_id)

    assert loaded_rider is not None
    assert loaded_rider.name == "Tadej Pogacar"
    assert loaded_rider.birth_date is None
    assert loaded_stage is not None
    assert loaded_stage.number.value == 1
    assert loaded_result is not None
    assert loaded_result.rank == 1

    stage_results = result_repo.list_by_stage(stage_id)
    assert len(stage_results) == 1
    assert stage_results[0].rider_id == rider_id


def test_rider_is_found_by_source_slug(db_session: Session) -> None:
    """Ingestion relies on this to avoid duplicating a known rider."""
    repo = SqlAlchemyRiderRepository(db_session)
    repo.save(
        Rider(id=uuid4(), name="Jonas Vingegaard", nationality="Denmark", source_slug="vingegaard")
    )
    db_session.commit()

    assert repo.get_by_source_slug("vingegaard") is not None
    assert repo.get_by_source_slug("unknown-rider") is None


def test_team_is_found_by_edition_and_slug(db_session: Session) -> None:
    """The same team recurs across editions, so the slug alone is ambiguous."""
    edition_2023 = _seed_edition(db_session, 2023)
    edition_2024 = _seed_edition(db_session, 2024)
    repo = SqlAlchemyTeamRepository(db_session)

    repo.save(
        Team(
            id=uuid4(),
            tour_edition_id=edition_2023,
            name="Team Jumbo-Visma",
            source_slug="visma-lease-a-bike",
        )
    )
    repo.save(
        Team(
            id=uuid4(),
            tour_edition_id=edition_2024,
            name="Team Visma-Lease a Bike",
            source_slug="visma-lease-a-bike",
        )
    )
    db_session.commit()

    in_2023 = repo.get_by_edition_and_slug(edition_2023, "visma-lease-a-bike")
    in_2024 = repo.get_by_edition_and_slug(edition_2024, "visma-lease-a-bike")

    assert in_2023 is not None
    assert in_2024 is not None
    assert in_2023.name == "Team Jumbo-Visma"
    assert in_2024.name == "Team Visma-Lease a Bike"


def test_participation_round_trip_preserves_abandonment(db_session: Session) -> None:
    edition_id = _seed_edition(db_session)
    team_id = _save_team(db_session, edition_id)

    rider = Rider(id=uuid4(), name="Mark Cavendish", nationality="Isle of Man", source_slug="cav")
    SqlAlchemyRiderRepository(db_session).save(rider)
    db_session.flush()

    repo = SqlAlchemyRiderParticipationRepository(db_session)
    participation = RiderParticipation(
        id=uuid4(),
        tour_edition_id=edition_id,
        rider_id=rider.id,
        team_id=team_id,
        bib_number=181,
        age=39,
        abandonment=Abandonment(AbandonmentKind.DID_NOT_FINISH, StageNumber(8)),
    )
    repo.save(participation)
    db_session.commit()

    loaded = repo.get_by_edition_and_rider(edition_id, rider.id)

    assert loaded is not None
    assert loaded.bib_number == 181
    assert loaded.age == 39
    assert loaded.finished is False
    assert loaded.abandonment is not None
    assert loaded.abandonment.kind is AbandonmentKind.DID_NOT_FINISH
    assert loaded.abandonment.stage_number == StageNumber(8)


def test_finisher_round_trip_has_no_abandonment(db_session: Session) -> None:
    edition_id = _seed_edition(db_session)
    team_id = _save_team(db_session, edition_id)

    rider = Rider(id=uuid4(), name="Tadej Pogacar", nationality="Slovenia", source_slug="pogacar")
    SqlAlchemyRiderRepository(db_session).save(rider)
    db_session.flush()

    repo = SqlAlchemyRiderParticipationRepository(db_session)
    repo.save(
        RiderParticipation(
            id=uuid4(),
            tour_edition_id=edition_id,
            rider_id=rider.id,
            team_id=team_id,
            bib_number=1,
            age=25,
            final_gc_position=1,
            is_young_rider=True,
        )
    )
    db_session.commit()

    loaded = repo.get_by_edition_and_rider(edition_id, rider.id)

    assert loaded is not None
    assert loaded.finished is True
    assert loaded.final_gc_position == 1
    assert loaded.is_young_rider is True
    assert loaded.abandonment is None


def test_rider_history_spans_editions(db_session: Session) -> None:
    """The identity split exists so one rider can be followed across years."""
    edition_2023 = _seed_edition(db_session, 2023)
    edition_2024 = _seed_edition(db_session, 2024)
    team_2023 = _save_team(db_session, edition_2023)
    team_2024 = _save_team(db_session, edition_2024)

    rider = Rider(id=uuid4(), name="Jonas Vingegaard", nationality="Denmark", source_slug="jonas")
    SqlAlchemyRiderRepository(db_session).save(rider)
    db_session.flush()

    repo = SqlAlchemyRiderParticipationRepository(db_session)
    for edition_id, team_id, position in (
        (edition_2023, team_2023, 1),
        (edition_2024, team_2024, 2),
    ):
        repo.save(
            RiderParticipation(
                id=uuid4(),
                tour_edition_id=edition_id,
                rider_id=rider.id,
                team_id=team_id,
                bib_number=1,
                final_gc_position=position,
            )
        )
    db_session.commit()

    history = repo.list_by_rider(rider.id)

    assert len(history) == 2
    assert {p.final_gc_position for p in history} == {1, 2}


def test_participations_are_listed_by_bib_number(db_session: Session) -> None:
    edition_id = _seed_edition(db_session)
    team_id = _save_team(db_session, edition_id)
    rider_repo = SqlAlchemyRiderRepository(db_session)
    repo = SqlAlchemyRiderParticipationRepository(db_session)

    for bib in (11, 3, 7):
        rider = Rider(
            id=uuid4(),
            name=f"Rider {bib}",
            nationality="France",
            source_slug=f"rider-{bib}",
        )
        rider_repo.save(rider)
        db_session.flush()
        repo.save(
            RiderParticipation(
                id=uuid4(),
                tour_edition_id=edition_id,
                rider_id=rider.id,
                team_id=team_id,
                bib_number=bib,
            )
        )
    db_session.commit()

    assert [p.bib_number for p in repo.list_by_edition(edition_id)] == [3, 7, 11]
