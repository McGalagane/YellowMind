"""Rider rating entity."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class RiderRating:
    """Multi-dimensional rider ability ratings at a point in time."""

    id: UUID
    rider_id: UUID
    stage_id: UUID
    climbing: float
    sprint: float
    tt: float
    endurance: float
    recovery: float
    descending: float
    explosiveness: float
    form: float

    def __post_init__(self) -> None:
        for field_name in (
            "climbing",
            "sprint",
            "tt",
            "endurance",
            "recovery",
            "descending",
            "explosiveness",
            "form",
        ):
            value = getattr(self, field_name)
            if value < 0:
                msg = f"{field_name} rating cannot be negative, got {value}"
                raise ValueError(msg)
