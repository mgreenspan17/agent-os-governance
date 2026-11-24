# vt-scan

VirusTotal-backed pre-install scanner for binaries and tools. Aligns with:

- `policies/SECURITY_POLICY.md` — secret management and rotation
- `policies/SAFETY_POLICY.md` — dry-run default, rate limits, destructive gates
- `policies/DATA_PROVENANCE.md` — source tagging and audit trails
- `constitution/eventlog-governance.md` — immutable EventLog spine

## Phase A scope (this iteration)

- Local SHA-256/SHA-1/MD5 hashing with streaming I/O.
- Path-safety guard against traversal and symlinks.
- Size cap (200 MiB by default — matches the VT public API cap).
- Token-bucket rate limiter (4 req/min, 500 req/day) that refuses rather than drops.
- SQLite verdict cache with differentiated TTL (30 days for hash-only lookups, 7 days for upload verdicts).
- VirusTotal client wrapper: `GET /files/{sha256}` only; uploads are stubbed for Phase B.
- Append-only JSONL EventLog writer with secret redaction and idempotent keying.
- Typer CLI exposing `hash`, `check` (dry-run only), `cache stats`, `cache clear`, `key status`.
- Pytest suite using mocked VT responses — no real network calls in CI.

## Phase B (deferred)

- Live mode for `vt-scan check` behind `--live` + `allow_writes=true`.
- `POST /files` upload + `GET /analyses/{id}` polling.
- Notion "Tools" row writer.
- `vt-scan cache warm <paths…>` and `vt-scan replay <tool_install_id>`.
- `vt-scan key rotate` with 80-day reminder / 95-day hard block.

## Quick start

```bash
pip install -r tools/vt-scan/requirements.txt
export VT_API_KEY=<your_key>

# hash only, no network
python -m vt_scan.cli hash ./some-tool.exe

# dry-run check (Phase A never consumes quota even if VT_API_KEY is set)
python -m vt_scan.cli check ./some-tool.exe --json

# cache stats / clear
python -m vt_scan.cli cache stats
python -m vt_scan.cli cache clear --force  # requires --force

# inspect configured key (prints masked id only)
python -m vt_scan.cli key status
```

## Exit codes (Phase A)

| code | meaning                                            |
| ---- | -------------------------------------------------- |
| 0    | clean verdict or dry-run preview succeeded         |
| 2    | hash error (path traversal, symlink, oversize)     |
| 3    | verdict dirty — install refused                    |
| 4    | rate-limit envelope exhausted                      |
| 5    | secret missing or stale                            |
| 6    | write refused (live mode without `allow_writes`)   |

## Layout

```
tools/vt-scan/
├── README.md
├── CHANGELOG.md
├── requirements.txt
├── vt_scan/
│   ├── __init__.py
│   ├── hashing.py
│   ├── rate_limit.py
│   ├── cache.py
│   ├── vt_client.py
│   ├── eventlog.py
│   └── cli.py
└── tests/
    ├── test_hashing.py
    ├── test_rate_limit.py
    ├── test_cache.py
    ├── test_eventlog.py
    └── test_cli_help.py
```
