"""Race result repository port."""

from abc import ABC, abstractmethod
from uuid import UUID

from yellowmind.domain.entities import RaceResult


class RaceResultRepository(ABC):
    """Persistence port for race results."""

    @abstractmethod
    def get_by_id(self, result_id: UUID) -> RaceResult | None:
        """Return a result by ID."""

    @abstractmethod
    def get_by_stage_and_rider(self, stage_id: UUID, rider_id: UUID) -> RaceResult | None:
        """Return one rider's result on a stage, if stored."""

    @abstractmethod
    def list_by_stage(self, stage_id: UUID) -> list[RaceResult]:
        """Return all results for a stage, ordered by rank."""

    @abstractmethod
    def save(self, result: RaceResult) -> None:
        """Persist a race result."""
