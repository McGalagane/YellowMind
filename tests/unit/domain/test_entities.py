"""Tests for domain entities."""

from datetime import date, datetime
from uuid import uuid4

import pytest

from yellowmind.domain.entities import (
    Prediction,
    RaceResult,
    ResultStatus,
    Rider,
    RiderRating,
    Simulation,
    Stage,
    StageProfile,
    StageType,
    Team,
    TeamStrategy,
    TourEdition,
    Weather,
)
from yellowmind.domain.entities.stage_profile import FinishType
from yellowmind.domain.value_objects import Distance, Probability, StageNumber


def test_tour_edition_valid() -> None:
    edition = TourEdition(
        id=uuid4(),
        year=2024,
        name="Tour de France 2024",
        start_date=date(2024, 6, 29),
        end_date=date(2024, 7, 21),
    )
    assert edition.year == 2024


def test_tour_edition_invalid_dates() -> None:
    with pytest.raises(ValueError, match="End date"):
        TourEdition(
            id=uuid4(),
            year=2024,
            name="Tour de France 2024",
            start_date=date(2024, 7, 21),
            end_date=date(2024, 6, 29),
        )


def test_team_requires_name() -> None:
    with pytest.raises(ValueError, match="Team name"):
        Team(id=uuid4(), tour_edition_id=uuid4(), name="  ", source_slug="groupama-fdj")


def test_team_requires_source_slug() -> None:
    with pytest.raises(ValueError, match="Team source slug"):
        Team(id=uuid4(), tour_edition_id=uuid4(), name="Groupama-FDJ", source_slug=" ")


def test_rider_requires_name() -> None:
    with pytest.raises(ValueError, match="Rider name"):
        Rider(id=uuid4(), name="", nationality="Slovenia", source_slug="tadej-pogacar")


def test_rider_requires_source_slug() -> None:
    with pytest.raises(ValueError, match="Rider source slug"):
        Rider(id=uuid4(), name="Tadej Pogacar", nationality="Slovenia", source_slug="")


def test_rider_birth_date_is_optional() -> None:
    """The data source publishes age per edition, never a birth date."""
    rider = Rider(id=uuid4(), name="Tadej Pogacar", nationality="Slovenia", source_slug="pogacar")

    assert rider.birth_date is None


def test_rider_accepts_birth_date_when_known() -> None:
    rider = Rider(
        id=uuid4(),
        name="Tadej Pogacar",
        nationality="Slovenia",
        source_slug="pogacar",
        birth_date=date(1998, 9, 21),
    )

    assert rider.birth_date == date(1998, 9, 21)


def test_stage_entity() -> None:
    stage = Stage(
        id=uuid4(),
        tour_edition_id=uuid4(),
        number=StageNumber(1),
        date=date(2024, 6, 29),
        stage_type=StageType.FLAT,
        distance=Distance(185.0),
    )
    assert stage.number.value == 1


def test_stage_profile_score_bounds() -> None:
    with pytest.raises(ValueError, match="Profile score"):
        StageProfile(
            id=uuid4(),
            stage_id=uuid4(),
            elevation_gain_m=1000,
            finish_type=FinishType.UPHILL,
            profile_score=6,
        )


def test_race_result_finished_requires_rank() -> None:
    with pytest.raises(ValueError, match="rank"):
        RaceResult(
            id=uuid4(),
            stage_id=uuid4(),
            rider_id=uuid4(),
            rank=None,
            time="4:00:00",
            time_gap_seconds=0,
            status=ResultStatus.FINISHED,
        )


def test_weather_non_negative() -> None:
    with pytest.raises(ValueError, match="Wind speed"):
        Weather(
            id=uuid4(),
            stage_id=uuid4(),
            temperature_c=25.0,
            wind_speed_kmh=-1.0,
            precipitation_mm=0.0,
            location_name="Bilbao",
            latitude=43.26,
            longitude=-2.92,
        )


def test_rider_rating_non_negative() -> None:
    with pytest.raises(ValueError, match="climbing"):
        RiderRating(
            id=uuid4(),
            rider_id=uuid4(),
            stage_id=uuid4(),
            climbing=-1.0,
            sprint=1500.0,
            tt=1500.0,
            endurance=1500.0,
            recovery=1500.0,
            descending=1500.0,
            explosiveness=1500.0,
            form=1500.0,
        )


def test_prediction_probabilities_sum_to_one() -> None:
    rider_a = uuid4()
    rider_b = uuid4()
    with pytest.raises(ValueError, match="sum to 1.0"):
        Prediction(
            id=uuid4(),
            tour_edition_id=uuid4(),
            stage_id=uuid4(),
            target="stage_winner",
            probabilities={
                rider_a: Probability(0.6),
                rider_b: Probability(0.5),
            },
            created_at=datetime(2024, 7, 1, 12, 0, 0),
        )


def test_prediction_valid() -> None:
    rider_a = uuid4()
    rider_b = uuid4()
    prediction = Prediction(
        id=uuid4(),
        tour_edition_id=uuid4(),
        stage_id=uuid4(),
        target="stage_winner",
        probabilities={
            rider_a: Probability(0.6),
            rider_b: Probability(0.4),
        },
        created_at=datetime(2024, 7, 1, 12, 0, 0),
    )
    assert prediction.target == "stage_winner"


def test_simulation_requires_iterations() -> None:
    with pytest.raises(ValueError, match="n_iterations"):
        Simulation(
            id=uuid4(),
            tour_edition_id=uuid4(),
            n_iterations=0,
            outcomes={"gc_winner": {}},
            created_at=datetime(2024, 7, 1, 12, 0, 0),
        )


def test_team_strategy_requires_approach() -> None:
    with pytest.raises(ValueError, match="approach"):
        TeamStrategy(
            id=uuid4(),
            team_id=uuid4(),
            gc_leader_id=uuid4(),
            approach="",
        )
