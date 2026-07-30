"""Daily weather observation ready to store against a stage."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WeatherRecord:
    """Weather at a stage finish on the stage date.

    Coordinates and ``location_name`` are kept so a later reader can see which
    place was used — finishes are geocoded, not stage midpoints.
    """

    stage_number: int
    location_name: str
    latitude: float
    longitude: float
    temperature_c: float
    wind_speed_kmh: float
    precipitation_mm: float
