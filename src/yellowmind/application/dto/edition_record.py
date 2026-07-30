"""Edition-level facts gathered from a data source."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class EditionRecord:
    """One Tour edition's identity and duration.

    Nothing here is specific to a provider, so adapters produce this directly
    and use cases stay free of parsing concerns.
    """

    year: int
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            msg = f"Edition {self.year} ends before it starts"
            raise ValueError(msg)
        if self.end_date.year != self.year:
            msg = f"Edition {self.year} ends in {self.end_date.year}"
            raise ValueError(msg)
