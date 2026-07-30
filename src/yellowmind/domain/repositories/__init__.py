"""Abstract repository interfaces (ports)."""

from yellowmind.domain.repositories.prediction_repository import PredictionRepository
from yellowmind.domain.repositories.race_result_repository import RaceResultRepository
from yellowmind.domain.repositories.rider_participation_repository import (
    RiderParticipationRepository,
)
from yellowmind.domain.repositories.rider_repository import RiderRepository
from yellowmind.domain.repositories.stage_repository import StageRepository
from yellowmind.domain.repositories.team_repository import TeamRepository
from yellowmind.domain.repositories.tour_edition_repository import TourEditionRepository

__all__ = [
    "PredictionRepository",
    "RaceResultRepository",
    "RiderParticipationRepository",
    "RiderRepository",
    "StageRepository",
    "TeamRepository",
    "TourEditionRepository",
]
