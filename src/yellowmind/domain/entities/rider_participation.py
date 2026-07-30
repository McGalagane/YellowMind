"""Rider participation entity."""

from dataclasses import dataclass
from uuid import UUID

from yellowmind.domain.value_objects import Abandonment


@dataclass(slots=True)
class RiderParticipation:
    """One rider's involvement in one Tour edition.

    Holds everything that is true of a rider only for a given year: which team
    they rode for, the number they wore, and how their race ended. A rider
    either reaches Paris with a general classification position or leaves with
    an abandonment, never both.
    """

    id: UUID
    tour_edition_id: UUID
    rider_id: UUID
    team_id: UUID
    #: Racing number worn for this edition.
    bib_number: int
    #: Age during this edition. Edition-relative, so it is not a rider attribute.
    age: int | None = None
    final_gc_position: int | None = None
    abandonment: Abandonment | None = None
    #: Eligible for the young rider classification in this edition.
    is_young_rider: bool = False

    def __post_init__(self) -> None:
        if self.bib_number < 1:
            msg = f"Bib number must be positive, got {self.bib_number}"
            raise ValueError(msg)
        if self.age is not None and self.age <= 0:
            msg = f"Age must be positive, got {self.age}"
            raise ValueError(msg)
        if self.final_gc_position is not None and self.final_gc_position < 1:
            msg = f"GC position must be positive, got {self.final_gc_position}"
            raise ValueError(msg)
        if self.final_gc_position is not None and self.abandonment is not None:
            msg = "A rider cannot both place in the GC and abandon"
            raise ValueError(msg)

    @property
    def finished(self) -> bool:
        """Whether the rider completed the edition."""
        return self.final_gc_position is not None
