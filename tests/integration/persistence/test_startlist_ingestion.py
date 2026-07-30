"""End-to-end test from startlist HTML through to reloaded riders and teams."""

from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from yellowmind.application.use_cases import IngestStartlist, IngestTourEdition
from yellowmind.domain.entities import TourEdition
from yellowmind.domain.value_objects import AbandonmentKind
from yellowmind.infrastructure.ingestion.wikipedia.parsing import parse_edition, parse_startlist
from yellowmind.infrastructure.ingestion.wikipedia.records import startlist_entries_to_records
from yellowmind.infrastructure.persistence.base import Base
from yellowmind.infrastructure.persistence.models import RiderModel, RiderParticipationModel
from yellowmind.infrastructure.persistence.repositories import (
    SqlAlchemyRiderParticipationRepository,
    SqlAlchemyRiderRepository,
    SqlAlchemyTeamRepository,
    SqlAlchemyTourEditionRepository,
)

_FIXTURES = Path(__file__).parents[2] / "fixtures" / "wikipedia"


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


def _ingest_edition(session: Session) -> TourEdition:
    html = (_FIXTURES / "edition_overview_sample.html").read_text()
    edition = IngestTourEdition(SqlAlchemyTourEditionRepository(session)).execute(
        parse_edition(html)
    )
    session.flush()
    return edition


def _ingest_startlist(session: Session, edition: TourEdition) -> int:
    html = (_FIXTURES / "startlist_sample.html").read_text()
    records = startlist_entries_to_records(parse_startlist(html))
    use_case = IngestStartlist(
        SqlAlchemyRiderRepository(session),
        SqlAlchemyTeamRepository(session),
        SqlAlchemyRiderParticipationRepository(session),
    )
    summary = use_case.execute(edition, records)
    session.commit()
    return summary.participations


def _count(session: Session, model: type[RiderModel] | type[RiderParticipationModel]) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def test_startlist_html_becomes_stored_participations(db_session: Session) -> None:
    edition = _ingest_edition(db_session)

    stored = _ingest_startlist(db_session, edition)

    participations = SqlAlchemyRiderParticipationRepository(db_session).list_by_edition(edition.id)
    assert stored == len(participations)
    assert participations, "fixture should yield at least one rider"
    # Bib order is the repository's contract, and the fixture is not in bib order.
    assert [p.bib_number for p in participations] == sorted(p.bib_number for p in participations)


def test_every_rider_is_linked_to_a_team_in_the_edition(db_session: Session) -> None:
    edition = _ingest_edition(db_session)
    _ingest_startlist(db_session, edition)

    teams = SqlAlchemyTeamRepository(db_session).list_by_edition(edition.id)
    team_ids = {team.id for team in teams}
    participations = SqlAlchemyRiderParticipationRepository(db_session).list_by_edition(edition.id)

    assert teams
    assert all(p.team_id in team_ids for p in participations)


def test_abandonments_survive_the_round_trip(db_session: Session) -> None:
    """The fixture covers DNF, DNS, DSQ, HD, OTL and COV."""
    edition = _ingest_edition(db_session)
    _ingest_startlist(db_session, edition)

    participations = SqlAlchemyRiderParticipationRepository(db_session).list_by_edition(edition.id)
    abandoned = [p for p in participations if p.abandonment is not None]

    assert abandoned, "fixture should include riders who left the race"
    assert all(p.final_gc_position is None for p in abandoned)
    assert all(isinstance(p.abandonment.kind, AbandonmentKind) for p in abandoned if p.abandonment)


def test_finishers_and_abandonments_account_for_the_whole_field(db_session: Session) -> None:
    edition = _ingest_edition(db_session)
    _ingest_startlist(db_session, edition)

    participations = SqlAlchemyRiderParticipationRepository(db_session).list_by_edition(edition.id)
    finishers = [p for p in participations if p.finished]
    abandoned = [p for p in participations if p.abandonment is not None]

    assert len(finishers) + len(abandoned) == len(participations)


def test_reingesting_the_same_startlist_is_idempotent(db_session: Session) -> None:
    edition = _ingest_edition(db_session)
    _ingest_startlist(db_session, edition)
    riders_after_first = _count(db_session, RiderModel)
    participations_after_first = _count(db_session, RiderParticipationModel)

    _ingest_startlist(db_session, edition)

    assert _count(db_session, RiderModel) == riders_after_first
    assert _count(db_session, RiderParticipationModel) == participations_after_first


def test_riders_are_reused_across_editions(db_session: Session) -> None:
    """One rider row, one participation per edition."""
    edition_2023 = _ingest_edition(db_session)
    _ingest_startlist(db_session, edition_2023)
    riders_after_first = _count(db_session, RiderModel)

    edition_2024 = TourEdition(
        id=uuid4(),
        year=2024,
        name="Tour de France 2024",
        start_date=edition_2023.start_date.replace(year=2024),
        end_date=edition_2023.end_date.replace(year=2024),
    )
    SqlAlchemyTourEditionRepository(db_session).save(edition_2024)
    db_session.flush()
    _ingest_startlist(db_session, edition_2024)

    assert _count(db_session, RiderModel) == riders_after_first
    assert _count(db_session, RiderParticipationModel) == riders_after_first * 2
