"""Unit tests for weather ingestion."""

from datetime import date
from uuid import uuid4

import pytest
from tests.unit.application.doubles import InMemoryStageRepository, InMemoryWeatherRepository

from yellowmind.application.dto import WeatherRecord
from yellowmind.application.use_cases import IngestWeather, MissingStageError
from yellowmind.domain.entities import Stage, StageType, TourEdition
from yellowmind.domain.value_objects import Distance, StageNumber


def _edition(year: int = 2023) -> TourEdition:
    return TourEdition(
        id=uuid4(),
        year=year,
        name=f"Tour de France {year}",
        start_date=date(year, 7, 1),
        end_date=date(year, 7, 23),
    )


def _stage(edition: TourEdition, number: int) -> Stage:
    return Stage(
        id=uuid4(),
        tour_edition_id=edition.id,
        number=StageNumber(number),
        date=date(edition.year, 7, number),
        stage_type=StageType.FLAT,
        distance=Distance(180.0),
    )


def _weather(stage: int, temp: float = 22.0) -> WeatherRecord:
    return WeatherRecord(
        stage_number=stage,
        location_name="Bilbao",
        latitude=43.26,
        longitude=-2.92,
        temperature_c=temp,
        wind_speed_kmh=12.0,
        precipitation_mm=0.5,
    )


def test_creates_weather_for_each_stage() -> None:
    edition = _edition()
    stages = InMemoryStageRepository()
    weather = InMemoryWeatherRepository()
    stages.save(_stage(edition, 1))
    stages.save(_stage(edition, 2))

    summary = IngestWeather(stages, weather).execute(edition, [_weather(1), _weather(2)])

    assert summary.weather_created == 2
    assert summary.weather_updated == 0
    assert summary.stages_without_weather == ()
    stored = weather.get_by_stage(stages.get_by_edition_and_number(edition.id, 1).id)  # type: ignore[union-attr]
    assert stored is not None
    assert stored.location_name == "Bilbao"
    assert stored.temperature_c == 22.0


def test_reingest_updates_existing_row() -> None:
    edition = _edition()
    stages = InMemoryStageRepository()
    weather = InMemoryWeatherRepository()
    stages.save(_stage(edition, 1))
    use_case = IngestWeather(stages, weather)

    use_case.execute(edition, [_weather(1, temp=20.0)])
    summary = use_case.execute(edition, [_weather(1, temp=28.0)])

    assert summary.weather_created == 0
    assert summary.weather_updated == 1
    assert len(weather.rows) == 1
    stored = next(iter(weather.rows.values()))
    assert stored.temperature_c == 28.0


def test_reports_stages_without_weather() -> None:
    edition = _edition()
    stages = InMemoryStageRepository()
    weather = InMemoryWeatherRepository()
    stages.save(_stage(edition, 1))
    stages.save(_stage(edition, 2))

    summary = IngestWeather(stages, weather).execute(edition, [_weather(1)])

    assert summary.stages_without_weather == (2,)


def test_missing_stage_raises() -> None:
    edition = _edition()
    stages = InMemoryStageRepository()
    weather = InMemoryWeatherRepository()

    with pytest.raises(MissingStageError, match="Stage 1"):
        IngestWeather(stages, weather).execute(edition, [_weather(1)])
