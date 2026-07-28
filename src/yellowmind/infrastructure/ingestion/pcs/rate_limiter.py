"""Simple rate limiter for HTTP requests."""

import time


class RateLimiter:
    """Enforce a minimum interval between consecutive requests."""

    def __init__(self, min_interval_seconds: float) -> None:
        if min_interval_seconds < 0:
            msg = "Rate limit interval cannot be negative"
            raise ValueError(msg)
        self._min_interval = min_interval_seconds
        self._last_request_at = 0.0

    def wait(self) -> None:
        """Block until the next request is allowed."""
        if self._min_interval == 0:
            return

        elapsed = time.monotonic() - self._last_request_at
        remaining = self._min_interval - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_request_at = time.monotonic()
