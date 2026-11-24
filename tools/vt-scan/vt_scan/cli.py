# Program: vt-scan / cli.py
# Use case: Typer CLI for vt-scan Phase A — `hash` (local only), `check`
#   (dry-run only; never consumes VT quota), `cache stats|clear`, and
#   `key status`. Defaults to dry-run per SAFETY_POLICY §1.1.
# Version history:
#   0.1.0  2026-11-24  Phase A: hash, check (dry-run), cache, key subcommands.

from __future__ import annotations

import datetime as _dt
import json
import os
import sys
import time
from typing import Optional


try:
    import typer
except ImportError:  # pragma: no cover - install hint surfaced in --help
    typer = None  # type: ignore


# Exit codes aligned with the plan. Phase A only emits 0, 2, 4, 5, 6 in
# practice; 3 (dirty) and others are reserved so Phase B can keep the same
# contract for live installs.
EXIT_OK = 0
EXIT_HASH_MISMATCH = 2
EXIT_VERDICT_DIRTY = 3
EXIT_RATE_LIMIT = 4
EXIT_SECRET = 5
EXIT_WRITE_REFUSED = 6


DEFAULT_CACHE_PATH = os.path.expanduser("~/.vt-scan/cache.sqlite")
DEFAULT_LOG_PATH = os.path.expanduser("~/.vt-scan/eventlog.jsonl")
DEFAULT_DIRTY_THRESHOLD = 3  # malicious + suspicious >= threshold => dirty


def _require_typer() -> None:
    if typer is None:
        print(
            "vt-scan CLI requires typer; install with `pip install typer`",
            file=sys.stderr,
        )
        sys.exit(EXIT_WRITE_REFUSED)


def _now() -> float:
    return time.time()


def _verdict_dirty(malicious: int, suspicious: int, threshold: int) -> bool:
    return (malicious + suspicious) >= threshold


def _emit(payload: dict, json_mode: bool) -> None:
    """Emit `payload` either as a pretty JSON object or as `key: value` lines."""
    if json_mode:
        typer.echo(json.dumps(payload, sort_keys=True, indent=2))
        return
    for k, v in payload.items():
        if isinstance(v, (dict, list)):
            typer.echo(f"{k}: {json.dumps(v, sort_keys=True)}")
        else:
            typer.echo(f"{k}: {v}")


# Late-bound subcommands to avoid tying CLI imports to module import success.
app = typer.Typer(help="vt-scan — VirusTotal pre-install scanner (Phase A: dry-run only)")
cache_app = typer.Typer(help="operate the local verdict cache")
key_app = typer.Typer(help="inspect / rotate the VT_API_KEY envelope")
app.add_typer(cache_app, name="cache")
app.add_typer(key_app, name="key")


@app.command("hash")
def cmd_hash(
    path: str = typer.Argument(..., help="local file to hash (sha256/sha1/md5 + size)"),
    json_mode: bool = typer.Option(False, "--json", help="emit a single JSON object"),
) -> None:
    """Compute the SHA-256 / SHA-1 / MD5 hash of a local file. No network."""
    _require_typer()
    from vt_scan.hashing import FileHashError, hash_set

    try:
        hs = hash_set(path)
    except FileHashError as exc:
        if json_mode:
            typer.echo(json.dumps({"path": path, "error": str(exc)}))
        else:
            typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=EXIT_HASH_MISMATCH)
    _emit({"path": path, **hs.to_dict()}, json_mode)


@app.command("check")
def cmd_check(
    path: str = typer.Argument(..., help="local file to scan"),
    upload_if_unknown: bool = typer.Option(
        False, "--upload-if-unknown", help="(Phase B) submit the file if VT has no record"
    ),
    cache: Optional[str] = typer.Option(None, "--cache", help="override cache db path"),
    log: Optional[str] = typer.Option(None, "--log", help="override EventLog path"),
    threshold: int = typer.Option(
        DEFAULT_DIRTY_THRESHOLD, "--threshold", help="malicious+suspicious threshold"
    ),
    json_mode: bool = typer.Option(False, "--json", help="emit a single JSON object"),
) -> None:
    """Dry-run scan: hash + cache lookup + VT verdict preview. No live calls."""
    _require_typer()
    # Local imports so a missing optional dep (typer) does not break rule chain.
    from vt_scan.cache import VerdictCache
    from vt_scan.eventlog import EventLog
    from vt_scan.hashing import FileHashError, hash_set
    from vt_scan.rate_limit import VTRateLimiter
    from vt_scan.vt_client import VTClient

    cache_path = cache or DEFAULT_CACHE_PATH
    log_path = log or DEFAULT_LOG_PATH

    try:
        hs = hash_set(path)
    except FileHashError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(EXIT_HASH_MISMATCH)

    cache_db = VerdictCache(cache_path)
    log = EventLog(log_path)
    rl = VTRateLimiter()
    client = VTClient()

    api_key_status = "configured" if client.has_key else "missing"
    cached = cache_db.get(hs.sha256, _now())
    cache_hit = cached is not None
    verdict_status = "unknown"
    verdict_payload: dict = {}

    log.append(
        "tool_scan_started",
        category="tool_scan",
        idempotency_key=hs.sha256,
        raw_payload={
            "path": path,
            "size_bytes": hs.size_bytes,
            "sha256": hs.sha256,
            "upload_if_unknown": upload_if_unknown,
            "dry_run": True,
        },
    )

    # Phase A: dry-run NEVER consumes VT quota. We deliberately do NOT call
    # `client.lookup_file` here. The preview just summarizes what *would*
    # happen so operators can compare expected vs actual.
    would_call_lookup = not cache_hit
    would_consume_quota = would_call_lookup and client.has_key

    if cached is not None:
        verdict_status = (
            "dirty"
            if _verdict_dirty(cached.malicious, cached.suspicious, threshold)
            else "clean"
        )
        verdict_payload = cached.to_dict()

    log.append(
        "tool_scan_lookup_completed",
        category="tool_scan",
        idempotency_key=hs.sha256,
        raw_payload={
            "sha256": hs.sha256,
            "cache_hit": cache_hit,
            "network_used": False,
            "dry_run": True,
            "api_key_status": api_key_status,
        },
    )
    log.append(
        "tool_scan_verdict_recorded",
        category="tool_scan",
        idempotency_key=hs.sha256,
        raw_payload={
            "sha256": hs.sha256,
            "verdict_status": verdict_status,
            "dry_run": True,
        },
    )

    response = {
        "path": path,
        "size_bytes": hs.size_bytes,
        "hash_set": hs.to_dict(),
        "rate_limit": rl.stats(),
        "api_key_status": api_key_status,
        "cache": {"hit": cache_hit, "stats": cache_db.stats(_now())},
        "dry_run": True,
        "would_call_lookup": would_call_lookup,
        "would_consume_quota_slot": would_consume_quota,
        "verdict_status": verdict_status,
        "verdict": verdict_payload,
        "live_blocked_reason": (
            "Phase A is dry-run only; live mode + uploads land in Phase B"
        ),
    }
    _emit(response, json_mode)


@cache_app.command("stats")
def cmd_cache_stats(
    cache: Optional[str] = typer.Option(None, "--path", help="override cache db path"),
    json_mode: bool = typer.Option(False, "--json", help="emit a single JSON object"),
) -> None:
    """Print the local verdict cache counters."""
    _require_typer()
    from vt_scan.cache import VerdictCache

    cache_path = cache or DEFAULT_CACHE_PATH
    db = VerdictCache(cache_path)
    _emit(db.stats(_now()), json_mode)


@cache_app.command("clear")
def cmd_cache_clear(
    cache: Optional[str] = typer.Option(None, "--path", help="override cache db path"),
    force: bool = typer.Option(
        False,
        "--force",
        help="destructive gate; required to actually delete cached verdicts",
    ),
    json_mode: bool = typer.Option(False, "--json", help="emit a single JSON object"),
) -> None:
    """Wipe the local verdict cache. Requires --force (destructive gate)."""
    _require_typer()

    cache_path = cache or DEFAULT_CACHE_PATH
    if not force:
        preview = {
            "would_remove": "all rows",
            "cache_path": cache_path,
            "destructive_gate": "blocked: pass --force to proceed",
        }
        _emit(preview, json_mode)
        raise typer.Exit(EXIT_WRITE_REFUSED)

    from vt_scan.cache import VerdictCache

    db = VerdictCache(cache_path)
    removed = db.clear()
    _emit(
        {
            "cache_path": cache_path,
            "removed_rows": removed,
            "completed_at": _dt.datetime.utcnow().isoformat() + "Z",  # noqa: DTZ005
        },
        json_mode,
    )


@key_app.command("status")
def cmd_key_status(
    json_mode: bool = typer.Option(False, "--json", help="emit a single JSON object"),
) -> None:
    """Inspect the configured VT_API_KEY. Prints only a masked key id."""
    _require_typer()
    from vt_scan.vt_client import VTMissingKeyError, VTClient

    try:
        client = VTClient()
        _emit(
            {
                "env_var": "VT_API_KEY",
                "configured": client.has_key,
                "key_id": client.key_id if client.has_key else "",
                "public_envelope": {"per_minute": 4, "per_day": 500},
            },
            json_mode,
        )
        if not client.has_key:
            raise typer.Exit(EXIT_SECRET)
    except VTMissingKeyError:
        typer.echo("error: VT_API_KEY is missing or empty", err=True)
        raise typer.Exit(EXIT_SECRET)


if __name__ == "__main__":
    if typer is None:
        print(
            "vt-scan CLI requires typer; install with `pip install typer`",
            file=sys.stderr,
        )
        sys.exit(EXIT_WRITE_REFUSED)
    app()
