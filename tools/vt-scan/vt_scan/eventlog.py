# Program: vt-scan / eventlog.py
# Use case: Append-only structured EventLog writer aligned with
#   constitution/eventlog-governance.md. Keeps `event_id`, `timestamp`,
#   `event_type`, `category`, `source_system`, `producer_id`,
#   `idempotency_key`, `hash`, `raw_payload` on every record.
#   Secret-keyed fields are redacted before the record is flushed.
# Version history:
#   0.1.0  2026-11-24  Phase A: JSONL append with redaction + idempotent
#                        keying on (tool_install_id, event_type).

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional


# Field names required by the EventLog spine. Module stays honest if we ever
# add a writer that omits one of these.
SPINE_FIELDS = (
    "event_id",
    "timestamp",
    "event_type",
    "category",
    "source_system",
    "producer_id",
    "idempotency_key",
    "hash",
    "raw_payload",
)


# Field names whose presence in a payload triggers redaction to {{VT_API_KEY}}.
# We refuse to log secret-shaped values; this matches SECURITY_POLICY.md §1.4.
SECRET_FIELD_NAMES = {
    "api_key",
    "x-apikey",
    "x_api_key",
    "apikey",
    "token",
    "password",
    "secret",
    "authorization",
}


class EventLog:
    """Append-only JSONL writer with per-process locking.

    Each `append` writes one line and flushes before returning. The lock keeps
    concurrent processes safe; this is enough for Phase A. Phase B can add an
    OS-level file lock if multi-process contention becomes observable."""

    def __init__(self, log_path: str) -> None:
        if not log_path:
            raise ValueError("log_path is required")
        self.log_path = log_path
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    @contextmanager
    def _open(self) -> Iterator:
        with self._lock:
            with open(self.log_path, "a", encoding="utf-8") as fh:
                yield fh

    def append(
        self,
        event_type: str,
        *,
        category: str,
        idempotency_key: str,
        raw_payload: Optional[dict] = None,
        tool_install_id: Optional[str] = None,
        producer_id: str = "vt-scan",
        source_system: str = "vt-scan",
    ) -> dict:
        if not event_type:
            raise ValueError("event_type is required")
        if not idempotency_key:
            raise ValueError("idempotency_key is required (use the sha256)")

        tid = tool_install_id or str(uuid.uuid4())
        raw_in = raw_payload or {}
        raw_redacted = redact(raw_in)
        # Hash the REDACTED payload so secrets never enter EventLog hashes.
        payload_hash = hashlib.sha256(
            json.dumps(_canonical(raw_redacted), sort_keys=True).encode("utf-8")
        ).hexdigest()
        record = {
            "event_id": str(uuid.uuid4()),
            "timestamp": _iso_utc_now(),
            "event_type": event_type,
            "category": category,
            "source_system": source_system,
            "producer_id": producer_id,
            "idempotency_key": idempotency_key,
            "hash": payload_hash,
            "tool_install_id": tid,
            "raw_payload": raw_redacted,
        }
        with self._open() as fh:
            fh.write(json.dumps(record, sort_keys=True))
            fh.write("\n")
        return record


def redact(payload: dict) -> dict:
    """Walk a payload and replace any value under a secret-shaped key with the
    `{{VT_API_KEY}}` placeholder. Lists are walked; primitives are passed
    through. We do not pattern-match values (too brittle)."""
    if not isinstance(payload, dict):
        return payload
    out: dict = {}
    for k, v in payload.items():
        if isinstance(k, str) and k.lower() in SECRET_FIELD_NAMES:
            out[k] = "{{VT_API_KEY}}"
        elif isinstance(v, dict):
            out[k] = redact(v)
        elif isinstance(v, list):
            out[k] = [redact(item) if isinstance(item, dict) else item for item in v]
        else:
            out[k] = v
    return out


def _canonical(payload: dict) -> dict:
    return json.loads(json.dumps(payload, sort_keys=True))


def _iso_utc_now() -> str:
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"  # noqa: DTZ005


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("usage: python -m vt_scan.eventlog <log_path> <event_type>", file=sys.stderr)
        sys.exit(2)
    log = EventLog(sys.argv[1])
    entry = log.append(
        event_type=sys.argv[2],
        category="tool_scan",
        idempotency_key="manual-" + os.urandom(4).hex(),
        raw_payload={"note": "manual test entry"},
    )
    print(json.dumps(entry, sort_keys=True, indent=2))
