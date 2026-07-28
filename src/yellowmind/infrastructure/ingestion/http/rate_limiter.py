"""Rate limiter for outbound HTTP requests."""

import time
from collections.abc import Callable


class RateLimiter:
    """Enforce a minimum interval between consecutive requests."""

    def __init__(
        self,
        min_interval_seconds: float,
        *,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if min_interval_seconds < 0:
            msg = "Rate limit interval cannot be negative"
            raise ValueError(msg)
        self._min_interval = min_interval_seconds
        self._sleep = sleep
        self._monotonic = monotonic
        self._last_request_at: float | None = None

    def wait(self) -> None:
        """Block until the next request is allowed."""
        if self._min_interval == 0:
            return

        if self._last_request_at is not None:
            remaining = self._min_interval - (self._monotonic() - self._last_request_at)
            if remaining > 0:
                self._sleep(remaining)

        self._last_request_at = self._monotonic()
