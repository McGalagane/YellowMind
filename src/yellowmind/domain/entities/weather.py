"""Weather entity."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True)
class Weather:
    """Weather conditions at a stage finish."""

    id: UUID
    stage_id: UUID
    temperature_c: float
    wind_speed_kmh: float
    precipitation_mm: float
    location_name: str
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if self.wind_speed_kmh < 0:
            msg = "Wind speed cannot be negative"
            raise ValueError(msg)
        if self.precipitation_mm < 0:
            msg = "Precipitation cannot be negative"
            raise ValueError(msg)
        if not (-90.0 <= self.latitude <= 90.0):
            msg = f"Latitude must be between -90 and 90, got {self.latitude}"
            raise ValueError(msg)
        if not (-180.0 <= self.longitude <= 180.0):
            msg = f"Longitude must be between -180 and 180, got {self.longitude}"
            raise ValueError(msg)
        if not self.location_name.strip():
            msg = "Location name cannot be empty"
            raise ValueError(msg)
