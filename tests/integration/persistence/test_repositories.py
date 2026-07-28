"""Integration tests for persistence layer."""

from collections.abc import Generator
from datetime import date
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from yellowmind.domain.entities import RaceResult, ResultStatus, Rider, Stage, StageType
from yellowmind.domain.value_objects import Distance, StageNumber
from yellowmind.infrastructure.persistence.base import Base
from yellowmind.infrastructure.persistence.models import TeamModel, TourEditionModel
from yellowmind.infrastructure.persistence.repositories import (
    SqlAlchemyRaceResultRepository,
    SqlAlchemyRiderRepository,
    SqlAlchemyStageRepository,
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


def _seed_edition_and_team(session: Session) -> tuple[UUID, UUID]:
    edition_id = uuid4()
    team_id = uuid4()
    session.add(
        TourEditionModel(
            id=edition_id,
            year=2024,
            name="Tour de France 2024",
            start_date=date(2024, 6, 29),
            end_date=date(2024, 7, 21),
        )
    )
    session.add(
        TeamModel(
            id=team_id,
            tour_edition_id=edition_id,
            name="UAE Team Emirates",
            nationality="UAE",
        )
    )
    session.flush()
    return edition_id, team_id


def test_rider_stage_and_result_round_trip(db_session: Session) -> None:
    edition_id, team_id = _seed_edition_and_team(db_session)

    rider_id = uuid4()
    stage_id = uuid4()
    result_id = uuid4()

    rider = Rider(
        id=rider_id,
        team_id=team_id,
        name="Tadej Pogacar",
        birth_date=date(1998, 9, 21),
        nationality="SLO",
        pcs_slug="tadej-pogacar",
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
    assert loaded_stage is not None
    assert loaded_stage.number.value == 1
    assert loaded_result is not None
    assert loaded_result.rank == 1

    stage_results = result_repo.list_by_stage(stage_id)
    assert len(stage_results) == 1
    assert stage_results[0].rider_id == rider_id
