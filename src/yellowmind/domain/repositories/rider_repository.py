"""Rider repository port."""

from abc import ABC, abstractmethod
from uuid import UUID

from yellowmind.domain.entities import Rider


class RiderRepository(ABC):
    """Persistence port for riders."""

    @abstractmethod
    def get_by_id(self, rider_id: UUID) -> Rider | None:
        """Return a rider by ID."""

    @abstractmethod
    def get_by_source_slug(self, source_slug: str) -> Rider | None:
        """Return a rider by source identifier.

        Ingestion uses this to recognise a rider already stored from an earlier
        edition instead of creating a duplicate.
        """

    @abstractmethod
    def save(self, rider: Rider) -> None:
        """Persist a rider."""
