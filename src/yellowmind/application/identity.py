"""Resolve a source rider identifier to a stored rider within one edition."""

from __future__ import annotations

import re
import unicodedata
from uuid import UUID

from yellowmind.domain.entities import Rider


def fold_identity(value: str) -> str:
    """Lowercase, strip accents and punctuation, for cross-article matching.

    Wikipedia articles for the same rider disagree on accents (``Niccolò`` vs
    ``Niccolo``) and capitalisation (``Van`` vs ``van``). Folding collapses
    those without inventing a full alias table.
    """
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", without_marks.lower())


def family_key(name: str) -> str:
    """Return the folded family name (last whitespace-separated token)."""
    cleaned = name.replace("_", " ").split("(", 1)[0].strip()
    parts = cleaned.split()
    return fold_identity(parts[-1]) if parts else ""


class EditionRiderIndex:
    """Lookup helpers over the riders who started one edition.

    Matching is scoped to the edition so a family-name fallback cannot jump to
    a rider who was not on the startlist that year.
    """

    def __init__(self, riders: list[Rider]) -> None:
        self._by_slug = {rider.source_slug: rider for rider in riders}
        self._by_folded_slug: dict[str, list[Rider]] = {}
        self._by_folded_name: dict[str, list[Rider]] = {}
        self._by_family: dict[str, list[Rider]] = {}
        for rider in riders:
            self._by_folded_slug.setdefault(fold_identity(rider.source_slug), []).append(rider)
            self._by_folded_name.setdefault(fold_identity(rider.name), []).append(rider)
            self._by_family.setdefault(family_key(rider.name), []).append(rider)

    def resolve(self, slug: str, name: str) -> Rider | None:
        """Return the matching rider, or None when identity is ambiguous."""
        exact = self._by_slug.get(slug)
        if exact is not None:
            return exact

        folded_slug = self._unique(self._by_folded_slug.get(fold_identity(slug), []))
        if folded_slug is not None:
            return folded_slug

        folded_name = self._unique(self._by_folded_name.get(fold_identity(name), []))
        if folded_name is not None:
            return folded_name

        return self._unique(self._by_family.get(family_key(name), []))

    @staticmethod
    def _unique(candidates: list[Rider]) -> Rider | None:
        return candidates[0] if len(candidates) == 1 else None

    def rider_ids(self) -> set[UUID]:
        """Return every rider id in the index."""
        return {rider.id for rider in self._by_slug.values()}
