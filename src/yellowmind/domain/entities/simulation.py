"""Simulation entity."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class Simulation:
    """Monte Carlo simulation results for a Tour edition."""

    id: UUID
    tour_edition_id: UUID
    n_iterations: int
    outcomes: dict[str, object]
    created_at: datetime

    def __post_init__(self) -> None:
        if self.n_iterations < 1:
            msg = f"n_iterations must be at least 1, got {self.n_iterations}"
            raise ValueError(msg)
        if not self.outcomes:
            msg = "Simulation outcomes cannot be empty"
            raise ValueError(msg)
