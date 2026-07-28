"""Stage repository port."""

from abc import ABC, abstractmethod
from uuid import UUID

from yellowmind.domain.entities import Stage


class StageRepository(ABC):
    """Persistence port for stages."""

    @abstractmethod
    def get_by_id(self, stage_id: UUID) -> Stage | None:
        """Return a stage by ID."""

    @abstractmethod
    def list_by_edition(self, tour_edition_id: UUID) -> list[Stage]:
        """Return all stages for a Tour edition."""

    @abstractmethod
    def save(self, stage: Stage) -> None:
        """Persist a stage."""
