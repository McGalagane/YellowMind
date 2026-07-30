"""End-to-end test from stage-range HTML through to stored results."""

from collections.abc import Generator
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from yellowmind.application.use_cases import IngestStageResults
from yellowmind.domain.entities import (
    Rider,
    RiderParticipation,
    Stage,
    StageType,
    Team,
    TourEdition,
)
from yellowmind.domain.value_objects import Distance, StageNumber
from yellowmind.infrastructure.ingestion.wikipedia.parsing import parse_stage_boards
from yellowmind.infrastructure.persistence.base import Base
from yellowmind.infrastructure.persistence.repositories import (
    SqlAlchemyGcStandingRepository,
    SqlAlchemyRaceResultRepository,
    SqlAlchemyRiderParticipationRepository,
    SqlAlchemyRiderRepository,
    SqlAlchemyStageRepository,
    SqlAlchemyTeamRepository,
    SqlAlchemyTourEditionRepository,
)

_FIXTURE = Path(__file__).parents[2] / "fixtures" / "wikipedia" / "stage_results_sample.html"


@pytest.fixture
def db_session() -> Generator[Session]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    try:
        yield session
    finally:
        session.close()


def _seed(session: Session) -> TourEdition:
    edition = TourEdition(
        id=uuid4(),
        year=2023,
        name="Tour de France 2023",
        start_date=date(2023, 7, 1),
        end_date=date(2023, 7, 23),
    )
    SqlAlchemyTourEditionRepository(session).save(edition)
    team = Team(
        id=uuid4(),
        tour_edition_id=edition.id,
        name="UAE Team Emirates",
        source_slug="UAE_Team_Emirates",
    )
    SqlAlchemyTeamRepository(session).save(team)
    stages = SqlAlchemyStageRepository(session)
    for number in (1, 2):
        stages.save(
            Stage(
                id=uuid4(),
                tour_edition_id=edition.id,
                number=StageNumber(number),
                date=date(2023, 7, number),
                stage_type=StageType.FLAT,
                distance=Distance(180.0),
            )
        )
    riders = SqlAlchemyRiderRepository(session)
    participations = SqlAlchemyRiderParticipationRepository(session)
    for bib, (slug, name) in enumerate(
        (
            ("Adam_Yates", "Adam Yates"),
            ("Simon_Yates_(cyclist)", "Simon Yates"),
            ("Tadej_Pogačar", "Tadej Pogacar"),
            ("Mike_Teunissen", "Mike Teunissen"),
            ("Wout_van_Aert", "Wout van Aert"),
        ),
        start=1,
    ):
        rider = Rider(id=uuid4(), name=name, nationality="Unknown", source_slug=slug)
        riders.save(rider)
        participations.save(
            RiderParticipation(
                id=uuid4(),
                tour_edition_id=edition.id,
                rider_id=rider.id,
                team_id=team.id,
                bib_number=bib,
            )
        )
    session.flush()
    return edition


def _use_case(session: Session) -> IngestStageResults:
    return IngestStageResults(
        SqlAlchemyStageRepository(session),
        SqlAlchemyRiderRepository(session),
        SqlAlchemyRiderParticipationRepository(session),
        SqlAlchemyRaceResultRepository(session),
        SqlAlchemyGcStandingRepository(session),
    )


def test_fixture_html_becomes_stored_results_and_standings(db_session: Session) -> None:
    edition = _seed(db_session)
    boards = parse_stage_boards(_FIXTURE.read_text())
    results = [r for b in boards for r in b.results]
    standings = [g for b in boards for g in b.gc]
    skipped = tuple(b.stage_number for b in boards if b.results_skipped)

    summary = _use_case(db_session).execute(
        edition, results, standings, skipped_team_time_trials=skipped
    )
    db_session.commit()

    stage_one = SqlAlchemyStageRepository(db_session).get_by_edition_and_number(edition.id, 1)
    stage_two = SqlAlchemyStageRepository(db_session).get_by_edition_and_number(edition.id, 2)
    assert stage_one is not None and stage_two is not None

    stored_results = SqlAlchemyRaceResultRepository(db_session).list_by_stage(stage_one.id)
    assert [r.rank for r in stored_results] == [1, 2, 3]
    assert stored_results[2].time_gap_seconds == 4

    yellow = SqlAlchemyGcStandingRepository(db_session).list_by_stage(stage_one.id)
    assert yellow[0].rank == 1
    assert summary.skipped_team_time_trials == (2,)
    assert SqlAlchemyRaceResultRepository(db_session).list_by_stage(stage_two.id) == []
    assert len(SqlAlchemyGcStandingRepository(db_session).list_by_stage(stage_two.id)) == 2


def test_reingesting_results_is_idempotent(db_session: Session) -> None:
    edition = _seed(db_session)
    boards = parse_stage_boards(_FIXTURE.read_text())
    results = [r for b in boards for r in b.results]
    standings = [g for b in boards for g in b.gc]
    use_case = _use_case(db_session)

    use_case.execute(edition, results, standings)
    db_session.commit()
    summary = use_case.execute(edition, results, standings)
    db_session.commit()

    assert summary.results_created == 0
    assert summary.standings_created == 0
    assert summary.results_updated == len(results)
    assert summary.standings_updated == len(standings)
