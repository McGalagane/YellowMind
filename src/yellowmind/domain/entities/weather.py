"""Weather entity."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class Weather:
    """Weather conditions for a stage."""

    id: UUID
    stage_id: UUID
    temperature_c: float
    wind_speed_kmh: float
    precipitation_mm: float

    def __post_init__(self) -> None:
        if self.wind_speed_kmh < 0:
            msg = "Wind speed cannot be negative"
            raise ValueError(msg)
        if self.precipitation_mm < 0:
            msg = "Precipitation cannot be negative"
            raise ValueError(msg)
