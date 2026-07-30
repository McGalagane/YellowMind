"""Rider entity."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(slots=True)
class Rider:
    """A cyclist, independent of any single Tour edition.

    A rider's team, bib number, and result belong to a specific edition and are
    held by `RiderParticipation`. Keeping them off this entity is what lets the
    same rider be tracked across years, which form and history features need.
    """

    id: UUID
    name: str
    #: Country as named by the source, e.g. ``Denmark`` or ``Isle of Man``.
    nationality: str
    #: Stable identifier from the data source, used to recognise the same rider
    #: across editions even when the displayed name varies.
    source_slug: str
    #: Not published by the current source, which gives only age per edition.
    birth_date: date | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            msg = "Rider name cannot be empty"
            raise ValueError(msg)
        if not self.source_slug.strip():
            msg = "Rider source slug cannot be empty"
            raise ValueError(msg)
