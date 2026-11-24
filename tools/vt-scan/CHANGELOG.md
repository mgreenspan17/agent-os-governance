# Changelog

All notable changes to `vt-scan` are recorded here. Versioning follows the
semantic-versioning rule (major breaking / minor feature / patch fix).

## 0.1.0 — 2026-11-24 — Phase A

### Added
- `vt_scan.hashing` — `sha256_file`, `hash_set`, path-safety, size cap.
- `vt_scan.rate_limit` — `TokenBucket`, `DayWindow`, combined `VTRateLimiter`
  enforcing 4 req/min and 500 req/day; refuses via `RateLimitExceeded`.
- `vt_scan.cache` — SQLite verdict cache with TTL per source (lookup=30d,
  upload=7d), backed at `~/.vt-scan/cache.sqlite`.
- `vt_scan.vt_client` — `GET /files/{sha256}` wrapper with masked header on
  error and normalized `VTVerdict`. Uploads are stubbed (`NotImplementedError`)
  for Phase B.
- `vt_scan.eventlog` — append-only JSONL writer aligned with the EventLog
  spine fields, with redaction and per-`(tool_install_id, event_type)`
  idempotency.
- `vt_scan.cli` — Typer CLI with `hash`, `check` (dry-run only), `cache
  stats|clear`, `key status`. Exit codes per the plan (0/2/3/4/5/6).
- Pytest suite covering hashing determinism, rate-limit refusal, cache
  TTL, and EventLog redaction/idempotency. No live network calls.

### Notes
- Dry-run only in this iteration. `check` never consumes VT quota even when
  `VT_API_KEY` is set; only the local cache is consulted.
- Secret handling: `VT_API_KEY` is read from env and replaced with the
  `{{VT_API_KEY}}` placeholder before any write to EventLog or Notion row
  previews, per `policies/SECURITY_POLICY.md` §1.4.
