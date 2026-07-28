"""Port for external cycling data providers."""

from abc import ABC, abstractmethod


class CyclingDataSource(ABC):
    """Abstract interface for fetching raw data from a cycling statistics provider."""

    @abstractmethod
    def fetch(self, path: str) -> str:
        """Fetch raw response body for a provider-relative path or absolute URL."""
