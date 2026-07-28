"""Wikipedia client configuration."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Self

_DEFAULT_BASE_URL = "https://en.wikipedia.org"

# Wikipedia's API etiquette asks for a descriptive User-Agent identifying the
# project and a contact address, so requests can be traced to their source.
_DEFAULT_USER_AGENT = (
    "YellowMind/0.1 (https://github.com/McGalagane/YellowMind; portfolio ML project)"
)


@dataclass(frozen=True, slots=True)
class WikipediaConfig:
    """Configuration for the Wikipedia REST API client."""

    base_url: str = _DEFAULT_BASE_URL
    user_agent: str = _DEFAULT_USER_AGENT
    rate_limit_seconds: float = 1.0
    max_retries: int = 3
    cache_dir: Path = Path("data/cache/wikipedia")
    timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> Self:
        """Load configuration from environment variables."""
        return cls(
            base_url=os.getenv("WIKIPEDIA_BASE_URL", _DEFAULT_BASE_URL),
            user_agent=os.getenv("WIKIPEDIA_USER_AGENT", _DEFAULT_USER_AGENT),
            rate_limit_seconds=float(os.getenv("WIKIPEDIA_RATE_LIMIT_SECONDS", "1.0")),
            max_retries=int(os.getenv("WIKIPEDIA_MAX_RETRIES", "3")),
            cache_dir=Path(os.getenv("WIKIPEDIA_CACHE_DIR", "data/cache/wikipedia")),
            timeout_seconds=float(os.getenv("WIKIPEDIA_TIMEOUT_SECONDS", "30.0")),
        )
