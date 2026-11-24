# Program: vt-scan / tests/test_cli_help.py
# Use case: Smoke tests for the Typer CLI surface and vt_client redaction.
#   No network traffic; no real VirusTotal calls.

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from vt_scan.vt_client import (
    VTMissingKeyError,
    VTClient,
    mask_api_key,
    masked_headers,
    resolve_api_key,
)


REPO = Path(__file__).resolve().parent.parent
PKG_PARENT = REPO  # tests/ is sibling of vt_scan/


def _run_cli(*args: str, env: dict | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    full_env = {
        "PATH": __import__("os").environ.get("PATH", ""),
        "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", ""),
        "PYTHONPATH": str(REPO),
    }
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "vt_scan.cli", *args],
        capture_output=True,
        text=True,
        env=full_env,
        cwd=str(cwd or REPO),
    )


def test_cli_help_smoke() -> None:
    res = _run_cli("--help")
    assert res.returncode == 0
    assert "vt-scan" in res.stdout


def test_cli_check_help_smoke() -> None:
    res = _run_cli("check", "--help")
    assert res.returncode == 0
    assert "Dry-run scan" in res.stdout


def test_cli_hash_refuses_traversal(tmp_path: Path) -> None:
    # On Windows os.path.normpath resolves `..` segments, so we may see either
    # "path traversal" or "not a regular file". The contract we enforce is the
    # exit code: the CLI must refuse and surface EXIT_HASH_MISMATCH.
    bad = str(tmp_path / ".." / "nope.bin")
    res = _run_cli("hash", bad)
    assert res.returncode == 2  # EXIT_HASH_MISMATCH
    assert (
        "path traversal" in res.stderr.lower()
        or "not a regular file" in res.stderr.lower()
    )


def test_cli_hash_emits_known_size(tmp_path: Path) -> None:
    p = tmp_path / "hello.bin"
    p.write_bytes(b"x" * 1024)
    res = _run_cli("hash", str(p), "--json")
    assert res.returncode == 0
    assert "1024" in res.stdout
    assert "sha256" in res.stdout


def test_cli_check_is_dry_run_by_default(tmp_path: Path) -> None:
    p = tmp_path / "candidate.bin"
    p.write_bytes(b"some bytes")
    cache = tmp_path / "cache.sqlite"
    log = tmp_path / "eventlog.jsonl"
    res = _run_cli(
        "check",
        str(p),
        "--json",
        "--cache",
        str(cache),
        "--log",
        str(log),
    )
    assert res.returncode == 0, res.stderr
    assert '"dry_run": true' in res.stdout
    assert "would_call_lookup" in res.stdout


def test_cli_key_status_reports_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    # Typer routes the structured payload to stdout, so the test asserts on
    # stdout rather than stderr; the exit code is the canonical signal.
    monkeypatch.delenv("VT_API_KEY", raising=False)
    res = _run_cli("key", "status", "--json")
    assert res.returncode == 5  # EXIT_SECRET
    assert "VT_API_KEY" in res.stdout
    assert '"configured": false' in res.stdout


def test_cli_cache_clear_requires_force(tmp_path: Path) -> None:
    cache = tmp_path / "cache.sqlite"
    res = _run_cli("cache", "clear", "--path", str(cache))
    assert res.returncode == 6  # EXIT_WRITE_REFUSED
    assert "--force" in res.stdout


# vt_client redaction tests (no network)

def test_mask_api_key_keeps_only_tail() -> None:
    masked = mask_api_key("abcd1234efgh5678")
    assert masked.startswith("{{VT_API_KEY}}:")
    assert masked.endswith("5678")


def test_masked_headers_redacts_x_apikey() -> None:
    out = masked_headers({"x-apikey": "abcd1234efgh5678", "Accept": "application/json"})
    assert out["x-apikey"].startswith("{{VT_API_KEY}}:")
    assert out["Accept"] == "application/json"


def test_resolve_api_key_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VT_API_KEY", raising=False)
    with pytest.raises(VTMissingKeyError):
        resolve_api_key()


def test_vt_client_without_key_reports_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VT_API_KEY", raising=False)
    c = VTClient()
    assert c.has_key is False
    assert c.key_id == ""
