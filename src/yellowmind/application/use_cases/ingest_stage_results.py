"""Store stage results and GC standings for an edition."""

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import uuid4

from yellowmind.application.dto import GcStandingRecord, StageResultRecord
from yellowmind.application.identity import EditionRiderIndex
from yellowmind.domain.entities import GcStanding, RaceResult, ResultStatus, Rider, TourEdition
from yellowmind.domain.repositories import (
    GcStandingRepository,
    RaceResultRepository,
    RiderParticipationRepository,
    RiderRepository,
    StageRepository,
)


class MissingStageError(Exception):
    """Raised when a result references a stage that has not been ingested."""


@dataclass(frozen=True, slots=True)
class StageResultsIngestionSummary:
    """What one results ingestion run changed."""

    edition_year: int
    results_created: int
    results_updated: int
    standings_created: int
    standings_updated: int
    stages_without_results: tuple[int, ...]
    skipped_team_time_trials: tuple[int, ...]
    #: Source slugs that could not be matched to a startlist rider.
    unresolved_riders: tuple[str, ...]


class IngestStageResults:
    """Persist top-10 stage finishes and GC standings for an edition.

    Requires the edition's stages and startlist to already exist. Rider identity
    is resolved within the edition's participants so accent and naming drift
    between Wikipedia articles can be absorbed without a global alias table.
    """

    def __init__(
        self,
        stages: StageRepository,
        riders: RiderRepository,
        participations: RiderParticipationRepository,
        results: RaceResultRepository,
        standings: GcStandingRepository,
    ) -> None:
        self._stages = stages
        self._riders = riders
        self._participations = participations
        self._results = results
        self._standings = standings

    def execute(
        self,
        edition: TourEdition,
        result_records: Sequence[StageResultRecord],
        standing_records: Sequence[GcStandingRecord],
        *,
        skipped_team_time_trials: Sequence[int] = (),
    ) -> StageResultsIngestionSummary:
        """Store results and standings against ``edition``.

        Rows whose rider cannot be resolved are skipped and listed in the
        summary rather than failing the whole edition: a single redirect gap
        should not block 200 other placements.

        Raises:
            MissingStageError: If a record's stage number is not stored.
        """
        stages_by_number = {
            stage.number.value: stage for stage in self._stages.list_by_edition(edition.id)
        }
        index = self._edition_rider_index(edition)
        unresolved: set[str] = set()
        results_created = results_updated = 0
        standings_created = standings_updated = 0

        for record in result_records:
            stage = stages_by_number.get(record.stage_number)
            if stage is None:
                msg = f"Stage {record.stage_number} of {edition.year} has not been ingested"
                raise MissingStageError(msg)
            rider = index.resolve(record.rider_slug, record.rider_name)
            if rider is None:
                unresolved.add(record.rider_slug)
                continue

            stored = self._results.get_by_stage_and_rider(stage.id, rider.id)
            self._results.save(
                RaceResult(
                    id=stored.id if stored is not None else uuid4(),
                    stage_id=stage.id,
                    rider_id=rider.id,
                    rank=record.rank,
                    time=record.time,
                    time_gap_seconds=record.time_gap_seconds,
                    status=ResultStatus.FINISHED,
                )
            )
            if stored is None:
                results_created += 1
            else:
                results_updated += 1

        for record in standing_records:
            stage = stages_by_number.get(record.stage_number)
            if stage is None:
                msg = f"Stage {record.stage_number} of {edition.year} has not been ingested"
                raise MissingStageError(msg)
            rider = index.resolve(record.rider_slug, record.rider_name)
            if rider is None:
                unresolved.add(record.rider_slug)
                continue

            stored = self._standings.get_by_stage_and_rider(stage.id, rider.id)
            self._standings.save(
                GcStanding(
                    id=stored.id if stored is not None else uuid4(),
                    stage_id=stage.id,
                    rider_id=rider.id,
                    rank=record.rank,
                    time=record.time,
                    time_gap_seconds=record.time_gap_seconds,
                )
            )
            if stored is None:
                standings_created += 1
            else:
                standings_updated += 1

        stages_with_results = {r.stage_number for r in result_records}
        without_results = tuple(
            sorted(
                n
                for n in stages_by_number
                if n not in stages_with_results and n not in skipped_team_time_trials
            )
        )

        return StageResultsIngestionSummary(
            edition_year=edition.year,
            results_created=results_created,
            results_updated=results_updated,
            standings_created=standings_created,
            standings_updated=standings_updated,
            stages_without_results=without_results,
            skipped_team_time_trials=tuple(skipped_team_time_trials),
            unresolved_riders=tuple(sorted(unresolved)),
        )

    def _edition_rider_index(self, edition: TourEdition) -> EditionRiderIndex:
        riders: list[Rider] = []
        for participation in self._participations.list_by_edition(edition.id):
            rider = self._riders.get_by_id(participation.rider_id)
            if rider is not None:
                riders.append(rider)
        return EditionRiderIndex(riders)
