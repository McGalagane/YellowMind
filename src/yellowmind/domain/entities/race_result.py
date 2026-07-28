"""Race result entity."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class ResultStatus(StrEnum):
    """Rider status at stage finish."""

    FINISHED = "finished"
    DNF = "dnf"
    DNS = "dns"
    DSQ = "dsq"


@dataclass(slots=True)
class RaceResult:
    """A rider's result on a specific stage."""

    id: UUID
    stage_id: UUID
    rider_id: UUID
    rank: int | None
    time: str | None
    time_gap_seconds: int | None
    status: ResultStatus

    def __post_init__(self) -> None:
        if self.status == ResultStatus.FINISHED and self.rank is None:
            msg = "Finished results must have a rank"
            raise ValueError(msg)
        if self.rank is not None and self.rank < 1:
            msg = f"Rank must be positive, got {self.rank}"
            raise ValueError(msg)
