"""End-to-end test from course finishes through to stored weather."""

from collections.abc import Generator
from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from yellowmind.application.dto import WeatherRecord
from yellowmind.application.use_cases import IngestWeather
from yellowmind.domain.entities import Stage, StageType, TourEdition
from yellowmind.domain.value_objects import Distance, StageNumber
from yellowmind.infrastructure.persistence.base import Base
from yellowmind.infrastructure.persistence.repositories import (
    SqlAlchemyStageRepository,
    SqlAlchemyTourEditionRepository,
    SqlAlchemyWeatherRepository,
)


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
    session.flush()
    return edition


def test_weather_records_are_stored(db_session: Session) -> None:
    edition = _seed(db_session)
    records = [
        WeatherRecord(
            stage_number=1,
            location_name="Bilbao",
            latitude=43.26,
            longitude=-2.92,
            temperature_c=24.0,
            wind_speed_kmh=14.0,
            precipitation_mm=0.0,
        ),
        WeatherRecord(
            stage_number=2,
            location_name="San Sebastián",
            latitude=43.32,
            longitude=-1.98,
            temperature_c=22.0,
            wind_speed_kmh=18.0,
            precipitation_mm=2.5,
        ),
    ]

    summary = IngestWeather(
        SqlAlchemyStageRepository(db_session),
        SqlAlchemyWeatherRepository(db_session),
    ).execute(edition, records)
    db_session.commit()

    stage_one = SqlAlchemyStageRepository(db_session).get_by_edition_and_number(edition.id, 1)
    assert stage_one is not None
    stored = SqlAlchemyWeatherRepository(db_session).get_by_stage(stage_one.id)
    assert stored is not None
    assert stored.location_name == "Bilbao"
    assert stored.temperature_c == 24.0
    assert summary.weather_created == 2


def test_reingesting_weather_is_idempotent(db_session: Session) -> None:
    edition = _seed(db_session)
    record = WeatherRecord(
        stage_number=1,
        location_name="Bilbao",
        latitude=43.26,
        longitude=-2.92,
        temperature_c=24.0,
        wind_speed_kmh=14.0,
        precipitation_mm=0.0,
    )
    use_case = IngestWeather(
        SqlAlchemyStageRepository(db_session),
        SqlAlchemyWeatherRepository(db_session),
    )

    use_case.execute(edition, [record])
    db_session.commit()
    summary = use_case.execute(edition, [record])
    db_session.commit()

    assert summary.weather_created == 0
    assert summary.weather_updated == 1
