"""Weather repository port."""

from abc import ABC, abstractmethod
from uuid import UUID

from yellowmind.domain.entities import Weather


class WeatherRepository(ABC):
    """Persistence port for stage weather."""

    @abstractmethod
    def get_by_id(self, weather_id: UUID) -> Weather | None:
        """Return weather by ID."""

    @abstractmethod
    def get_by_stage(self, stage_id: UUID) -> Weather | None:
        """Return the weather row for a stage, if stored."""

    @abstractmethod
    def save(self, weather: Weather) -> None:
        """Persist a weather observation."""
