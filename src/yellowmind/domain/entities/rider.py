"""Rider entity."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(slots=True)
class Rider:
    """A cyclist participating in a Tour edition."""

    id: UUID
    team_id: UUID
    name: str
    birth_date: date
    nationality: str
    pcs_slug: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            msg = "Rider name cannot be empty"
            raise ValueError(msg)
        if not self.pcs_slug.strip():
            msg = "PCS slug cannot be empty"
            raise ValueError(msg)
