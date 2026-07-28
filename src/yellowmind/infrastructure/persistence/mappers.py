"""Map between ORM models and domain entities."""

from __future__ import annotations

from yellowmind.domain.entities import RaceResult, ResultStatus, Rider, Stage, StageType
from yellowmind.domain.value_objects import Distance, StageNumber
from yellowmind.infrastructure.persistence.models import RaceResultModel, RiderModel, StageModel


def rider_to_domain(model: RiderModel) -> Rider:
    """Convert a rider ORM model to a domain entity."""
    return Rider(
        id=model.id,
        team_id=model.team_id,
        name=model.name,
        birth_date=model.birth_date,
        nationality=model.nationality,
        pcs_slug=model.pcs_slug,
    )


def rider_to_model(rider: Rider) -> RiderModel:
    """Convert a rider domain entity to an ORM model."""
    return RiderModel(
        id=rider.id,
        team_id=rider.team_id,
        name=rider.name,
        birth_date=rider.birth_date,
        nationality=rider.nationality,
        pcs_slug=rider.pcs_slug,
    )


def stage_to_domain(model: StageModel) -> Stage:
    """Convert a stage ORM model to a domain entity."""
    return Stage(
        id=model.id,
        tour_edition_id=model.tour_edition_id,
        number=StageNumber(model.number),
        date=model.date,
        stage_type=StageType(model.stage_type),
        distance=Distance(model.distance_km),
    )


def stage_to_model(stage: Stage) -> StageModel:
    """Convert a stage domain entity to an ORM model."""
    return StageModel(
        id=stage.id,
        tour_edition_id=stage.tour_edition_id,
        number=stage.number.value,
        date=stage.date,
        stage_type=stage.stage_type.value,
        distance_km=stage.distance.kilometres,
    )


def race_result_to_domain(model: RaceResultModel) -> RaceResult:
    """Convert a race result ORM model to a domain entity."""
    return RaceResult(
        id=model.id,
        stage_id=model.stage_id,
        rider_id=model.rider_id,
        rank=model.rank,
        time=model.time,
        time_gap_seconds=model.time_gap_seconds,
        status=ResultStatus(model.status),
    )


def race_result_to_model(result: RaceResult) -> RaceResultModel:
    """Convert a race result domain entity to an ORM model."""
    return RaceResultModel(
        id=result.id,
        stage_id=result.stage_id,
        rider_id=result.rider_id,
        rank=result.rank,
        time=result.time,
        time_gap_seconds=result.time_gap_seconds,
        status=result.status.value,
    )
