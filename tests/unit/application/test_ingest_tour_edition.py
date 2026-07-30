"""Unit tests for the Tour edition ingestion use case."""

from datetime import date

from tests.unit.application.doubles import InMemoryTourEditionRepository

from yellowmind.application.dto import EditionRecord
from yellowmind.application.use_cases import IngestTourEdition


def _record(year: int = 2023) -> EditionRecord:
    return EditionRecord(year=year, start_date=date(year, 7, 1), end_date=date(year, 7, 23))


def test_stores_a_new_edition() -> None:
    repo = InMemoryTourEditionRepository()

    edition = IngestTourEdition(repo).execute(_record())

    assert repo.saved == [edition]
    assert edition.year == 2023
    assert edition.name == "Tour de France 2023"
    assert edition.start_date == date(2023, 7, 1)


def test_rerunning_keeps_the_existing_identity() -> None:
    """Other tables hold this UUID, so a re-ingest must not change it."""
    repo = InMemoryTourEditionRepository()
    use_case = IngestTourEdition(repo)

    first = use_case.execute(_record())
    second = use_case.execute(_record())

    assert second.id == first.id


def test_rerunning_does_not_create_a_second_edition() -> None:
    repo = InMemoryTourEditionRepository()
    use_case = IngestTourEdition(repo)

    use_case.execute(_record())
    use_case.execute(_record())

    assert repo.get_by_year(2023) is not None
    assert len({edition.id for edition in repo.saved}) == 1


def test_corrected_dates_are_applied_on_reingest() -> None:
    """A backfill re-run should pick up an article that has since been fixed."""
    repo = InMemoryTourEditionRepository()
    use_case = IngestTourEdition(repo)
    use_case.execute(_record())

    updated = use_case.execute(
        EditionRecord(year=2023, start_date=date(2023, 7, 1), end_date=date(2023, 7, 24))
    )

    assert updated.end_date == date(2023, 7, 24)


def test_distinct_years_get_distinct_identities() -> None:
    repo = InMemoryTourEditionRepository()
    use_case = IngestTourEdition(repo)

    first = use_case.execute(_record(2023))
    second = use_case.execute(_record(2024))

    assert first.id != second.id
