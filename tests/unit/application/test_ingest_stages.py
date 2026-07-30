"""Unit tests for the stage ingestion use case."""

from datetime import date
from uuid import uuid4

import pytest
from tests.unit.application.doubles import InMemoryStageRepository

from yellowmind.application.dto import StageRecord
from yellowmind.application.use_cases import IngestStages, StageScheduleError
from yellowmind.domain.entities import StageType, TourEdition


def _edition(year: int = 2023) -> TourEdition:
    return TourEdition(
        id=uuid4(),
        year=year,
        name=f"Tour de France {year}",
        start_date=date(year, 7, 1),
        end_date=date(year, 7, 23),
    )


def _record(
    number: int = 1,
    *,
    day: int = 1,
    stage_type: StageType = StageType.FLAT,
    distance_km: float = 182.0,
) -> StageRecord:
    return StageRecord(
        number=number,
        date=date(2023, 7, day),
        stage_type=stage_type,
        distance_km=distance_km,
    )


def test_stores_a_route() -> None:
    repo = InMemoryStageRepository()
    edition = _edition()

    summary = IngestStages(repo).execute(
        edition, [_record(1, day=1), _record(2, day=2), _record(3, day=3)]
    )

    assert summary.stages_created == 3
    assert summary.stages_updated == 0
    assert summary.stages_total == 3
    assert [s.number.value for s in repo.list_by_edition(edition.id)] == [1, 2, 3]


def test_carries_terrain_and_distance_through() -> None:
    repo = InMemoryStageRepository()
    edition = _edition()

    IngestStages(repo).execute(
        edition, [_record(1, stage_type=StageType.MOUNTAIN_TT, distance_km=22.5)]
    )

    stored = repo.list_by_edition(edition.id)[0]
    assert stored.stage_type is StageType.MOUNTAIN_TT
    assert stored.distance.kilometres == 22.5


def test_rerunning_updates_rather_than_duplicating() -> None:
    repo = InMemoryStageRepository()
    edition = _edition()
    use_case = IngestStages(repo)
    records = [_record(1, day=1), _record(2, day=2)]

    use_case.execute(edition, records)
    summary = use_case.execute(edition, records)

    assert summary.stages_created == 0
    assert summary.stages_updated == 2
    assert len(repo.list_by_edition(edition.id)) == 2


def test_rerunning_keeps_stage_identity() -> None:
    """Results reference a stage, so its UUID must survive a re-ingest."""
    repo = InMemoryStageRepository()
    edition = _edition()
    use_case = IngestStages(repo)

    use_case.execute(edition, [_record(1)])
    first = repo.list_by_edition(edition.id)[0]
    use_case.execute(edition, [_record(1)])
    second = repo.list_by_edition(edition.id)[0]

    assert second.id == first.id


def test_corrected_route_is_applied_on_reingest() -> None:
    repo = InMemoryStageRepository()
    edition = _edition()
    use_case = IngestStages(repo)
    use_case.execute(edition, [_record(1, distance_km=182.0)])

    use_case.execute(edition, [_record(1, distance_km=180.5, stage_type=StageType.HILLY)])

    stored = repo.list_by_edition(edition.id)[0]
    assert stored.distance.kilometres == 180.5
    assert stored.stage_type is StageType.HILLY


def test_rejects_a_repeated_stage_number() -> None:
    """Two rows for one slot means the route table was misread."""
    repo = InMemoryStageRepository()

    with pytest.raises(StageScheduleError, match="appears twice"):
        IngestStages(repo).execute(_edition(), [_record(1, day=1), _record(1, day=2)])


def test_rejects_a_stage_before_the_edition_starts() -> None:
    repo = InMemoryStageRepository()
    edition = _edition(2023)
    early = StageRecord(
        number=1, date=date(2023, 6, 30), stage_type=StageType.FLAT, distance_km=182.0
    )

    with pytest.raises(StageScheduleError, match="falls outside"):
        IngestStages(repo).execute(edition, [early])


def test_rejects_a_stage_after_the_edition_ends() -> None:
    repo = InMemoryStageRepository()
    edition = _edition(2023)
    late = StageRecord(
        number=21, date=date(2023, 7, 24), stage_type=StageType.FLAT, distance_km=115.0
    )

    with pytest.raises(StageScheduleError, match="falls outside"):
        IngestStages(repo).execute(edition, [late])


def test_accepts_stages_on_the_boundary_dates() -> None:
    """The opening and closing stages fall on the edition's own dates."""
    repo = InMemoryStageRepository()
    edition = _edition(2023)
    first = StageRecord(
        number=1, date=date(2023, 7, 1), stage_type=StageType.FLAT, distance_km=182.0
    )
    last = StageRecord(
        number=21, date=date(2023, 7, 23), stage_type=StageType.FLAT, distance_km=115.0
    )

    summary = IngestStages(repo).execute(edition, [first, last])

    assert summary.stages_created == 2


def test_stages_of_two_editions_stay_separate() -> None:
    repo = InMemoryStageRepository()
    use_case = IngestStages(repo)
    edition_2023 = _edition(2023)
    edition_2024 = TourEdition(
        id=uuid4(),
        year=2024,
        name="Tour de France 2024",
        start_date=date(2024, 6, 29),
        end_date=date(2024, 7, 21),
    )

    use_case.execute(edition_2023, [_record(1, day=1)])
    use_case.execute(
        edition_2024,
        [
            StageRecord(
                number=1,
                date=date(2024, 6, 29),
                stage_type=StageType.HILLY,
                distance_km=206.0,
            )
        ],
    )

    assert len(repo.list_by_edition(edition_2023.id)) == 1
    assert len(repo.list_by_edition(edition_2024.id)) == 1


def test_empty_route_stores_nothing() -> None:
    repo = InMemoryStageRepository()
    edition = _edition()

    summary = IngestStages(repo).execute(edition, [])

    assert summary.stages_total == 0
    assert not repo.list_by_edition(edition.id)
