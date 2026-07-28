"""File-based HTTP response cache."""

import hashlib
from pathlib import Path


class FileResponseCache:
    """Cache HTTP responses on disk keyed by URL."""

    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, url: str) -> str | None:
        """Return cached content for a URL, or None if not cached."""
        path = self._path_for_url(url)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def set(self, url: str, content: str) -> None:
        """Store response content for a URL."""
        path = self._path_for_url(url)
        path.write_text(content, encoding="utf-8")

    def _path_for_url(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{digest}.html"
