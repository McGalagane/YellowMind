"""Team strategy entity."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class TeamStrategy:
    """Team tactical approach for a Tour edition."""

    id: UUID
    team_id: UUID
    gc_leader_id: UUID | None
    approach: str

    def __post_init__(self) -> None:
        if not self.approach.strip():
            msg = "Team approach cannot be empty"
            raise ValueError(msg)
