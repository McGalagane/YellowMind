"""Open-Meteo client configuration."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Self

_DEFAULT_ARCHIVE_BASE_URL = "https://archive-api.open-meteo.com"
_DEFAULT_GEOCODING_BASE_URL = "https://geocoding-api.open-meteo.com"
_DEFAULT_USER_AGENT = (
    "YellowMind/0.1 (https://github.com/McGalagane/YellowMind; portfolio ML project)"
)


@dataclass(frozen=True, slots=True)
class OpenMeteoConfig:
    """Configuration for the Open-Meteo archive and geocoding APIs."""

    archive_base_url: str = _DEFAULT_ARCHIVE_BASE_URL
    geocoding_base_url: str = _DEFAULT_GEOCODING_BASE_URL
    user_agent: str = _DEFAULT_USER_AGENT
    rate_limit_seconds: float = 0.25
    max_retries: int = 3
    cache_dir: Path = Path("data/cache/open_meteo")
    timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> Self:
        """Load configuration from environment variables."""
        return cls(
            archive_base_url=os.getenv("OPEN_METEO_ARCHIVE_BASE_URL", _DEFAULT_ARCHIVE_BASE_URL),
            geocoding_base_url=os.getenv(
                "OPEN_METEO_GEOCODING_BASE_URL", _DEFAULT_GEOCODING_BASE_URL
            ),
            user_agent=os.getenv("OPEN_METEO_USER_AGENT", _DEFAULT_USER_AGENT),
            rate_limit_seconds=float(os.getenv("OPEN_METEO_RATE_LIMIT_SECONDS", "0.25")),
            max_retries=int(os.getenv("OPEN_METEO_MAX_RETRIES", "3")),
            cache_dir=Path(os.getenv("OPEN_METEO_CACHE_DIR", "data/cache/open_meteo")),
            timeout_seconds=float(os.getenv("OPEN_METEO_TIMEOUT_SECONDS", "30.0")),
        )
