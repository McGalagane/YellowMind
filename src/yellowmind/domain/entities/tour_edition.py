"""Tour edition aggregate root."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(slots=True)
class TourEdition:
    """A single edition of the Tour de France."""

    id: UUID
    year: int
    name: str
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if self.year < 1903:
            msg = f"Invalid Tour year: {self.year}"
            raise ValueError(msg)
        if self.end_date < self.start_date:
            msg = "End date must be on or after start date"
            raise ValueError(msg)
