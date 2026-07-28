"""Prediction entity."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from yellowmind.domain.value_objects import Probability


@dataclass(slots=True)
class Prediction:
    """Model prediction output for a stage or edition target."""

    id: UUID
    tour_edition_id: UUID
    stage_id: UUID | None
    target: str
    probabilities: dict[UUID, Probability]
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.target.strip():
            msg = "Prediction target cannot be empty"
            raise ValueError(msg)
        if not self.probabilities:
            msg = "Probabilities cannot be empty"
            raise ValueError(msg)

        total = sum(probability.value for probability in self.probabilities.values())
        if abs(total - 1.0) > 1e-6:
            msg = f"Probabilities must sum to 1.0, got {total}"
            raise ValueError(msg)
