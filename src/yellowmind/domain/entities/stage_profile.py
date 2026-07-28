"""Stage profile entity."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class FinishType(StrEnum):
    """Stage finish terrain classification."""

    FLAT = "flat"
    UPHILL = "uphill"
    DOWNHILL = "downhill"


@dataclass(slots=True)
class StageProfile:
    """Topographic profile of a stage."""

    id: UUID
    stage_id: UUID
    elevation_gain_m: float
    finish_type: FinishType
    profile_score: int

    def __post_init__(self) -> None:
        if self.elevation_gain_m < 0:
            msg = "Elevation gain cannot be negative"
            raise ValueError(msg)
        if not 0 <= self.profile_score <= 5:
            msg = f"Profile score must be 0-5, got {self.profile_score}"
            raise ValueError(msg)
