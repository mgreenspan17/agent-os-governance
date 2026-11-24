# Program: vt-scan / tests/test_cache.py
# Use case: Verify verdict cache put/get/clear semantics, TTL behavior, and
#   schema invariants.

from __future__ import annotations

import time
from pathlib import Path

import pytest

from vt_scan.cache import (
    LOOKUP_TTL_SECONDS,
    SOURCE_LOOKUP,
    SOURCE_UPLOAD,
    VERDICT_CLEAN,
    VERDICT_DIRTY,
    VERDICT_ERROR,
    VERDICT_UNKNOWN,
    CacheEntry,
    VerdictCache,
)


def _entry(sha256: str, verdict: str = VERDICT_CLEAN, expires_at: float | None = None) -> CacheEntry:
    now = time.time()
    return CacheEntry(
        sha256=sha256,
        verdict=verdict,
        malicious=0,
        suspicious=0,
        undetected=10,
        harmless=20,
        engines_total=30,
        vt_link=f"https://www.virustotal.com/file/{sha256}",
        cached_at=now,
        expires_at=expires_at if expires_at is not None else now + 3600,
        source=SOURCE_LOOKUP,
        key_id="VT-****abcd",
    )


def test_cache_round_trip(tmp_path: Path) -> None:
    db = tmp_path / "cache.sqlite"
    cache = VerdictCache(str(db))
    e = _entry("a" * 64)
    cache.put(e)
    fetched = cache.get(e.sha256)
    assert fetched is not None
    assert fetched.sha256 == e.sha256
    assert fetched.verdict == VERDICT_CLEAN
    assert fetched.vt_link == e.vt_link


def test_cache_ttl_hides_expired(tmp_path: Path) -> None:
    db = tmp_path / "cache.sqlite"
    cache = VerdictCache(str(db))
    e = _entry("b" * 64, expires_at=time.time() - 1)
    cache.put(e)
    assert cache.get(e.sha256) is None


def test_cache_distinguishes_lookup_vs_upload_ttl() -> None:
    assert LOOKUP_TTL_SECONDS == 30 * 24 * 3600
    assert SOURCE_LOOKUP != SOURCE_UPLOAD


def test_cache_rejects_invalid_verdict(tmp_path: Path) -> None:
    db = tmp_path / "cache.sqlite"
    cache = VerdictCache(str(db))
    e = _entry("c" * 64, verdict="not-a-real-verdict")
    with pytest.raises(ValueError):
        cache.put(e)


def test_cache_rejects_invalid_source(tmp_path: Path) -> None:
    db = tmp_path / "cache.sqlite"
    cache = VerdictCache(str(db))
    e = _entry("d" * 64)
    e.source = "transmogrified"
    with pytest.raises(ValueError):
        cache.put(e)


def test_cache_clear_returns_rowcount(tmp_path: Path) -> None:
    db = tmp_path / "cache.sqlite"
    cache = VerdictCache(str(db))
    for i in range(5):
        cache.put(_entry(f"{i:064x}"))
    assert cache.clear() == 5
    s = cache.stats()
    assert s["total"] == 0


def test_cache_stats_counts_lookup_and_upload(tmp_path: Path) -> None:
    db = tmp_path / "cache.sqlite"
    cache = VerdictCache(str(db))
    cache.put(_entry("00" * 32, verdict=VERDICT_CLEAN))  # default source = lookup
    e = _entry("11" * 32, verdict=VERDICT_DIRTY)
    e.source = SOURCE_UPLOAD
    cache.put(e)
    s = cache.stats()
    assert s["lookups"] == 1
    assert s["uploads"] == 1
    assert s["live"] == 2


def test_cache_get_rejects_empty_sha(tmp_path: Path) -> None:
    cache = VerdictCache(str(tmp_path / "cache.sqlite"))
    assert cache.get("") is None


def test_cache_distinguishes_verdict_labels() -> None:
    # Smoke test confirming the export surface uses canonical strings.
    assert {VERDICT_CLEAN, VERDICT_DIRTY, VERDICT_UNKNOWN, VERDICT_ERROR} == {
        "clean",
        "dirty",
        "unknown",
        "error",
    }
