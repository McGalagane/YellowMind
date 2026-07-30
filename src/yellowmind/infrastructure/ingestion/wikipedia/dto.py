"""Source-shaped records produced by the Wikipedia parsers.

These mirror the article tables rather than the domain model. Mapping them onto
domain entities is a separate step, so parsing stays free of persistence and
identity concerns.
"""

from dataclasses import dataclass
from typing import Final

from yellowmind.domain.value_objects import AbandonmentKind

# Source tokens observed in the `Pos.` column, mapped to semantic kinds. The
# tokens were derived from every edition between 2015 and 2024 rather than
# assumed; an unlisted token becomes `UNKNOWN` so it degrades into a visible
# record instead of failing the whole parse.
# `HD` (hors delai) and `OTL` both mean the rider finished outside the time
# limit; they are the French and English notations for the same outcome.
ABANDONMENT_CODES: Final[dict[str, AbandonmentKind]] = {
    "DNF": AbandonmentKind.DID_NOT_FINISH,
    "DNS": AbandonmentKind.DID_NOT_START,
    "HD": AbandonmentKind.OUTSIDE_TIME_LIMIT,
    "OTL": AbandonmentKind.OUTSIDE_TIME_LIMIT,
    "COV": AbandonmentKind.COVID_WITHDRAWAL,
    "DSQ": AbandonmentKind.DISQUALIFIED,
}


@dataclass(frozen=True, slots=True)
class ParsedAbandonment:
    """Why and when a rider left the race, as printed by the source.

    Distinct from the domain's `Abandonment` because it keeps the raw token and
    an unvalidated stage number; narrowing happens when mapping to the domain.
    """

    kind: AbandonmentKind
    #: Stage the marker refers to: the stage abandoned during for ``DNF``, or
    #: the stage not taken for ``DNS``. Absent when the source omits it.
    stage_number: int | None
    #: Exact source token, kept so `HD` and `OTL` stay distinguishable and so
    #: an ``UNKNOWN`` kind remains diagnosable.
    raw_code: str

    def __post_init__(self) -> None:
        if self.stage_number is not None and self.stage_number < 1:
            msg = f"Stage number must be positive, got {self.stage_number}"
            raise ValueError(msg)
        if not self.raw_code:
            msg = "Abandonment raw_code cannot be empty"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class StartlistEntry:
    """One row of an edition's startlist table."""

    bib_number: int
    rider_name: str
    #: Wikipedia article slug, e.g. ``Jonas_Vingegaard``. Stable identity for
    #: matching the same rider across editions.
    rider_slug: str
    nationality: str
    #: Team name as printed for that edition, e.g. ``Team Jumbo-Visma``.
    team_name: str
    #: Wikipedia article slug for the team. Points at the article's *current*
    #: title, which may differ from ``team_name`` after a sponsor change, so it
    #: is the stable cross-edition key while ``team_name`` is historical.
    team_slug: str
    age: int | None
    #: Final general classification position, or ``None`` if the rider did not
    #: reach Paris.
    final_gc_position: int | None
    abandonment: ParsedAbandonment | None
    #: Eligible for the young rider classification, marked with a dagger.
    is_young_rider: bool

    def __post_init__(self) -> None:
        if self.bib_number < 1:
            msg = f"Bib number must be positive, got {self.bib_number}"
            raise ValueError(msg)
        if not self.rider_name:
            msg = "Rider name cannot be empty"
            raise ValueError(msg)
        if self.final_gc_position is not None and self.final_gc_position < 1:
            msg = f"GC position must be positive, got {self.final_gc_position}"
            raise ValueError(msg)
        if self.final_gc_position is not None and self.abandonment is not None:
            msg = f"Rider {self.rider_name} cannot both place and abandon"
            raise ValueError(msg)

    @property
    def finished(self) -> bool:
        """Whether the rider completed the race."""
        return self.final_gc_position is not None
