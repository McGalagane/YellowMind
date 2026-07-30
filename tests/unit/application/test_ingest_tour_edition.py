"""Unit tests for the Tour edition ingestion use case."""

from datetime import date
from uuid import UUID

from yellowmind.application.dto import EditionRecord
from yellowmind.application.use_cases import IngestTourEdition
from yellowmind.domain.entities import TourEdition
from yellowmind.domain.repositories import TourEditionRepository


class InMemoryTourEditionRepository(TourEditionRepository):
    """Repository double recording every save, to assert on write behaviour."""

    def __init__(self) -> None:
        self.saved: list[TourEdition] = []
        self._by_year: dict[int, TourEdition] = {}

    def get_by_id(self, edition_id: UUID) -> TourEdition | None:
        return next((e for e in self._by_year.values() if e.id == edition_id), None)

    def get_by_year(self, year: int) -> TourEdition | None:
        return self._by_year.get(year)

    def save(self, edition: TourEdition) -> None:
        self.saved.append(edition)
        self._by_year[edition.year] = edition


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
