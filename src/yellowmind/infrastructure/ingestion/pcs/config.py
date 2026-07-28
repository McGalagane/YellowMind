"""PCS client configuration."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Self

_DEFAULT_BASE_URL = "https://www.procyclingstats.com"
_DEFAULT_USER_AGENT = "YellowMind/0.1 (+https://github.com/McGalagane/YellowMind)"


@dataclass(frozen=True, slots=True)
class PCSConfig:
    """Configuration for the ProCyclingStats HTTP client."""

    base_url: str = _DEFAULT_BASE_URL
    user_agent: str = _DEFAULT_USER_AGENT
    rate_limit_seconds: float = 1.0
    max_retries: int = 3
    cache_dir: Path = Path("data/cache/pcs")
    timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> Self:
        """Load configuration from environment variables."""
        return cls(
            base_url=os.getenv("PCS_BASE_URL", _DEFAULT_BASE_URL),
            user_agent=os.getenv("PCS_USER_AGENT", _DEFAULT_USER_AGENT),
            rate_limit_seconds=float(os.getenv("PCS_RATE_LIMIT_SECONDS", "1.0")),
            max_retries=int(os.getenv("PCS_MAX_RETRIES", "3")),
            cache_dir=Path(os.getenv("PCS_CACHE_DIR", "data/cache/pcs")),
            timeout_seconds=float(os.getenv("PCS_TIMEOUT_SECONDS", "30.0")),
        )
