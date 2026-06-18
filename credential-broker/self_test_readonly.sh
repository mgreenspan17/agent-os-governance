#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="dry-run"
ROLE_PREFIX="cb_test_readonly"

usage() {
  cat <<'EOF'
Credential Broker Lite v0 - Readonly Self-Test Runner

Usage:
  ./self_test_readonly.sh [--dry-run] [--live] [--role-prefix PREFIX] [--help]

Modes:
  --dry-run   Default mode. Prints the full planned test lifecycle without changing anything.
  --live      Requires explicit flag and separate operational approval before any runtime use.

Notes:
  - This script never prints passwords or full DB URLs.
  - This script does not read .env files.
  - Live mode is intentionally gated for separate approval in deployment lanes.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      MODE="dry-run"
      shift
      ;;
    --live)
      MODE="live"
      shift
      ;;
    --role-prefix)
      if [[ $# -lt 2 ]]; then
        echo "ERROR: --role-prefix requires a value" >&2
        exit 1
      fi
      ROLE_PREFIX="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

planned_role="${ROLE_PREFIX}_$(date -u +%Y%m%d%H%M%S)"
planned_credential_file="${SCRIPT_DIR}/grants/${planned_role}.secret"

echo "=== Credential Broker Readonly Self-Test ==="
echo "Mode: ${MODE}"

if [[ "${MODE}" == "live" ]]; then
  echo "LIVE mode requested."
  echo "STOP: live execution requires separate explicit approval and is not run in this code lane."
  echo "No database action was performed."
  exit 2
fi

echo "planned temporary role name: ${planned_role}"
echo "planned grants: CONNECT on database, USAGE on schema public, SELECT on approved readonly tables; NOSUPERUSER always enforced"
echo "planned SELECT test: run SELECT count(*) against readonly target table and expect success"
echo "planned INSERT denial test: run INSERT against readonly target table and expect permission denied"
echo "planned CREATE TABLE denial test: run CREATE TABLE in public schema and expect permission denied"
echo "planned revoke/drop cleanup: REVOKE privileges and DROP ROLE for temporary role"
echo "planned credential-file cleanup: remove temporary credential file ${planned_credential_file}"

echo "dry-run safety: no roles created, no credentials created, no Postgres writes, no deletions performed"
