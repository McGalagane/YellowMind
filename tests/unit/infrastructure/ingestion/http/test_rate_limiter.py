"""Tests for the outbound request rate limiter."""

import pytest

from yellowmind.infrastructure.ingestion.http import RateLimiter


class FakeClock:
    """Deterministic monotonic clock advanced only by recorded sleeps."""

    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_rejects_negative_interval() -> None:
    with pytest.raises(ValueError, match="Rate limit"):
        RateLimiter(-0.1)


def test_zero_interval_never_sleeps() -> None:
    clock = FakeClock()
    limiter = RateLimiter(0, sleep=clock.sleep, monotonic=clock.monotonic)

    limiter.wait()
    limiter.wait()

    assert clock.sleeps == []


def test_first_request_is_not_delayed() -> None:
    clock = FakeClock()
    limiter = RateLimiter(1.0, sleep=clock.sleep, monotonic=clock.monotonic)

    limiter.wait()

    assert clock.sleeps == []


def test_sleeps_only_for_the_remaining_interval() -> None:
    clock = FakeClock()
    limiter = RateLimiter(1.0, sleep=clock.sleep, monotonic=clock.monotonic)

    limiter.wait()
    # 0.25 and 0.75 are exact in binary floating point, so this compares cleanly.
    clock.advance(0.25)
    limiter.wait()

    assert clock.sleeps == [0.75]


def test_no_sleep_when_interval_already_elapsed() -> None:
    clock = FakeClock()
    limiter = RateLimiter(1.0, sleep=clock.sleep, monotonic=clock.monotonic)

    limiter.wait()
    clock.advance(5.0)
    limiter.wait()

    assert clock.sleeps == []
