"""One stage's details, as gathered from a data source."""

from dataclasses import dataclass
from datetime import date

from yellowmind.domain.entities import StageType


@dataclass(frozen=True, slots=True)
class StageRecord:
    """A stage's schedule and terrain, before an edition identity is attached."""

    number: int
    date: date
    stage_type: StageType
    distance_km: float

    def __post_init__(self) -> None:
        if not 1 <= self.number <= 21:
            msg = f"Stage number must be between 1 and 21, got {self.number}"
            raise ValueError(msg)
        if self.distance_km <= 0:
            msg = f"Stage distance must be positive, got {self.distance_km}"
            raise ValueError(msg)
