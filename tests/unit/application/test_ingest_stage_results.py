"""Unit tests for stage results ingestion."""

from datetime import date
from uuid import uuid4

import pytest
from tests.unit.application.doubles import (
    InMemoryGcStandingRepository,
    InMemoryRaceResultRepository,
    InMemoryRiderParticipationRepository,
    InMemoryRiderRepository,
    InMemoryStageRepository,
)

from yellowmind.application.dto import GcStandingRecord, StageResultRecord
from yellowmind.application.use_cases import IngestStageResults, MissingStageError
from yellowmind.domain.entities import (
    ResultStatus,
    Rider,
    RiderParticipation,
    Stage,
    StageType,
    TourEdition,
)
from yellowmind.domain.value_objects import Distance, StageNumber


def _edition(year: int = 2023) -> TourEdition:
    return TourEdition(
        id=uuid4(),
        year=year,
        name=f"Tour de France {year}",
        start_date=date(year, 7, 1),
        end_date=date(year, 7, 23),
    )


def _stage(edition: TourEdition, number: int) -> Stage:
    return Stage(
        id=uuid4(),
        tour_edition_id=edition.id,
        number=StageNumber(number),
        date=date(edition.year, 7, number),
        stage_type=StageType.FLAT,
        distance=Distance(180.0),
    )


def _result(stage: int, rank: int, slug: str, gap: int = 0) -> StageResultRecord:
    return StageResultRecord(
        stage_number=stage,
        rank=rank,
        rider_name=slug.replace("_", " "),
        rider_slug=slug,
        time='+ 0"' if gap else "4h 00' 00\"",
        time_gap_seconds=gap,
    )


def _standing(stage: int, rank: int, slug: str, gap: int = 0) -> GcStandingRecord:
    return GcStandingRecord(
        stage_number=stage,
        rank=rank,
        rider_name=slug.replace("_", " "),
        rider_slug=slug,
        time='+ 0"' if gap else "4h 00' 00\"",
        time_gap_seconds=gap,
    )


class _Fixture:
    def __init__(self) -> None:
        self.stages = InMemoryStageRepository()
        self.riders = InMemoryRiderRepository()
        self.participations = InMemoryRiderParticipationRepository()
        self.results = InMemoryRaceResultRepository()
        self.standings = InMemoryGcStandingRepository()
        self.use_case = IngestStageResults(
            self.stages,
            self.riders,
            self.participations,
            self.results,
            self.standings,
        )
        self.edition = _edition()
        self._team_id = uuid4()

    def seed_stage(self, number: int) -> Stage:
        stage = _stage(self.edition, number)
        self.stages.save(stage)
        return stage

    def seed_rider(self, slug: str, name: str | None = None) -> Rider:
        rider = Rider(
            id=uuid4(),
            name=name or slug.replace("_", " "),
            nationality="Unknown",
            source_slug=slug,
        )
        self.riders.save(rider)
        self.participations.save(
            RiderParticipation(
                id=uuid4(),
                tour_edition_id=self.edition.id,
                rider_id=rider.id,
                team_id=self._team_id,
                bib_number=len(self.participations.rows) + 1,
            )
        )
        return rider


def test_stores_results_and_standings() -> None:
    fixture = _Fixture()
    stage = fixture.seed_stage(1)
    rider = fixture.seed_rider("Adam_Yates")

    summary = fixture.use_case.execute(
        fixture.edition,
        [_result(1, 1, "Adam_Yates")],
        [_standing(1, 1, "Adam_Yates")],
    )

    assert summary.results_created == 1
    assert summary.standings_created == 1
    stored = fixture.results.list_by_stage(stage.id)[0]
    assert stored.rider_id == rider.id
    assert stored.status is ResultStatus.FINISHED


def test_resolves_accent_drift_against_startlist() -> None:
    fixture = _Fixture()
    stage = fixture.seed_stage(1)
    rider = fixture.seed_rider("Niccolò_Bonifazio", "Niccolò Bonifazio")

    fixture.use_case.execute(
        fixture.edition,
        [_result(1, 5, "Niccolo_Bonifazio")],
        [],
    )

    assert fixture.results.list_by_stage(stage.id)[0].rider_id == rider.id


def test_resolves_tom_pidcock_to_thomas_on_startlist() -> None:
    fixture = _Fixture()
    stage = fixture.seed_stage(1)
    rider = fixture.seed_rider("Thomas_Pidcock", "Thomas Pidcock")

    fixture.use_case.execute(
        fixture.edition,
        [_result(1, 1, "Tom_Pidcock")],
        [],
    )

    assert fixture.results.list_by_stage(stage.id)[0].rider_id == rider.id


def test_skips_unresolved_riders_without_failing() -> None:
    fixture = _Fixture()
    fixture.seed_stage(1)
    fixture.seed_rider("Adam_Yates")

    summary = fixture.use_case.execute(
        fixture.edition,
        [_result(1, 1, "Adam_Yates"), _result(1, 2, "Unknown_Rider")],
        [],
    )

    assert summary.results_created == 1
    assert summary.unresolved_riders == ("Unknown_Rider",)


def test_rerunning_is_idempotent() -> None:
    fixture = _Fixture()
    fixture.seed_stage(1)
    fixture.seed_rider("Adam_Yates")
    records = [_result(1, 1, "Adam_Yates")]
    standings = [_standing(1, 1, "Adam_Yates")]

    fixture.use_case.execute(fixture.edition, records, standings)
    summary = fixture.use_case.execute(fixture.edition, records, standings)

    assert summary.results_created == 0
    assert summary.results_updated == 1
    assert summary.standings_updated == 1


def test_reports_stages_without_results() -> None:
    fixture = _Fixture()
    fixture.seed_stage(1)
    fixture.seed_stage(2)
    fixture.seed_stage(3)
    fixture.seed_rider("Adam_Yates")

    summary = fixture.use_case.execute(
        fixture.edition,
        [_result(1, 1, "Adam_Yates")],
        [_standing(1, 1, "Adam_Yates")],
        skipped_team_time_trials=(2,),
    )

    assert summary.stages_without_results == (3,)
    assert summary.skipped_team_time_trials == (2,)


def test_rejects_unknown_stage() -> None:
    fixture = _Fixture()
    fixture.seed_rider("Adam_Yates")

    with pytest.raises(MissingStageError, match="Stage 1"):
        fixture.use_case.execute(fixture.edition, [_result(1, 1, "Adam_Yates")], [])
