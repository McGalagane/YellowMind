"""Map between ORM models and domain entities."""

from __future__ import annotations

from yellowmind.domain.entities import (
    GcStanding,
    RaceResult,
    ResultStatus,
    Rider,
    RiderParticipation,
    Stage,
    StageType,
    Team,
    TourEdition,
)
from yellowmind.domain.value_objects import (
    Abandonment,
    AbandonmentKind,
    Distance,
    StageNumber,
)
from yellowmind.infrastructure.persistence.models import (
    GcStandingModel,
    RaceResultModel,
    RiderModel,
    RiderParticipationModel,
    StageModel,
    TeamModel,
    TourEditionModel,
)


def tour_edition_to_domain(model: TourEditionModel) -> TourEdition:
    """Convert a Tour edition ORM model to a domain entity."""
    return TourEdition(
        id=model.id,
        year=model.year,
        name=model.name,
        start_date=model.start_date,
        end_date=model.end_date,
    )


def tour_edition_to_model(edition: TourEdition) -> TourEditionModel:
    """Convert a Tour edition domain entity to an ORM model."""
    return TourEditionModel(
        id=edition.id,
        year=edition.year,
        name=edition.name,
        start_date=edition.start_date,
        end_date=edition.end_date,
    )


def rider_to_domain(model: RiderModel) -> Rider:
    """Convert a rider ORM model to a domain entity."""
    return Rider(
        id=model.id,
        name=model.name,
        nationality=model.nationality,
        source_slug=model.source_slug,
        birth_date=model.birth_date,
    )


def rider_to_model(rider: Rider) -> RiderModel:
    """Convert a rider domain entity to an ORM model."""
    return RiderModel(
        id=rider.id,
        name=rider.name,
        nationality=rider.nationality,
        source_slug=rider.source_slug,
        birth_date=rider.birth_date,
    )


def team_to_domain(model: TeamModel) -> Team:
    """Convert a team ORM model to a domain entity."""
    return Team(
        id=model.id,
        tour_edition_id=model.tour_edition_id,
        name=model.name,
        source_slug=model.source_slug,
        nationality=model.nationality,
    )


def team_to_model(team: Team) -> TeamModel:
    """Convert a team domain entity to an ORM model."""
    return TeamModel(
        id=team.id,
        tour_edition_id=team.tour_edition_id,
        name=team.name,
        source_slug=team.source_slug,
        nationality=team.nationality,
    )


def participation_to_domain(model: RiderParticipationModel) -> RiderParticipation:
    """Convert a participation ORM model to a domain entity."""
    return RiderParticipation(
        id=model.id,
        tour_edition_id=model.tour_edition_id,
        rider_id=model.rider_id,
        team_id=model.team_id,
        bib_number=model.bib_number,
        age=model.age,
        final_gc_position=model.final_gc_position,
        abandonment=_abandonment_to_domain(model.abandonment_kind, model.abandonment_stage),
        is_young_rider=model.is_young_rider,
    )


def participation_to_model(participation: RiderParticipation) -> RiderParticipationModel:
    """Convert a participation domain entity to an ORM model."""
    abandonment = participation.abandonment
    stage = abandonment.stage_number if abandonment is not None else None
    return RiderParticipationModel(
        id=participation.id,
        tour_edition_id=participation.tour_edition_id,
        rider_id=participation.rider_id,
        team_id=participation.team_id,
        bib_number=participation.bib_number,
        age=participation.age,
        final_gc_position=participation.final_gc_position,
        abandonment_kind=abandonment.kind.value if abandonment is not None else None,
        abandonment_stage=stage.value if stage is not None else None,
        is_young_rider=participation.is_young_rider,
    )


def _abandonment_to_domain(kind: str | None, stage: int | None) -> Abandonment | None:
    """Rebuild an abandonment from its two stored columns."""
    if kind is None:
        return None
    return Abandonment(
        kind=AbandonmentKind(kind),
        stage_number=StageNumber(stage) if stage is not None else None,
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


def gc_standing_to_domain(model: GcStandingModel) -> GcStanding:
    """Convert a GC standing ORM model to a domain entity."""
    return GcStanding(
        id=model.id,
        stage_id=model.stage_id,
        rider_id=model.rider_id,
        rank=model.rank,
        time=model.time,
        time_gap_seconds=model.time_gap_seconds,
    )


def gc_standing_to_model(standing: GcStanding) -> GcStandingModel:
    """Convert a GC standing domain entity to an ORM model."""
    return GcStandingModel(
        id=standing.id,
        stage_id=standing.stage_id,
        rider_id=standing.rider_id,
        rank=standing.rank,
        time=standing.time,
        time_gap_seconds=standing.time_gap_seconds,
    )
