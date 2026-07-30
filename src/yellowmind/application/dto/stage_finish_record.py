"""Finish place extracted from an edition's route table."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StageFinishRecord:
    """Where a stage finished, as named on the overview Course column.

    ``finish_slug`` is the Wikipedia article slug when the finish was wikilinked;
    it may be empty when the article only wrote the name in plain text (as 2024
    stage 21 does for Nice). The slug is preferred for coordinate lookup because
    mountain tops often lack Open-Meteo geocoding coverage.
    """

    stage_number: int
    finish_name: str
    finish_slug: str
