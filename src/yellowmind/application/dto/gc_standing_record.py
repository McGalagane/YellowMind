"""One GC placing after a stage, as gathered from a data source."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GcStandingRecord:
    """A rider's general-classification place after a stage."""

    #: Stage after which this standing applies.
    stage_number: int
    rank: int
    rider_name: str
    rider_slug: str
    time: str
    #: Gap to the yellow jersey in seconds; 0 for the leader.
    time_gap_seconds: int

    def __post_init__(self) -> None:
        if not 1 <= self.stage_number <= 21:
            msg = f"Stage number must be between 1 and 21, got {self.stage_number}"
            raise ValueError(msg)
        if self.rank < 1:
            msg = f"Rank must be positive, got {self.rank}"
            raise ValueError(msg)
        if not self.rider_slug.strip():
            msg = f"Rider {self.rider_name} has no source slug"
            raise ValueError(msg)
        if self.time_gap_seconds < 0:
            msg = f"Time gap cannot be negative, got {self.time_gap_seconds}"
            raise ValueError(msg)
