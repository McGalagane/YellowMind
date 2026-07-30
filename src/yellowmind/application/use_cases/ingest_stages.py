"""Store an edition's stages."""

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import uuid4

from yellowmind.application.dto import StageRecord
from yellowmind.domain.entities import Stage, TourEdition
from yellowmind.domain.repositories import StageRepository
from yellowmind.domain.value_objects import Distance, StageNumber


class StageScheduleError(Exception):
    """Raised when a set of stage records is not a coherent schedule."""


@dataclass(frozen=True, slots=True)
class StageIngestionSummary:
    """What one ingestion run changed."""

    edition_year: int
    stages_created: int
    stages_updated: int

    @property
    def stages_total(self) -> int:
        """Stages stored, however they were resolved."""
        return self.stages_created + self.stages_updated


class IngestStages:
    """Persist an edition's route.

    Runs after the edition exists, since every stage references it.
    """

    def __init__(self, stages: StageRepository) -> None:
        self._stages = stages

    def execute(
        self, edition: TourEdition, records: Sequence[StageRecord]
    ) -> StageIngestionSummary:
        """Store `records` against `edition`.

        Re-running updates the stage already held for each number rather than
        inserting another, so a backfill can be repeated safely.

        Raises:
            StageScheduleError: If two records claim the same stage number, or a
                stage falls outside the edition's own dates. Either means the
                route table was misread, and storing it would corrupt the
                schedule every later prediction reads.
        """
        seen: set[int] = set()
        created = 0
        updated = 0

        for record in records:
            if record.number in seen:
                msg = f"Stage {record.number} appears twice in the {edition.year} route"
                raise StageScheduleError(msg)
            seen.add(record.number)

            if not edition.start_date <= record.date <= edition.end_date:
                msg = (
                    f"Stage {record.number} on {record.date} falls outside the "
                    f"{edition.year} Tour ({edition.start_date} to {edition.end_date})"
                )
                raise StageScheduleError(msg)

            stored = self._stages.get_by_edition_and_number(edition.id, record.number)
            self._stages.save(
                Stage(
                    id=stored.id if stored is not None else uuid4(),
                    tour_edition_id=edition.id,
                    number=StageNumber(record.number),
                    date=record.date,
                    stage_type=record.stage_type,
                    distance=Distance(record.distance_km),
                )
            )
            if stored is None:
                created += 1
            else:
                updated += 1

        return StageIngestionSummary(
            edition_year=edition.year, stages_created=created, stages_updated=updated
        )
