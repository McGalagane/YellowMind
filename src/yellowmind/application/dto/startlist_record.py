"""One rider's startlist row, as gathered from a data source."""

from dataclasses import dataclass

from yellowmind.domain.value_objects import Abandonment


@dataclass(frozen=True, slots=True)
class StartlistRecord:
    """A rider's entry into one edition, before identities are resolved.

    Carries the source's own identifiers rather than internal UUIDs, because
    assigning those is the ingesting use case's job.
    """

    bib_number: int
    rider_name: str
    #: Stable source identifier for the rider, used to recognise the same person
    #: across editions.
    rider_slug: str
    #: Country as named by the source, e.g. ``Isle of Man``.
    nationality: str
    #: Team name as printed for this edition.
    team_name: str
    #: Stable source identifier for the team. Points at the team's current name,
    #: so it may differ from `team_name` after a sponsor change.
    team_slug: str
    age: int | None
    final_gc_position: int | None
    abandonment: Abandonment | None
    is_young_rider: bool

    def __post_init__(self) -> None:
        if self.bib_number < 1:
            msg = f"Bib number must be positive, got {self.bib_number}"
            raise ValueError(msg)
        if not self.rider_name.strip():
            msg = "Rider name cannot be empty"
            raise ValueError(msg)
        # Both slugs are the keys identity resolution turns on, so an absent one
        # would silently merge or duplicate riders.
        if not self.rider_slug.strip():
            msg = f"Rider {self.rider_name} has no source slug"
            raise ValueError(msg)
        if not self.team_slug.strip():
            msg = f"Team {self.team_name} has no source slug"
            raise ValueError(msg)
        if self.final_gc_position is not None and self.final_gc_position < 1:
            msg = f"GC position must be positive, got {self.final_gc_position}"
            raise ValueError(msg)
        if self.final_gc_position is not None and self.abandonment is not None:
            msg = f"Rider {self.rider_name} cannot both place and abandon"
            raise ValueError(msg)
