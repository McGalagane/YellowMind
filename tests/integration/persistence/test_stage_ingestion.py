"""End-to-end test from route table HTML through to reloaded stages."""

from collections.abc import Generator
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from yellowmind.application.use_cases import IngestStages
from yellowmind.domain.entities import StageType, TourEdition
from yellowmind.infrastructure.ingestion.wikipedia.parsing import parse_stages
from yellowmind.infrastructure.persistence.base import Base
from yellowmind.infrastructure.persistence.models import StageModel
from yellowmind.infrastructure.persistence.repositories import (
    SqlAlchemyStageRepository,
    SqlAlchemyTourEditionRepository,
)

_FIXTURE = Path(__file__).parents[2] / "fixtures" / "wikipedia" / "route_stages_sample.html"


@pytest.fixture
def db_session() -> Generator[Session]:
    """Provide an in-memory SQLite session with full schema."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    try:
        yield session
    finally:
        session.close()


def _seed_edition(session: Session) -> TourEdition:
    """Store the 2020 edition, whose dates span the fixture's two months."""
    edition = TourEdition(
        id=uuid4(),
        year=2020,
        name="Tour de France 2020",
        start_date=date(2020, 8, 29),
        end_date=date(2020, 9, 20),
    )
    SqlAlchemyTourEditionRepository(session).save(edition)
    session.flush()
    return edition


def _ingest(session: Session, edition: TourEdition) -> int:
    records = parse_stages(_FIXTURE.read_text(), edition.year)
    summary = IngestStages(SqlAlchemyStageRepository(session)).execute(edition, records)
    session.commit()
    return summary.stages_total


def _stage_count(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(StageModel)) or 0


def test_route_html_becomes_stored_stages(db_session: Session) -> None:
    edition = _seed_edition(db_session)

    stored = _ingest(db_session, edition)

    stages = SqlAlchemyStageRepository(db_session).list_by_edition(edition.id)
    assert stored == len(stages)
    assert [s.number.value for s in stages] == list(range(1, 11))


def test_terrain_and_distance_survive_the_round_trip(db_session: Session) -> None:
    edition = _seed_edition(db_session)
    _ingest(db_session, edition)

    stages = SqlAlchemyStageRepository(db_session).list_by_edition(edition.id)
    by_number = {s.number.value: s for s in stages}

    assert by_number[4].stage_type is StageType.INDIVIDUAL_TT
    assert by_number[5].stage_type is StageType.TEAM_TT
    assert by_number[7].stage_type is StageType.MOUNTAIN_TT
    assert by_number[2].stage_type is StageType.HILLY
    assert by_number[1].distance.kilometres == 182.0


def test_dates_span_two_months(db_session: Session) -> None:
    edition = _seed_edition(db_session)
    _ingest(db_session, edition)

    stages = SqlAlchemyStageRepository(db_session).list_by_edition(edition.id)

    assert stages[0].date == date(2020, 8, 29)
    assert stages[3].date == date(2020, 9, 1)


def test_reingesting_the_same_route_is_idempotent(db_session: Session) -> None:
    edition = _seed_edition(db_session)
    _ingest(db_session, edition)
    after_first = _stage_count(db_session)

    _ingest(db_session, edition)

    assert _stage_count(db_session) == after_first


def test_stage_is_found_by_edition_and_number(db_session: Session) -> None:
    edition = _seed_edition(db_session)
    _ingest(db_session, edition)
    repo = SqlAlchemyStageRepository(db_session)

    assert repo.get_by_edition_and_number(edition.id, 7) is not None
    assert repo.get_by_edition_and_number(edition.id, 21) is None


def test_database_rejects_a_duplicate_stage_number(db_session: Session) -> None:
    """The constraint backs up the use case rather than trusting it."""
    edition = _seed_edition(db_session)
    _ingest(db_session, edition)

    db_session.add(
        StageModel(
            id=uuid4(),
            tour_edition_id=edition.id,
            number=1,
            date=date(2020, 8, 29),
            stage_type=StageType.FLAT.value,
            distance_km=182.0,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()
