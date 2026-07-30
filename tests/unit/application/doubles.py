"""In-memory repository doubles for use-case tests.

These behave like the SQLAlchemy repositories in the ways use cases depend on:
lookups by source identifier, and a save that replaces a row of the same ID.
"""

from uuid import UUID

from yellowmind.domain.entities import (
    GcStanding,
    RaceResult,
    Rider,
    RiderParticipation,
    Stage,
    Team,
    TourEdition,
)
from yellowmind.domain.repositories import (
    GcStandingRepository,
    RaceResultRepository,
    RiderParticipationRepository,
    RiderRepository,
    StageRepository,
    TeamRepository,
    TourEditionRepository,
)


class InMemoryTourEditionRepository(TourEditionRepository):
    """Tour editions held in memory, recording every save."""

    def __init__(self) -> None:
        self.saved: list[TourEdition] = []
        self._by_year: dict[int, TourEdition] = {}

    def get_by_id(self, edition_id: UUID) -> TourEdition | None:
        return next((e for e in self._by_year.values() if e.id == edition_id), None)

    def get_by_year(self, year: int) -> TourEdition | None:
        return self._by_year.get(year)

    def save(self, edition: TourEdition) -> None:
        self.saved.append(edition)
        self._by_year[edition.year] = edition


class InMemoryRiderRepository(RiderRepository):
    """Riders held in memory, keyed by ID."""

    def __init__(self) -> None:
        self.rows: dict[UUID, Rider] = {}

    def get_by_id(self, rider_id: UUID) -> Rider | None:
        return self.rows.get(rider_id)

    def get_by_source_slug(self, source_slug: str) -> Rider | None:
        return next((r for r in self.rows.values() if r.source_slug == source_slug), None)

    def save(self, rider: Rider) -> None:
        self.rows[rider.id] = rider


class InMemoryTeamRepository(TeamRepository):
    """Teams held in memory, counting slug lookups to assert on query cost."""

    def __init__(self) -> None:
        self.rows: dict[UUID, Team] = {}
        self.slug_lookups = 0

    def get_by_id(self, team_id: UUID) -> Team | None:
        return self.rows.get(team_id)

    def get_by_edition_and_slug(self, tour_edition_id: UUID, source_slug: str) -> Team | None:
        self.slug_lookups += 1
        return next(
            (
                t
                for t in self.rows.values()
                if t.tour_edition_id == tour_edition_id and t.source_slug == source_slug
            ),
            None,
        )

    def list_by_edition(self, tour_edition_id: UUID) -> list[Team]:
        return [t for t in self.rows.values() if t.tour_edition_id == tour_edition_id]

    def save(self, team: Team) -> None:
        self.rows[team.id] = team


class InMemoryRiderParticipationRepository(RiderParticipationRepository):
    """Participations held in memory, keyed by ID."""

    def __init__(self) -> None:
        self.rows: dict[UUID, RiderParticipation] = {}

    def get_by_id(self, participation_id: UUID) -> RiderParticipation | None:
        return self.rows.get(participation_id)

    def get_by_edition_and_rider(
        self, tour_edition_id: UUID, rider_id: UUID
    ) -> RiderParticipation | None:
        return next(
            (
                p
                for p in self.rows.values()
                if p.tour_edition_id == tour_edition_id and p.rider_id == rider_id
            ),
            None,
        )

    def list_by_edition(self, tour_edition_id: UUID) -> list[RiderParticipation]:
        rows = [p for p in self.rows.values() if p.tour_edition_id == tour_edition_id]
        return sorted(rows, key=lambda p: p.bib_number)

    def list_by_rider(self, rider_id: UUID) -> list[RiderParticipation]:
        return [p for p in self.rows.values() if p.rider_id == rider_id]

    def save(self, participation: RiderParticipation) -> None:
        self.rows[participation.id] = participation


class InMemoryStageRepository(StageRepository):
    """Stages held in memory, keyed by ID."""

    def __init__(self) -> None:
        self.rows: dict[UUID, Stage] = {}

    def get_by_id(self, stage_id: UUID) -> Stage | None:
        return self.rows.get(stage_id)

    def get_by_edition_and_number(self, tour_edition_id: UUID, number: int) -> Stage | None:
        return next(
            (
                s
                for s in self.rows.values()
                if s.tour_edition_id == tour_edition_id and s.number.value == number
            ),
            None,
        )

    def list_by_edition(self, tour_edition_id: UUID) -> list[Stage]:
        rows = [s for s in self.rows.values() if s.tour_edition_id == tour_edition_id]
        return sorted(rows, key=lambda s: s.number.value)

    def save(self, stage: Stage) -> None:
        self.rows[stage.id] = stage


class InMemoryRaceResultRepository(RaceResultRepository):
    """Race results held in memory."""

    def __init__(self) -> None:
        self.rows: dict[UUID, RaceResult] = {}

    def get_by_id(self, result_id: UUID) -> RaceResult | None:
        return self.rows.get(result_id)

    def get_by_stage_and_rider(self, stage_id: UUID, rider_id: UUID) -> RaceResult | None:
        return next(
            (r for r in self.rows.values() if r.stage_id == stage_id and r.rider_id == rider_id),
            None,
        )

    def list_by_stage(self, stage_id: UUID) -> list[RaceResult]:
        rows = [r for r in self.rows.values() if r.stage_id == stage_id]
        return sorted(rows, key=lambda r: r.rank or 0)

    def save(self, result: RaceResult) -> None:
        self.rows[result.id] = result


class InMemoryGcStandingRepository(GcStandingRepository):
    """GC standings held in memory."""

    def __init__(self) -> None:
        self.rows: dict[UUID, GcStanding] = {}

    def get_by_id(self, standing_id: UUID) -> GcStanding | None:
        return self.rows.get(standing_id)

    def get_by_stage_and_rider(self, stage_id: UUID, rider_id: UUID) -> GcStanding | None:
        return next(
            (s for s in self.rows.values() if s.stage_id == stage_id and s.rider_id == rider_id),
            None,
        )

    def list_by_stage(self, stage_id: UUID) -> list[GcStanding]:
        rows = [s for s in self.rows.values() if s.stage_id == stage_id]
        return sorted(rows, key=lambda s: s.rank)

    def save(self, standing: GcStanding) -> None:
        self.rows[standing.id] = standing
