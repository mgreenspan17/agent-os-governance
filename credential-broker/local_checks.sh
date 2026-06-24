#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[check] bash syntax"
bash -n "${SCRIPT_DIR}/broker.sh"
bash -n "${SCRIPT_DIR}/self_test_readonly.sh"

echo "[check] dry-run default"
"${SCRIPT_DIR}/self_test_readonly.sh" --dry-run >/dev/null

echo "[check] dry-run via broker"
"${SCRIPT_DIR}/broker.sh" self-test-readonly --dry-run >/dev/null

echo "[check] live without confirmation must stop"
if "${SCRIPT_DIR}/self_test_readonly.sh" --live >/dev/null 2>&1; then
  echo "FAIL: live mode succeeded without --confirm-live" >&2
  exit 1
fi

echo "[check] live without LIVE_MODE=true must stop"
if LIVE_MODE=false DRY_RUN=false PG_CONTAINER=dummy PG_DATABASE=dummy PG_ADMIN_ROLE=dummy \
  "${SCRIPT_DIR}/self_test_readonly.sh" --live --confirm-live >/dev/null 2>&1; then
  echo "FAIL: live mode succeeded with LIVE_MODE=false" >&2
  exit 1
fi

echo "[check] static guardrails"
if grep -nE 'set -x|echo .*PASSWORD|echo .*PGPASSWORD|printenv|cat .*\.broker_config' "${SCRIPT_DIR}/self_test_readonly.sh" >/dev/null; then
  echo "FAIL: potential secret-output pattern found" >&2
  exit 1
fi

echo "[check] all local checks passed"
