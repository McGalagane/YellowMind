"""Store an edition's startlist as riders, teams and participations."""

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID, uuid4

from yellowmind.application.dto import StartlistRecord
from yellowmind.domain.entities import Rider, RiderParticipation, Team, TourEdition
from yellowmind.domain.repositories import (
    RiderParticipationRepository,
    RiderRepository,
    TeamRepository,
)


class DuplicateRiderError(Exception):
    """Raised when one startlist lists the same rider twice.

    Left as an error rather than resolved silently: a rider appearing twice in an
    edition means either the source is wrong or the parser is, and quietly
    keeping the last row would hide both.
    """


@dataclass(frozen=True, slots=True)
class StartlistIngestionSummary:
    """What one ingestion run changed, for backfill logs and validation."""

    edition_year: int
    riders_created: int
    riders_reused: int
    teams_created: int
    participations: int

    @property
    def riders_total(self) -> int:
        """Riders in the startlist, however they were resolved."""
        return self.riders_created + self.riders_reused


class IngestStartlist:
    """Resolve source identifiers to stored entities, then persist the field.

    Runs after the edition exists, since teams and participations reference it.
    """

    def __init__(
        self,
        riders: RiderRepository,
        teams: TeamRepository,
        participations: RiderParticipationRepository,
    ) -> None:
        self._riders = riders
        self._teams = teams
        self._participations = participations

    def execute(
        self, edition: TourEdition, records: Sequence[StartlistRecord]
    ) -> StartlistIngestionSummary:
        """Store `records` against `edition`.

        Re-running for the same edition updates the existing rows rather than
        inserting new ones, so a backfill can be repeated safely.

        Raises:
            DuplicateRiderError: If a rider appears twice in `records`.
        """
        # Teams recur roughly eight times per startlist, so they are resolved
        # once and reused rather than looked up for every rider.
        team_ids: dict[str, UUID] = {}
        teams_created = 0
        riders_created = 0
        riders_reused = 0
        seen_riders: set[str] = set()

        for record in records:
            if record.rider_slug in seen_riders:
                msg = (
                    f"Rider {record.rider_name} ({record.rider_slug}) appears "
                    f"more than once in the {edition.year} startlist"
                )
                raise DuplicateRiderError(msg)
            seen_riders.add(record.rider_slug)

            rider, rider_is_new = self._resolve_rider(record)
            if rider_is_new:
                riders_created += 1
            else:
                riders_reused += 1

            if record.team_slug not in team_ids:
                team, team_is_new = self._resolve_team(edition, record)
                team_ids[record.team_slug] = team.id
                if team_is_new:
                    teams_created += 1

            self._save_participation(edition, rider.id, team_ids[record.team_slug], record)

        return StartlistIngestionSummary(
            edition_year=edition.year,
            riders_created=riders_created,
            riders_reused=riders_reused,
            teams_created=teams_created,
            participations=len(records),
        )

    def _resolve_rider(self, record: StartlistRecord) -> tuple[Rider, bool]:
        """Return the stored rider for this slug, or a new one, and which it was.

        A stored rider keeps its UUID because participations from earlier
        editions reference it, while name and nationality are refreshed so a
        corrected article is picked up.
        """
        stored = self._riders.get_by_source_slug(record.rider_slug)
        rider = Rider(
            id=stored.id if stored is not None else uuid4(),
            name=record.rider_name,
            nationality=record.nationality,
            source_slug=record.rider_slug,
            birth_date=stored.birth_date if stored is not None else None,
        )
        self._riders.save(rider)
        return rider, stored is None

    def _resolve_team(self, edition: TourEdition, record: StartlistRecord) -> tuple[Team, bool]:
        """Return this edition's row for the team, or a new one."""
        stored = self._teams.get_by_edition_and_slug(edition.id, record.team_slug)
        team = Team(
            id=stored.id if stored is not None else uuid4(),
            tour_edition_id=edition.id,
            name=record.team_name,
            source_slug=record.team_slug,
            nationality=stored.nationality if stored is not None else None,
        )
        self._teams.save(team)
        return team, stored is None

    def _save_participation(
        self, edition: TourEdition, rider_id: UUID, team_id: UUID, record: StartlistRecord
    ) -> None:
        stored = self._participations.get_by_edition_and_rider(edition.id, rider_id)
        self._participations.save(
            RiderParticipation(
                id=stored.id if stored is not None else uuid4(),
                tour_edition_id=edition.id,
                rider_id=rider_id,
                team_id=team_id,
                bib_number=record.bib_number,
                age=record.age,
                final_gc_position=record.final_gc_position,
                abandonment=record.abandonment,
                is_young_rider=record.is_young_rider,
            )
        )
