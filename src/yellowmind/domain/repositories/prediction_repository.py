"""Prediction repository port."""

from abc import ABC, abstractmethod
from uuid import UUID

from yellowmind.domain.entities import Prediction


class PredictionRepository(ABC):
    """Persistence port for predictions."""

    @abstractmethod
    def get_by_id(self, prediction_id: UUID) -> Prediction | None:
        """Return a prediction by ID."""

    @abstractmethod
    def list_by_edition(self, tour_edition_id: UUID) -> list[Prediction]:
        """Return all predictions for a Tour edition."""

    @abstractmethod
    def save(self, prediction: Prediction) -> None:
        """Persist a prediction."""
