#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BROKER_CONFIG="${BROKER_CONFIG:-${SCRIPT_DIR}/.broker_config}"

usage() {
  cat <<'EOF'
Credential Broker Lite v0

Usage:
  ./broker.sh <command> [options]

Commands:
  status                               Show local broker paths and safety defaults
  self-test-readonly [--dry-run]       Run readonly lifecycle self-test planner (dry-run only)
  help                                 Show this help

Security:
  - No password printing
  - No full DB URL printing
  - No .env loading
  - No superuser credential issuance to agents
EOF
}

cmd_status() {
  local grant_dir="${GRANT_DIR:-${SCRIPT_DIR}/grants}"
  local audit_log="${AUDIT_LOG:-${SCRIPT_DIR}/audit.log}"

  echo "=== Credential Broker Lite v0 Status ==="
  echo "Script Directory: ${SCRIPT_DIR}"
  echo "Grant Directory: ${grant_dir}"
  echo "Audit Log: ${audit_log}"
  echo "LIVE_MODE: ${LIVE_MODE:-false}"
  echo "DRY_RUN: ${DRY_RUN:-true}"
}

cmd_self_test_readonly() {
  local mode="--dry-run"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dry-run)
        mode="--dry-run"
        shift
        ;;
      --live)
        echo "ERROR: broker.sh only permits self-test-readonly --dry-run in this lane." >&2
        exit 1
        ;;
      *)
        echo "ERROR: unknown option for self-test-readonly: $1" >&2
        exit 1
        ;;
    esac
  done

  "${SCRIPT_DIR}/self_test_readonly.sh" "${mode}"
}

if [[ -f "${BROKER_CONFIG}" ]]; then
  # shellcheck disable=SC1090
  source "${BROKER_CONFIG}"
fi

case "${1:-help}" in
  status)
    cmd_status
    ;;
  self-test-readonly)
    shift
    cmd_self_test_readonly "$@"
    ;;
  help|--help|-h)
    usage
    ;;
  *)
    echo "ERROR: unknown command: $1" >&2
    usage
    exit 1
    ;;
esac
