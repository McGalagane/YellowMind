"""General classification standing after a stage."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class GcStanding:
    """A rider's place in the general classification after a given stage.

    Distinct from `RaceResult`, which is a finish on one stage. A standing is
    cumulative: it answers who wore yellow after stage N, not who won stage N.
    """

    id: UUID
    #: Stage after which this standing applies.
    stage_id: UUID
    rider_id: UUID
    rank: int
    time: str | None
    time_gap_seconds: int | None

    def __post_init__(self) -> None:
        if self.rank < 1:
            msg = f"Rank must be positive, got {self.rank}"
            raise ValueError(msg)
        if self.time_gap_seconds is not None and self.time_gap_seconds < 0:
            msg = f"Time gap cannot be negative, got {self.time_gap_seconds}"
            raise ValueError(msg)
