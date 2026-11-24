# Program: vt-scan / rate_limit.py
# Use case: Gate VT API calls behind a token bucket (4 req/min) and a daily
#   counter (500 req/day). Refuses rather than silently dropping so callers
#   can abort the install rather than leave it half-processed.
# Version history:
#   0.1.0  2026-11-24  Phase A: TokenBucket + DayWindow + VTRateLimiter.

from __future__ import annotations

import datetime as _dt
import threading
import time
from dataclasses import dataclass, field
from typing import Optional


VT_PER_MINUTE_LIMIT = 4
VT_PER_DAY_LIMIT = 500


class RateLimitExceeded(Exception):
    """Raised when the VT envelope would be exceeded. The caller should abort
    the install and surface a clear error rather than retrying blindly."""

    def __init__(self, kind: str, retry_after_seconds: float) -> None:
        super().__init__(f"rate limit exceeded: {kind}")
        self.kind = kind
        self.retry_after_seconds = retry_after_seconds


@dataclass
class TokenBucket:
    """Classic token bucket. `capacity` is the burst size; refill is continuous."""

    capacity: float
    refill_per_second: float
    tokens: float = field(init=False)
    last_refill_at: float = field(init=False)
    _lock: threading.Lock = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("capacity must be positive")
        if self.refill_per_second <= 0:
            raise ValueError("refill_per_second must be positive")
        self.tokens = float(self.capacity)
        self.last_refill_at = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill_at
        if elapsed <= 0:
            return
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)
        self.last_refill_at = now

    def try_acquire(self, n: float = 1.0) -> None:
        with self._lock:
            self._refill()
            if self.tokens >= n:
                self.tokens -= n
                return
            deficit = n - self.tokens
            retry_after = deficit / self.refill_per_second
            raise RateLimitExceeded("per_minute", retry_after)


@dataclass
class DayWindow:
    """A UTC-day-bucketed counter. Resets at UTC midnight."""

    limit_per_day: int
    _state: dict = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._state = {"day_utc": _utc_yyyymmdd(), "count": 0}

    def try_acquire(self, n: int = 1) -> None:
        today = _utc_yyyymmdd()
        if today != self._state["day_utc"]:
            self._state = {"day_utc": today, "count": 0}
        if self._state["count"] + n > self.limit_per_day:
            retry_after = _seconds_until_next_utc_midnight()
            raise RateLimitExceeded("per_day", retry_after)
        self._state["count"] += n


class VTRateLimiter:
    """Combined per-minute and per-day envelope for the VT public API.

    Call `acquire()` exactly once per planned network call; the limiter refuses
    with `RateLimitExceeded` if either window would be exceeded."""

    def __init__(
        self,
        per_minute: int = VT_PER_MINUTE_LIMIT,
        per_day: int = VT_PER_DAY_LIMIT,
    ) -> None:
        self.bucket = TokenBucket(
            capacity=float(per_minute),
            refill_per_second=per_minute / 60.0,
        )
        self.window = DayWindow(limit_per_day=per_day)

    def acquire(self) -> None:
        # Per-day gate fires first so a misconfigured minute-pace never silently
        # exhausts the daily quota before the daily gate notices.
        self.window.try_acquire()
        self.bucket.try_acquire()

    def stats(self) -> dict:
        return {
            "per_minute": {
                "capacity": self.bucket.capacity,
                "tokens": round(self.bucket.tokens, 3),
            },
            "per_day": {
                "limit": self.window.limit_per_day,
                "count": self.window._state["count"],
                "day_utc": self.window._state["day_utc"],
            },
            "public_envelope": {
                "per_minute": VT_PER_MINUTE_LIMIT,
                "per_day": VT_PER_DAY_LIMIT,
            },
        }


def _utc_yyyymmdd() -> str:
    # NOTE: utcnow() is fine for Python 3.9 (deprecated only in 3.12+).
    return _dt.datetime.utcnow().strftime("%Y-%m-%d")  # noqa: DTZ005


def _seconds_until_next_utc_midnight() -> float:
    now = _dt.datetime.utcnow()  # noqa: DTZ005
    tomorrow = (now + _dt.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return max(1.0, (tomorrow - now).total_seconds())


if __name__ == "__main__":
    rl = VTRateLimiter()
    print("rate limit envelope:", rl.stats())
