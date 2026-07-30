"""Team repository port."""

from abc import ABC, abstractmethod
from uuid import UUID

from yellowmind.domain.entities import Team


class TeamRepository(ABC):
    """Persistence port for teams."""

    @abstractmethod
    def get_by_id(self, team_id: UUID) -> Team | None:
        """Return a team by ID."""

    @abstractmethod
    def get_by_edition_and_slug(self, tour_edition_id: UUID, source_slug: str) -> Team | None:
        """Return a team's appearance in one edition, if stored.

        Teams are recorded per edition, so the slug alone is not unique.
        """

    @abstractmethod
    def list_by_edition(self, tour_edition_id: UUID) -> list[Team]:
        """Return every team in an edition."""

    @abstractmethod
    def save(self, team: Team) -> None:
        """Persist a team."""
