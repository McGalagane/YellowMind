"""Stage entity."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from uuid import UUID

from yellowmind.domain.value_objects import Distance, StageNumber


class StageType(StrEnum):
    """Classification of stage terrain."""

    FLAT = "flat"
    HILLY = "hilly"
    MOUNTAIN = "mountain"
    INDIVIDUAL_TT = "individual_tt"
    TEAM_TT = "team_tt"


@dataclass(slots=True)
class Stage:
    """A single stage within a Tour edition."""

    id: UUID
    tour_edition_id: UUID
    number: StageNumber
    date: date
    stage_type: StageType
    distance: Distance
