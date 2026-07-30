"""Store a Tour edition gathered from a data source."""

from uuid import uuid4

from yellowmind.application.dto import EditionRecord
from yellowmind.domain.entities import TourEdition
from yellowmind.domain.repositories import TourEditionRepository


class IngestTourEdition:
    """Create or refresh the edition that other records attach to.

    Editions are the aggregate root: teams, participations, and stages all
    reference one, so this runs before any of them.
    """

    def __init__(self, editions: TourEditionRepository) -> None:
        self._editions = editions

    def execute(self, record: EditionRecord) -> TourEdition:
        """Persist `record`, reusing the stored edition's identity if present.

        Re-running for a year already stored updates that row rather than
        inserting a second one, so a backfill can be repeated safely. The
        existing UUID is kept because rows in other tables point at it.
        """
        stored = self._editions.get_by_year(record.year)
        edition = TourEdition(
            id=stored.id if stored is not None else uuid4(),
            year=record.year,
            name=f"Tour de France {record.year}",
            start_date=record.start_date,
            end_date=record.end_date,
        )
        self._editions.save(edition)
        return edition
