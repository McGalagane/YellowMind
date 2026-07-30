"""GC standing repository port."""

from abc import ABC, abstractmethod
from uuid import UUID

from yellowmind.domain.entities import GcStanding


class GcStandingRepository(ABC):
    """Persistence port for general-classification standings."""

    @abstractmethod
    def get_by_id(self, standing_id: UUID) -> GcStanding | None:
        """Return a standing by ID."""

    @abstractmethod
    def get_by_stage_and_rider(self, stage_id: UUID, rider_id: UUID) -> GcStanding | None:
        """Return one rider's standing after a stage, if stored."""

    @abstractmethod
    def list_by_stage(self, stage_id: UUID) -> list[GcStanding]:
        """Return standings after a stage, ordered by rank."""

    @abstractmethod
    def save(self, standing: GcStanding) -> None:
        """Persist a standing."""
