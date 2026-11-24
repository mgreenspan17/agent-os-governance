# Program: vt-scan / tests/test_rate_limit.py
# Use case: Verify token bucket and daily window behavior, plus the combined
#   VTRateLimiter envelope.

from __future__ import annotations

import time

import pytest

from vt_scan.rate_limit import (
    DayWindow,
    RateLimitExceeded,
    TokenBucket,
    VTRateLimiter,
    VT_PER_DAY_LIMIT,
    VT_PER_MINUTE_LIMIT,
)


def test_token_bucket_drains_then_refuses() -> None:
    bucket = TokenBucket(capacity=2.0, refill_per_second=1000.0)
    bucket.try_acquire()
    bucket.try_acquire()
    with pytest.raises(RateLimitExceeded) as ei:
        bucket.try_acquire()
    assert ei.value.kind == "per_minute"


def test_token_bucket_refill_uses_refill_rate() -> None:
    bucket = TokenBucket(capacity=2.0, refill_per_second=2.0)
    bucket.try_acquire()
    bucket.try_acquire()
    with pytest.raises(RateLimitExceeded):
        bucket.try_acquire()
    # 0.5 second of refill => 1 token available.
    time.sleep(0.6)
    bucket.try_acquire()
    with pytest.raises(RateLimitExceeded):
        bucket.try_acquire()


def test_day_window_resets_at_midnight(monkeypatch: pytest.MonkeyPatch) -> None:
    w = DayWindow(limit_per_day=2)
    w.try_acquire()
    w.try_acquire()
    with pytest.raises(RateLimitExceeded) as ei:
        w.try_acquire()
    assert ei.value.kind == "per_day"

    # Force the window to roll to "tomorrow" and confirm we can acquire again.
    w._state["day_utc"] = "1999-01-01"
    w.try_acquire()


def test_vt_rate_limiter_combines_windows() -> None:
    # per_minute=10 keeps the minute gate silent; per_day=2 makes the day
    # window the first gate to fire so we can assert its kind directly.
    rl = VTRateLimiter(per_minute=10, per_day=2)
    rl.acquire()
    rl.acquire()
    with pytest.raises(RateLimitExceeded) as ei:
        rl.acquire()
    assert ei.value.kind == "per_day"


def test_vt_rate_limiter_defaults_match_vt_public_envelope() -> None:
    assert VT_PER_MINUTE_LIMIT == 4
    assert VT_PER_DAY_LIMIT == 500


def test_vt_rate_limiter_stats_exposes_envelope() -> None:
    rl = VTRateLimiter()
    s = rl.stats()
    assert s["public_envelope"] == {"per_minute": 4, "per_day": 500}
    assert s["per_minute"]["capacity"] == 4
    assert s["per_day"]["limit"] == 500


def test_token_bucket_rejects_invalid_params() -> None:
    with pytest.raises(ValueError):
        TokenBucket(capacity=0, refill_per_second=1.0)
    with pytest.raises(ValueError):
        TokenBucket(capacity=1.0, refill_per_second=0)
