"""Parse cycling time cells into absolute times and gaps.

Wikipedia prints absolute times for the leader (`4h 22' 49"`, `14' 56"`) and
signed gaps for everyone else (`+ 5"`, `+ 1' 10"`, `+ 0"`). The apostrophe and
quote marks used as minute/second markers vary between a typewriter apostrophe
and a typographic prime, so both are accepted.
"""

from __future__ import annotations

import re
from typing import Final

# Minute and second markers as they appear across editions.
_MIN: Final[str] = r"['\u2032]"
_SEC: Final[str] = r"[\"\u2033]"

_ABSOLUTE: Final[re.Pattern[str]] = re.compile(
    rf"^(?:(?P<hours>\d+)\s*h\s*)?(?:(?P<minutes>\d+)\s*{_MIN}\s*)?(?P<seconds>\d+)\s*{_SEC}$"
)
_GAP: Final[re.Pattern[str]] = re.compile(
    rf"^\+\s*(?:(?P<hours>\d+)\s*h\s*)?(?:(?P<minutes>\d+)\s*{_MIN}\s*)?(?P<seconds>\d+)\s*{_SEC}$"
)


class TimeParseError(Exception):
    """Raised when a time cell cannot be read."""


def parse_time_cell(value: str) -> tuple[str, int]:
    """Return the cleaned display time and its duration as seconds.

    For a gap the seconds value is the gap itself; for an absolute time it is
    the elapsed duration. Both are useful: the display string is what the
    source printed, the integer is what models and validations compare.

    ``s.t.`` (same time) is not handled here: it has no intrinsic duration and
    must be resolved against the previous rider's gap by the caller.
    """
    text = " ".join(value.split())
    if not text:
        msg = "Time cell is empty"
        raise TimeParseError(msg)
    if _is_same_time(text):
        msg = "s.t. has no intrinsic duration"
        raise TimeParseError(msg)

    gap = _GAP.match(text)
    if gap is not None:
        return text, _to_seconds(gap)

    absolute = _ABSOLUTE.match(text)
    if absolute is not None:
        return text, _to_seconds(absolute)

    msg = f"Cannot read time from {value!r}"
    raise TimeParseError(msg)


def parse_gap_seconds(value: str) -> int:
    """Return a gap cell as seconds, or 0 for an absolute (leader) time."""
    text = " ".join(value.split())
    if _is_same_time(text):
        msg = "s.t. has no intrinsic duration"
        raise TimeParseError(msg)
    gap = _GAP.match(text)
    if gap is not None:
        return _to_seconds(gap)
    if _ABSOLUTE.match(text) is not None:
        return 0
    msg = f"Cannot read time from {value!r}"
    raise TimeParseError(msg)


def is_same_time(value: str) -> bool:
    """Whether ``value`` is the ``s.t.`` (same time) marker used in 2016."""
    return _is_same_time(" ".join(value.split()))


def _is_same_time(text: str) -> bool:
    return text.lower().rstrip(".") == "s.t"


def _to_seconds(match: re.Match[str]) -> int:
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    return hours * 3600 + minutes * 60 + seconds
