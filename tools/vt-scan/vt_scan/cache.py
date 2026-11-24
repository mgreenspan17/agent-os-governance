# Program: vt-scan / cache.py
# Use case: Local SQLite-backed verdict cache keyed by SHA-256 + VT key id,
#   so repeat lookups (or installs of the same binary) cost zero quota and so
#   the operational envelope is enforced offline.
# Version history:
#   0.1.0  2026-11-24  Phase A: schema + get/put/clear/stats. TTL differs by
#                        source (lookup=30d, upload=7d).

from __future__ import annotations

import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional


LOOKUP_TTL_SECONDS = 30 * 24 * 3600  # 30 days for hash-only lookups
UPLOAD_TTL_SECONDS = 7 * 24 * 3600   # 7 days for upload verdicts (verdict can change)

VERDICT_CLEAN = "clean"
VERDICT_DIRTY = "dirty"
VERDICT_UNKNOWN = "unknown"
VERDICT_ERROR = "error"
VERDICT_VALUES = {VERDICT_CLEAN, VERDICT_DIRTY, VERDICT_UNKNOWN, VERDICT_ERROR}

SOURCE_LOOKUP = "lookup"
SOURCE_UPLOAD = "upload"
SOURCE_VALUES = {SOURCE_LOOKUP, SOURCE_UPLOAD}


@dataclass
class CacheEntry:
    sha256: str
    verdict: str
    malicious: int
    suspicious: int
    undetected: int
    harmless: int
    engines_total: int
    vt_link: str
    cached_at: float
    expires_at: float
    source: str  # "lookup" | "upload"
    key_id: str  # masked key id (e.g. "VT-****abcd")

    def to_dict(self) -> dict:
        return {
            "sha256": self.sha256,
            "verdict": self.verdict,
            "malicious": self.malicious,
            "suspicious": self.suspicious,
            "undetected": self.undetected,
            "harmless": self.harmless,
            "engines_total": self.engines_total,
            "vt_link": self.vt_link,
            "cached_at": self.cached_at,
            "expires_at": self.expires_at,
            "source": self.source,
            "key_id": self.key_id,
        }


class VerdictCache:
    """Thread-safe SQLite-backed verdict cache. Single-file, single-table for Phase A."""

    def __init__(self, db_path: str) -> None:
        if not db_path:
            raise ValueError("db_path is required")
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_schema()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._lock, self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS verdicts (
                    sha256 TEXT PRIMARY KEY,
                    verdict TEXT NOT NULL,
                    malicious INTEGER NOT NULL,
                    suspicious INTEGER NOT NULL,
                    undetected INTEGER NOT NULL,
                    harmless INTEGER NOT NULL,
                    engines_total INTEGER NOT NULL,
                    vt_link TEXT NOT NULL DEFAULT '',
                    cached_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    source TEXT NOT NULL,
                    key_id TEXT NOT NULL DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS verdicts_expires_at_idx
                    ON verdicts(expires_at);
                """
            )

    def get(self, sha256: str, now: Optional[float] = None) -> Optional[CacheEntry]:
        if not sha256:
            return None
        ts = now if now is not None else time.time()
        with self._lock, self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM verdicts WHERE sha256 = ? AND expires_at > ?",
                (sha256, ts),
            ).fetchone()
        if not row:
            return None
        return _row_to_entry(row)

    def put(self, entry: CacheEntry) -> None:
        if entry.verdict not in VERDICT_VALUES:
            raise ValueError(f"invalid verdict: {entry.verdict!r}")
        if entry.source not in SOURCE_VALUES:
            raise ValueError(f"invalid source: {entry.source!r}")
        with self._lock, self._conn() as conn:
            conn.execute(
                """
                REPLACE INTO verdicts (
                    sha256, verdict, malicious, suspicious, undetected, harmless,
                    engines_total, vt_link, cached_at, expires_at, source, key_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.sha256,
                    entry.verdict,
                    entry.malicious,
                    entry.suspicious,
                    entry.undetected,
                    entry.harmless,
                    entry.engines_total,
                    entry.vt_link,
                    entry.cached_at,
                    entry.expires_at,
                    entry.source,
                    entry.key_id,
                ),
            )

    def stats(self, now: Optional[float] = None) -> dict:
        ts = now if now is not None else time.time()
        with self._lock, self._conn() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN expires_at > ? THEN 1 ELSE 0 END) AS live,
                    SUM(CASE WHEN source = 'lookup' THEN 1 ELSE 0 END) AS lookups,
                    SUM(CASE WHEN source = 'upload' THEN 1 ELSE 0 END) AS uploads
                FROM verdicts
                """,
                (ts,),
            ).fetchone()
        return {
            "db_path": self.db_path,
            "total": int(row["total"] or 0),
            "live": int(row["live"] or 0),
            "lookups": int(row["lookups"] or 0),
            "uploads": int(row["uploads"] or 0),
            "ttl_seconds": {"lookup": LOOKUP_TTL_SECONDS, "upload": UPLOAD_TTL_SECONDS},
        }

    def clear(self) -> int:
        with self._lock, self._conn() as conn:
            cur = conn.execute("DELETE FROM verdicts")
            return cur.rowcount


def _row_to_entry(row: sqlite3.Row) -> CacheEntry:
    return CacheEntry(
        sha256=row["sha256"],
        verdict=row["verdict"],
        malicious=int(row["malicious"]),
        suspicious=int(row["suspicious"]),
        undetected=int(row["undetected"]),
        harmless=int(row["harmless"]),
        engines_total=int(row["engines_total"]),
        vt_link=row["vt_link"],
        cached_at=float(row["cached_at"]),
        expires_at=float(row["expires_at"]),
        source=row["source"],
        key_id=row["key_id"],
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("usage: python -m vt_scan.cache <db_path>", file=sys.stderr)
        sys.exit(2)
    cache = VerdictCache(sys.argv[1])
    print(cache.stats())
