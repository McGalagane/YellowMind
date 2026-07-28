"""Tour edition repository port."""

from abc import ABC, abstractmethod
from uuid import UUID

from yellowmind.domain.entities import TourEdition


class TourEditionRepository(ABC):
    """Persistence port for Tour editions."""

    @abstractmethod
    def get_by_id(self, edition_id: UUID) -> TourEdition | None:
        """Return a Tour edition by ID."""

    @abstractmethod
    def get_by_year(self, year: int) -> TourEdition | None:
        """Return a Tour edition by year."""

    @abstractmethod
    def save(self, edition: TourEdition) -> None:
        """Persist a Tour edition."""
