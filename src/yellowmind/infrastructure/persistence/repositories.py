"""SQLAlchemy repository implementations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from yellowmind.domain.entities import RaceResult, Rider, RiderParticipation, Stage, Team
from yellowmind.domain.repositories import (
    RaceResultRepository,
    RiderParticipationRepository,
    RiderRepository,
    StageRepository,
    TeamRepository,
)
from yellowmind.infrastructure.persistence.mappers import (
    participation_to_domain,
    participation_to_model,
    race_result_to_domain,
    race_result_to_model,
    rider_to_domain,
    rider_to_model,
    stage_to_domain,
    stage_to_model,
    team_to_domain,
    team_to_model,
)
from yellowmind.infrastructure.persistence.models import (
    RaceResultModel,
    RiderModel,
    RiderParticipationModel,
    StageModel,
    TeamModel,
)


class SqlAlchemyRiderRepository(RiderRepository):
    """PostgreSQL-backed rider repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, rider_id: UUID) -> Rider | None:
        model = self._session.get(RiderModel, rider_id)
        return rider_to_domain(model) if model else None

    def get_by_source_slug(self, source_slug: str) -> Rider | None:
        model = self._session.scalars(
            select(RiderModel).where(RiderModel.source_slug == source_slug)
        ).one_or_none()
        return rider_to_domain(model) if model else None

    def save(self, rider: Rider) -> None:
        self._session.merge(rider_to_model(rider))


class SqlAlchemyTeamRepository(TeamRepository):
    """PostgreSQL-backed team repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, team_id: UUID) -> Team | None:
        model = self._session.get(TeamModel, team_id)
        return team_to_domain(model) if model else None

    def get_by_edition_and_slug(self, tour_edition_id: UUID, source_slug: str) -> Team | None:
        model = self._session.scalars(
            select(TeamModel).where(
                TeamModel.tour_edition_id == tour_edition_id,
                TeamModel.source_slug == source_slug,
            )
        ).one_or_none()
        return team_to_domain(model) if model else None

    def list_by_edition(self, tour_edition_id: UUID) -> list[Team]:
        models = self._session.scalars(
            select(TeamModel)
            .where(TeamModel.tour_edition_id == tour_edition_id)
            .order_by(TeamModel.name)
        ).all()
        return [team_to_domain(model) for model in models]

    def save(self, team: Team) -> None:
        self._session.merge(team_to_model(team))


class SqlAlchemyRiderParticipationRepository(RiderParticipationRepository):
    """PostgreSQL-backed rider participation repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, participation_id: UUID) -> RiderParticipation | None:
        model = self._session.get(RiderParticipationModel, participation_id)
        return participation_to_domain(model) if model else None

    def get_by_edition_and_rider(
        self, tour_edition_id: UUID, rider_id: UUID
    ) -> RiderParticipation | None:
        model = self._session.scalars(
            select(RiderParticipationModel).where(
                RiderParticipationModel.tour_edition_id == tour_edition_id,
                RiderParticipationModel.rider_id == rider_id,
            )
        ).one_or_none()
        return participation_to_domain(model) if model else None

    def list_by_edition(self, tour_edition_id: UUID) -> list[RiderParticipation]:
        models = self._session.scalars(
            select(RiderParticipationModel)
            .where(RiderParticipationModel.tour_edition_id == tour_edition_id)
            .order_by(RiderParticipationModel.bib_number)
        ).all()
        return [participation_to_domain(model) for model in models]

    def list_by_rider(self, rider_id: UUID) -> list[RiderParticipation]:
        models = self._session.scalars(
            select(RiderParticipationModel)
            .where(RiderParticipationModel.rider_id == rider_id)
            .order_by(RiderParticipationModel.tour_edition_id)
        ).all()
        return [participation_to_domain(model) for model in models]

    def save(self, participation: RiderParticipation) -> None:
        self._session.merge(participation_to_model(participation))


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
