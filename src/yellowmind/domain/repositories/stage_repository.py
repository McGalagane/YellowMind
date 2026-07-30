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
    def get_by_edition_and_number(self, tour_edition_id: UUID, number: int) -> Stage | None:
        """Return one stage of an edition, if stored.

        Ingestion uses this to update an existing stage rather than insert a
        second one for the same slot.
        """

    @abstractmethod
    def list_by_edition(self, tour_edition_id: UUID) -> list[Stage]:
        """Return all stages for a Tour edition, ordered by number."""

    @abstractmethod
    def save(self, stage: Stage) -> None:
        """Persist a stage."""
