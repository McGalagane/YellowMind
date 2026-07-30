"""Domain value objects with validation."""

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class StageNumber:
    """Tour stage number (1-21)."""

    value: int

    def __post_init__(self) -> None:
        if not 1 <= self.value <= 21:
            msg = f"Stage number must be between 1 and 21, got {self.value}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class Probability:
    """Probability value in the closed interval [0, 1]."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            msg = f"Probability must be between 0 and 1, got {self.value}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class Distance:
    """Stage distance in kilometres."""

    kilometres: float

    def __post_init__(self) -> None:
        if self.kilometres <= 0:
            msg = f"Distance must be positive, got {self.kilometres}"
            raise ValueError(msg)


class AbandonmentKind(StrEnum):
    """Why a rider failed to complete a Tour edition.

    ``UNKNOWN`` lets an unrecognised source marker be recorded rather than
    discarded, keeping the gap visible instead of silent.
    """

    DID_NOT_FINISH = "did_not_finish"
    DID_NOT_START = "did_not_start"
    OUTSIDE_TIME_LIMIT = "outside_time_limit"
    COVID_WITHDRAWAL = "covid_withdrawal"
    DISQUALIFIED = "disqualified"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Abandonment:
    """How and when a rider left a Tour edition."""

    kind: AbandonmentKind
    #: The stage abandoned during, or not started. Absent when the source does
    #: not say which stage the withdrawal relates to.
    stage_number: StageNumber | None = None
