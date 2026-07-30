"""Unit tests for edition-scoped rider identity resolution."""

from uuid import uuid4

from yellowmind.application.identity import EditionRiderIndex, family_key, fold_identity
from yellowmind.domain.entities import Rider


def _rider(slug: str, name: str) -> Rider:
    return Rider(id=uuid4(), name=name, nationality="Unknown", source_slug=slug)


def test_fold_identity_strips_accents_and_case() -> None:
    assert fold_identity("Niccolò_Bonifazio") == fold_identity("Niccolo_Bonifazio")
    assert fold_identity("Greg_Van_Avermaet") == fold_identity("Greg_van_Avermaet")


def test_family_key_uses_last_token() -> None:
    assert family_key("Jhoan Esteban Chaves") == "chaves"
    assert family_key("Tom_Pidcock") == "pidcock"


def test_resolves_exact_slug() -> None:
    rider = _rider("Adam_Yates", "Adam Yates")
    assert EditionRiderIndex([rider]).resolve("Adam_Yates", "Adam Yates") is rider


def test_resolves_accent_drift_in_slug() -> None:
    rider = _rider("Niccolò_Bonifazio", "Niccolò Bonifazio")
    index = EditionRiderIndex([rider])

    assert index.resolve("Niccolo_Bonifazio", "Niccolo Bonifazio") is rider


def test_resolves_by_unique_family_name() -> None:
    """Tom vs Thomas Pidcock: same person, different Wikipedia articles."""
    rider = _rider("Thomas_Pidcock", "Thomas Pidcock")
    index = EditionRiderIndex([rider])

    assert index.resolve("Tom_Pidcock", "Tom Pidcock") is rider


def test_does_not_guess_when_family_name_is_shared() -> None:
    """Adam and Simon Yates must not collapse into each other."""
    adam = _rider("Adam_Yates", "Adam Yates")
    simon = _rider("Simon_Yates_(cyclist)", "Simon Yates")
    index = EditionRiderIndex([adam, simon])

    assert index.resolve("Unknown_Yates", "Someone Yates") is None


def test_resolves_extended_given_name_to_startlist_name() -> None:
    rider = _rider("Esteban_Chaves", "Esteban Chaves")
    index = EditionRiderIndex([rider])

    # Family-name uniqueness covers this; folded names differ.
    assert index.resolve("Jhoan_Esteban_Chaves", "Jhoan Esteban Chaves") is rider
