"""End-to-end test from article HTML through to a reloaded Tour edition."""

from collections.abc import Generator
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from yellowmind.application.use_cases import IngestTourEdition
from yellowmind.infrastructure.ingestion.wikipedia.parsing import parse_edition
from yellowmind.infrastructure.persistence.base import Base
from yellowmind.infrastructure.persistence.models import TourEditionModel
from yellowmind.infrastructure.persistence.repositories import SqlAlchemyTourEditionRepository

_FIXTURE = Path(__file__).parents[2] / "fixtures" / "wikipedia" / "edition_overview_sample.html"


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


def _edition_count(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(TourEditionModel)) or 0


def test_article_html_becomes_a_stored_edition(db_session: Session) -> None:
    repo = SqlAlchemyTourEditionRepository(db_session)

    ingested = IngestTourEdition(repo).execute(parse_edition(_FIXTURE.read_text()))
    db_session.commit()

    reloaded = repo.get_by_year(2023)

    assert reloaded is not None
    assert reloaded.id == ingested.id
    assert reloaded.name == "Tour de France 2023"
    assert reloaded.start_date == date(2023, 7, 1)
    assert reloaded.end_date == date(2023, 7, 23)


def test_reingesting_the_same_article_is_idempotent(db_session: Session) -> None:
    """A backfill is expected to be re-runnable without duplicating rows."""
    repo = SqlAlchemyTourEditionRepository(db_session)
    use_case = IngestTourEdition(repo)
    html = _FIXTURE.read_text()

    first = use_case.execute(parse_edition(html))
    db_session.commit()
    second = use_case.execute(parse_edition(html))
    db_session.commit()

    assert second.id == first.id
    assert _edition_count(db_session) == 1


def test_edition_is_found_by_id_as_well_as_year(db_session: Session) -> None:
    repo = SqlAlchemyTourEditionRepository(db_session)
    ingested = IngestTourEdition(repo).execute(parse_edition(_FIXTURE.read_text()))
    db_session.commit()

    assert repo.get_by_id(ingested.id) is not None


def test_unknown_year_returns_nothing(db_session: Session) -> None:
    assert SqlAlchemyTourEditionRepository(db_session).get_by_year(1998) is None
