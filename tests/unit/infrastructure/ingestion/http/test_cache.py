"""Tests for the file-based response cache."""

from pathlib import Path

from yellowmind.infrastructure.ingestion.http import FileResponseCache


def test_get_returns_none_for_unknown_url(tmp_path: Path) -> None:
    assert FileResponseCache(tmp_path).get("https://example.test/missing") is None


def test_set_then_get_round_trips_content(tmp_path: Path) -> None:
    cache = FileResponseCache(tmp_path)
    cache.set("https://example.test/page", "<html>ok</html>")

    assert cache.get("https://example.test/page") == "<html>ok</html>"


def test_distinct_urls_do_not_collide(tmp_path: Path) -> None:
    cache = FileResponseCache(tmp_path)
    cache.set("https://example.test/a", "first")
    cache.set("https://example.test/b", "second")

    assert cache.get("https://example.test/a") == "first"
    assert cache.get("https://example.test/b") == "second"


def test_cache_survives_a_new_instance(tmp_path: Path) -> None:
    FileResponseCache(tmp_path).set("https://example.test/page", "persisted")

    assert FileResponseCache(tmp_path).get("https://example.test/page") == "persisted"


def test_creates_missing_cache_directory(tmp_path: Path) -> None:
    nested = tmp_path / "deep" / "cache"

    FileResponseCache(nested).set("https://example.test/page", "ok")

    assert nested.is_dir()


def test_unicode_content_round_trips(tmp_path: Path) -> None:
    cache = FileResponseCache(tmp_path)
    cache.set("https://example.test/rider", "Tadej Pogačar — Jonas Vingegaard")

    assert cache.get("https://example.test/rider") == "Tadej Pogačar — Jonas Vingegaard"
