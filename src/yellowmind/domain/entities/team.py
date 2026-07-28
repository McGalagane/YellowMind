"""Team entity."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class Team:
    """A team participating in a Tour edition."""

    id: UUID
    tour_edition_id: UUID
    name: str
    nationality: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            msg = "Team name cannot be empty"
            raise ValueError(msg)
