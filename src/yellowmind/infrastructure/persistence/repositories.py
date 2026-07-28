"""SQLAlchemy repository implementations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from yellowmind.domain.entities import RaceResult, Rider, Stage
from yellowmind.domain.repositories import RaceResultRepository, RiderRepository, StageRepository
from yellowmind.infrastructure.persistence.mappers import (
    race_result_to_domain,
    race_result_to_model,
    rider_to_domain,
    rider_to_model,
    stage_to_domain,
    stage_to_model,
)
from yellowmind.infrastructure.persistence.models import RaceResultModel, RiderModel, StageModel


class SqlAlchemyRiderRepository(RiderRepository):
    """PostgreSQL-backed rider repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, rider_id: UUID) -> Rider | None:
        model = self._session.get(RiderModel, rider_id)
        return rider_to_domain(model) if model else None

    def list_by_team(self, team_id: UUID) -> list[Rider]:
        models = self._session.scalars(
            select(RiderModel).where(RiderModel.team_id == team_id)
        ).all()
        return [rider_to_domain(model) for model in models]

    def save(self, rider: Rider) -> None:
        self._session.merge(rider_to_model(rider))


class SqlAlchemyStageRepository(StageRepository):
    """PostgreSQL-backed stage repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, stage_id: UUID) -> Stage | None:
        model = self._session.get(StageModel, stage_id)
        return stage_to_domain(model) if model else None

    def list_by_edition(self, tour_edition_id: UUID) -> list[Stage]:
        models = self._session.scalars(
            select(StageModel)
            .where(StageModel.tour_edition_id == tour_edition_id)
            .order_by(StageModel.number)
        ).all()
        return [stage_to_domain(model) for model in models]

    def save(self, stage: Stage) -> None:
        self._session.merge(stage_to_model(stage))


class SqlAlchemyRaceResultRepository(RaceResultRepository):
    """PostgreSQL-backed race result repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, result_id: UUID) -> RaceResult | None:
        model = self._session.get(RaceResultModel, result_id)
        return race_result_to_domain(model) if model else None

    def list_by_stage(self, stage_id: UUID) -> list[RaceResult]:
        models = self._session.scalars(
            select(RaceResultModel)
            .where(RaceResultModel.stage_id == stage_id)
            .order_by(RaceResultModel.rank)
        ).all()
        return [race_result_to_domain(model) for model in models]

    def save(self, result: RaceResult) -> None:
        self._session.merge(race_result_to_model(result))
