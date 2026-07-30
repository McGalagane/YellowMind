"""Store daily weather observations for an edition's stages."""

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import uuid4

from yellowmind.application.dto import WeatherRecord
from yellowmind.application.use_cases.ingest_stage_results import MissingStageError
from yellowmind.domain.entities import TourEdition, Weather
from yellowmind.domain.repositories import StageRepository, WeatherRepository


@dataclass(frozen=True, slots=True)
class WeatherIngestionSummary:
    """What one weather ingestion run changed."""

    edition_year: int
    weather_created: int
    weather_updated: int
    #: Stage numbers present in the edition but absent from the weather records.
    stages_without_weather: tuple[int, ...]


class IngestWeather:
    """Persist finish-location weather for an edition's stages.

    Requires stages to already exist. Re-running updates the row keyed by
    ``stage_id`` so a backfill can refresh coordinates or values safely.
    """

    def __init__(self, stages: StageRepository, weather: WeatherRepository) -> None:
        self._stages = stages
        self._weather = weather

    def execute(
        self, edition: TourEdition, records: Sequence[WeatherRecord]
    ) -> WeatherIngestionSummary:
        """Store ``records`` against ``edition``.

        Raises:
            MissingStageError: If a record's stage number is not stored.
        """
        stages_by_number = {
            stage.number.value: stage for stage in self._stages.list_by_edition(edition.id)
        }
        created = updated = 0

        for record in records:
            stage = stages_by_number.get(record.stage_number)
            if stage is None:
                msg = f"Stage {record.stage_number} of {edition.year} has not been ingested"
                raise MissingStageError(msg)

            stored = self._weather.get_by_stage(stage.id)
            self._weather.save(
                Weather(
                    id=stored.id if stored is not None else uuid4(),
                    stage_id=stage.id,
                    temperature_c=record.temperature_c,
                    wind_speed_kmh=record.wind_speed_kmh,
                    precipitation_mm=record.precipitation_mm,
                    location_name=record.location_name,
                    latitude=record.latitude,
                    longitude=record.longitude,
                )
            )
            if stored is None:
                created += 1
            else:
                updated += 1

        covered = {record.stage_number for record in records}
        without = tuple(sorted(n for n in stages_by_number if n not in covered))

        return WeatherIngestionSummary(
            edition_year=edition.year,
            weather_created=created,
            weather_updated=updated,
            stages_without_weather=without,
        )
