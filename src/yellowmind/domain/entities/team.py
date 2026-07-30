"""Team entity."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class Team:
    """A team as it competed in one Tour edition.

    Teams are recorded per edition because sponsors, and therefore names, change
    between years. `source_slug` is the thread linking those appearances.
    """

    id: UUID
    tour_edition_id: UUID
    #: Name used for this edition, e.g. ``Team Jumbo-Visma`` in 2023.
    name: str
    #: Stable identifier from the data source. Resolves to the team's current
    #: name, so it may differ from `name` after a sponsor change.
    source_slug: str
    #: Not published by the current source.
    nationality: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            msg = "Team name cannot be empty"
            raise ValueError(msg)
        if not self.source_slug.strip():
            msg = "Team source slug cannot be empty"
            raise ValueError(msg)
