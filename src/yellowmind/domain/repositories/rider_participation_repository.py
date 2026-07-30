"""Rider participation repository port."""

from abc import ABC, abstractmethod
from uuid import UUID

from yellowmind.domain.entities import RiderParticipation


class RiderParticipationRepository(ABC):
    """Persistence port for rider participations."""

    @abstractmethod
    def get_by_id(self, participation_id: UUID) -> RiderParticipation | None:
        """Return a participation by ID."""

    @abstractmethod
    def get_by_edition_and_rider(
        self, tour_edition_id: UUID, rider_id: UUID
    ) -> RiderParticipation | None:
        """Return a rider's participation in one edition, if stored."""

    @abstractmethod
    def list_by_edition(self, tour_edition_id: UUID) -> list[RiderParticipation]:
        """Return every participation in an edition, ordered by bib number."""

    @abstractmethod
    def list_by_rider(self, rider_id: UUID) -> list[RiderParticipation]:
        """Return every edition a rider took part in.

        This is the query that rider form and history features are built on.
        """

    @abstractmethod
    def save(self, participation: RiderParticipation) -> None:
        """Persist a participation."""
