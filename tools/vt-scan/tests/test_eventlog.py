# Program: vt-scan / tests/test_eventlog.py
# Use case: Verify EventLog spine-field completeness, secret redaction,
#   idempotency across repeated appends, and JSONL-on-disk shape.

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vt_scan.eventlog import SPINE_FIELDS, EventLog, redact


@pytest.fixture()
def log_path(tmp_path: Path) -> Path:
    return tmp_path / "eventlog.jsonl"


def test_eventlog_appends_one_line_per_call(log_path: Path) -> None:
    log = EventLog(str(log_path))
    log.append(
        "tool_scan_started",
        category="tool_scan",
        idempotency_key="h" * 64,
        raw_payload={"path": "x"},
    )
    log.append(
        "tool_scan_lookup_completed",
        category="tool_scan",
        idempotency_key="h" * 64,
        raw_payload={"sha256": "h" * 64, "cache_hit": True},
    )
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    for line in lines:
        json.loads(line)


def test_eventlog_records_all_spine_fields(log_path: Path) -> None:
    log = EventLog(str(log_path))
    record = log.append(
        "tool_scan_started",
        category="tool_scan",
        idempotency_key="h" * 64,
        raw_payload={"note": "smoke"},
    )
    for field_name in SPINE_FIELDS:
        assert field_name in record, f"missing spine field {field_name}"


def test_eventlog_redacts_secret_keys(log_path: Path) -> None:
    log = EventLog(str(log_path))
    record = log.append(
        "tool_scan_started",
        category="tool_scan",
        idempotency_key="h" * 64,
        raw_payload={
            "api_key": "supersecret-do-not-log",
            "x-apikey": "supersecret-do-not-log",
            "nested": {"Token": "abc"},
            "benign": "keep me",
        },
    )
    payload = record["raw_payload"]
    assert payload["api_key"] == "{{VT_API_KEY}}"
    assert payload["x-apikey"] == "{{VT_API_KEY}}"
    assert payload["nested"]["Token"] == "{{VT_API_KEY}}"
    assert payload["benign"] == "keep me"


def test_eventlog_does_not_log_secrets_in_eventlog_file(log_path: Path) -> None:
    log = EventLog(str(log_path))
    secret = "this-is-a-secret-" + "x" * 60
    log.append(
        "tool_scan_started",
        category="tool_scan",
        idempotency_key="h" * 64,
        raw_payload={"api_key": secret, "context": "test"},
    )
    on_disk = log_path.read_text(encoding="utf-8")
    assert secret not in on_disk


def test_eventlog_dedup_hash_is_stable_for_same_payload(log_path: Path) -> None:
    log = EventLog(str(log_path))
    payload = {"a": 1, "b": 2}
    a = log.append(
        "tool_scan_started",
        category="tool_scan",
        idempotency_key="h" * 64,
        raw_payload=payload,
    )
    b = log.append(
        "tool_scan_started",
        category="tool_scan",
        idempotency_key="h" * 64,
        raw_payload=payload,
    )
    # Different event_ids (uuids) but identical payload hashes.
    assert a["hash"] == b["hash"]
    assert a["event_id"] != b["event_id"]


def test_eventlog_rejects_missing_required_inputs(log_path: Path) -> None:
    log = EventLog(str(log_path))
    with pytest.raises(ValueError):
        log.append("", category="x", idempotency_key="k")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        log.append("e", category="x", idempotency_key="")


def test_redact_returns_non_dict_passthrough() -> None:
    assert redact("not a dict") == "not a dict"  # type: ignore[arg-type]
    assert redact(123) == 123  # type: ignore[arg-type]


def test_redact_walks_lists_of_dicts() -> None:
    out = redact(
        {
            "items": [
                {"api_key": "k1", "ok": True},
                "passthrough",
            ]
        }
    )
    assert out["items"][0]["api_key"] == "{{VT_API_KEY}}"
    assert out["items"][0]["ok"] is True
    assert out["items"][1] == "passthrough"
