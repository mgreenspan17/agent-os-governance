#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BROKER_CONFIG="${BROKER_CONFIG:-${SCRIPT_DIR}/.broker_config}"
MODE="dry-run"
CONFIRM_LIVE="false"
RUN_PREFLIGHT_ONLY="false"
ROLE_PREFIX="cb_test_readonly"
SHORT_ID="$(openssl rand -hex 3 2>/dev/null || date +%s | tail -c 7)"
TEMP_ROLE=""
TEMP_PASSWORD=""
TEMP_CREDENTIAL_FILE=""
ROLE_CREATED="false"
TABLE_FULLY_QUALIFIED=""

if [[ -f "${BROKER_CONFIG}" ]]; then
  # shellcheck disable=SC1090
  source "${BROKER_CONFIG}"
fi

GRANT_DIR="${GRANT_DIR:-${SCRIPT_DIR}/grants}"
AUDIT_LOG="${AUDIT_LOG:-${SCRIPT_DIR}/audit.log}"
LIVE_MODE="${LIVE_MODE:-false}"
DRY_RUN="${DRY_RUN:-true}"
PG_CONTAINER="${PG_CONTAINER:-}"
PG_DATABASE="${PG_DATABASE:-}"
PG_ADMIN_ROLE="${PG_ADMIN_ROLE:-}"
READONLY_SCHEMA="${READONLY_SCHEMA:-public}"
READONLY_TEST_TABLE="${READONLY_TEST_TABLE:-scanner_runs}"

usage() {
  cat <<'EOF'
Credential Broker Lite v0 - Readonly Self-Test Runner

Usage:
  ./self_test_readonly.sh [--dry-run] [--live --confirm-live] [--preflight] [--role-prefix PREFIX] [--help]

Modes:
  --dry-run   Default mode. Prints the full planned test lifecycle without changing anything.
  --live      Enables live role lifecycle test only when all live gates pass.

Safety:
  --confirm-live must be provided with --live.
  LIVE_MODE must be true and DRY_RUN must be false in broker config/environment.
  PG_CONTAINER, PG_DATABASE, and PG_ADMIN_ROLE must be configured.
  READONLY_SCHEMA and READONLY_TEST_TABLE are used for minimal readonly test scope.

Checks:
  --preflight Run non-destructive gate checks only.

Notes:
  - This script never prints passwords or full DB URLs.
  - This script does not read .env files.
  - Live mode is gated and must be executed only in approved server-side lanes.
EOF
}

audit_log() {
  local action="$1"
  local status="$2"
  local role="${3:-none}"
  local note="${4:-none}"
  local ts
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  mkdir -p "$(dirname "${AUDIT_LOG}")"
  touch "${AUDIT_LOG}"
  printf "%s action=%s status=%s role=%s note=%s\n" "${ts}" "${action}" "${status}" "${role}" "${note}" >> "${AUDIT_LOG}"
}

run_psql_admin() {
  local sql="$1"
  docker exec "${PG_CONTAINER}" psql -v ON_ERROR_STOP=1 -U "${PG_ADMIN_ROLE}" -d "${PG_DATABASE}" -c "${sql}"
}

cleanup_live_artifacts() {
  local cleanup_failed="false"

  if [[ -n "${TEMP_CREDENTIAL_FILE}" && -f "${TEMP_CREDENTIAL_FILE}" ]]; then
    rm -f "${TEMP_CREDENTIAL_FILE}" || cleanup_failed="true"
  fi

  if [[ "${ROLE_CREATED}" == "true" && -n "${TEMP_ROLE}" ]]; then
    run_psql_admin "REVOKE ALL PRIVILEGES ON TABLE ${TABLE_FULLY_QUALIFIED} FROM \"${TEMP_ROLE}\";" || cleanup_failed="true"
    run_psql_admin "REVOKE USAGE ON SCHEMA \"${READONLY_SCHEMA}\" FROM \"${TEMP_ROLE}\";" || cleanup_failed="true"
    run_psql_admin "REVOKE CONNECT ON DATABASE \"${PG_DATABASE}\" FROM \"${TEMP_ROLE}\";" || cleanup_failed="true"
    run_psql_admin "DROP ROLE IF EXISTS \"${TEMP_ROLE}\";" || cleanup_failed="true"
  fi

  if [[ "${cleanup_failed}" == "true" ]]; then
    audit_log "SELF_TEST_LIVE_CLEANUP" "FAIL" "${TEMP_ROLE:-none}" "cleanup_error"
  else
    audit_log "SELF_TEST_LIVE_CLEANUP" "PASS" "${TEMP_ROLE:-none}" "cleanup_complete"
  fi
}

preflight_checks() {
  local failed="false"

  echo "=== Credential Broker Readonly Self-Test Preflight ==="

  if command -v docker >/dev/null 2>&1; then
    echo "docker_cli: OK"
  else
    echo "docker_cli: MISSING"
    failed="true"
  fi

  if [[ -n "${PG_CONTAINER}" ]]; then
    if docker ps -a --format '{{.Names}}' | grep -Fx "${PG_CONTAINER}" >/dev/null 2>&1; then
      echo "pg_container: FOUND"
    else
      echo "pg_container: NOT_FOUND"
      failed="true"
    fi
  else
    echo "pg_container: NOT_CONFIGURED"
    failed="true"
  fi

  if [[ -n "${PG_DATABASE}" ]]; then
    echo "pg_database: CONFIGURED"
  else
    echo "pg_database: NOT_CONFIGURED"
    failed="true"
  fi

  if [[ -n "${PG_ADMIN_ROLE}" ]]; then
    echo "pg_admin_role: CONFIGURED"
  else
    echo "pg_admin_role: NOT_CONFIGURED"
    failed="true"
  fi

  if [[ "${LIVE_MODE}" == "true" ]]; then
    echo "live_mode_gate: OPEN"
  else
    echo "live_mode_gate: CLOSED"
  fi

  if [[ "${DRY_RUN}" == "false" ]]; then
    echo "dry_run_gate: OPEN_FOR_LIVE"
  else
    echo "dry_run_gate: CLOSED_FOR_LIVE"
  fi

  mkdir -p "${GRANT_DIR}"
  if [[ -w "${GRANT_DIR}" ]]; then
    echo "grant_dir_writable: YES"
  else
    echo "grant_dir_writable: NO"
    failed="true"
  fi

  mkdir -p "$(dirname "${AUDIT_LOG}")"
  touch "${AUDIT_LOG}"
  if [[ -w "${AUDIT_LOG}" ]]; then
    echo "audit_log_writable: YES"
  else
    echo "audit_log_writable: NO"
    failed="true"
  fi

  if [[ "${failed}" == "true" ]]; then
    return 1
  fi

  return 0
}

validate_live_gates() {
  local failed="false"

  if [[ "${CONFIRM_LIVE}" != "true" ]]; then
    echo "ERROR: --live requires --confirm-live." >&2
    failed="true"
  fi

  if [[ "${LIVE_MODE}" != "true" ]]; then
    echo "ERROR: LIVE_MODE must be true for live mode." >&2
    failed="true"
  fi

  if [[ "${DRY_RUN}" != "false" ]]; then
    echo "ERROR: DRY_RUN must be false for live mode." >&2
    failed="true"
  fi

  if [[ -z "${PG_CONTAINER}" ]]; then
    echo "ERROR: PG_CONTAINER must be configured for live mode." >&2
    failed="true"
  fi

  if [[ -z "${PG_DATABASE}" ]]; then
    echo "ERROR: PG_DATABASE must be configured for live mode." >&2
    failed="true"
  fi

  if [[ -z "${PG_ADMIN_ROLE}" ]]; then
    echo "ERROR: PG_ADMIN_ROLE must be configured for live mode." >&2
    failed="true"
  fi

  if [[ -z "${READONLY_SCHEMA}" || -z "${READONLY_TEST_TABLE}" ]]; then
    echo "ERROR: READONLY_SCHEMA and READONLY_TEST_TABLE must be configured or defaulted." >&2
    failed="true"
  fi

  if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker CLI is required for live mode." >&2
    failed="true"
  fi

  if [[ -n "${PG_CONTAINER}" ]] && ! docker ps -a --format '{{.Names}}' | grep -Fx "${PG_CONTAINER}" >/dev/null 2>&1; then
    echo "ERROR: configured PG_CONTAINER does not exist locally." >&2
    failed="true"
  fi

  if [[ "${failed}" == "true" ]]; then
    return 1
  fi

  return 0
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
    --confirm-live)
      CONFIRM_LIVE="true"
      shift
      ;;
    --preflight)
      RUN_PREFLIGHT_ONLY="true"
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

TEMP_ROLE="${ROLE_PREFIX}_$(date -u +%Y%m%d%H%M%S)_${SHORT_ID}"
TEMP_CREDENTIAL_FILE="${GRANT_DIR}/${TEMP_ROLE}.secret"
TABLE_FULLY_QUALIFIED="\"${READONLY_SCHEMA}\".\"${READONLY_TEST_TABLE}\""

echo "=== Credential Broker Readonly Self-Test ==="
echo "Mode: ${MODE}"

if [[ "${RUN_PREFLIGHT_ONLY}" == "true" ]]; then
  if preflight_checks; then
    audit_log "SELF_TEST_PREFLIGHT" "PASS" "none" "non_destructive"
    echo "preflight result: PASS"
    exit 0
  fi

  audit_log "SELF_TEST_PREFLIGHT" "FAIL" "none" "non_destructive"
  echo "preflight result: FAIL"
  exit 1
fi

if [[ "${MODE}" == "live" ]]; then
  if ! validate_live_gates; then
    audit_log "SELF_TEST_LIVE_GATE" "FAIL" "${TEMP_ROLE}" "gate_validation"
    echo "STOP: live gate validation failed before any database write." >&2
    exit 2
  fi

  trap cleanup_live_artifacts EXIT INT TERM

  mkdir -p "${GRANT_DIR}"
  touch "${AUDIT_LOG}"

  TEMP_PASSWORD="$(openssl rand -hex 24)"

  audit_log "SELF_TEST_LIVE_START" "PASS" "${TEMP_ROLE}" "gates_validated"
  run_psql_admin "CREATE ROLE \"${TEMP_ROLE}\" WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOINHERIT PASSWORD '${TEMP_PASSWORD}';"
  ROLE_CREATED="true"
  audit_log "SELF_TEST_ROLE_CREATE" "PASS" "${TEMP_ROLE}" "temporary_role"

  run_psql_admin "GRANT CONNECT ON DATABASE \"${PG_DATABASE}\" TO \"${TEMP_ROLE}\";"
  run_psql_admin "GRANT USAGE ON SCHEMA \"${READONLY_SCHEMA}\" TO \"${TEMP_ROLE}\";"
  run_psql_admin "GRANT SELECT ON TABLE ${TABLE_FULLY_QUALIFIED} TO \"${TEMP_ROLE}\";"
  audit_log "SELF_TEST_GRANTS" "PASS" "${TEMP_ROLE}" "readonly_grants"

  cat > "${TEMP_CREDENTIAL_FILE}" <<EOF
PG_CONTAINER=${PG_CONTAINER}
PG_DATABASE=${PG_DATABASE}
PG_ROLE=${TEMP_ROLE}
PG_PASSWORD=${TEMP_PASSWORD}
EOF
  chmod 600 "${TEMP_CREDENTIAL_FILE}"

  docker exec -e PGPASSWORD="${TEMP_PASSWORD}" "${PG_CONTAINER}" \
    psql -v ON_ERROR_STOP=1 -U "${TEMP_ROLE}" -d "${PG_DATABASE}" \
    -tAc "SELECT 1 FROM ${TABLE_FULLY_QUALIFIED} LIMIT 1;" >/dev/null
  audit_log "SELF_TEST_SELECT" "PASS" "${TEMP_ROLE}" "readonly_select"

  if docker exec -e PGPASSWORD="${TEMP_PASSWORD}" "${PG_CONTAINER}" \
    psql -v ON_ERROR_STOP=1 -U "${TEMP_ROLE}" -d "${PG_DATABASE}" \
    -c "INSERT INTO ${TABLE_FULLY_QUALIFIED} DEFAULT VALUES;" >/dev/null 2>&1; then
    audit_log "SELF_TEST_INSERT_DENIAL" "FAIL" "${TEMP_ROLE}" "insert_unexpected_success"
    echo "ERROR: INSERT denial check failed (unexpected success)." >&2
    exit 1
  fi
  audit_log "SELF_TEST_INSERT_DENIAL" "PASS" "${TEMP_ROLE}" "insert_blocked"

  if docker exec -e PGPASSWORD="${TEMP_PASSWORD}" "${PG_CONTAINER}" \
    psql -v ON_ERROR_STOP=1 -U "${TEMP_ROLE}" -d "${PG_DATABASE}" \
    -c "CREATE TABLE \"${READONLY_SCHEMA}\".\"${TEMP_ROLE}_deny_probe\" (id integer);" >/dev/null 2>&1; then
    audit_log "SELF_TEST_CREATE_DENIAL" "FAIL" "${TEMP_ROLE}" "create_unexpected_success"
    echo "ERROR: CREATE TABLE denial check failed (unexpected success)." >&2
    exit 1
  fi
  audit_log "SELF_TEST_CREATE_DENIAL" "PASS" "${TEMP_ROLE}" "create_blocked"

  cleanup_live_artifacts
  trap - EXIT INT TERM
  audit_log "SELF_TEST_LIVE_END" "PASS" "${TEMP_ROLE}" "complete"
  echo "live self-test result: PASS"
  echo "cleanup result: temporary role and credential artifacts removed"
  exit 0
fi

echo "planned temporary role name: ${TEMP_ROLE}"
echo "planned grants: CONNECT on database, USAGE on schema public, SELECT on approved readonly tables; NOSUPERUSER always enforced"
echo "planned SELECT test: run SELECT count(*) against readonly target table and expect success"
echo "planned INSERT denial test: run INSERT against readonly target table and expect permission denied"
echo "planned CREATE TABLE denial test: run CREATE TABLE in public schema and expect permission denied"
echo "planned revoke/drop cleanup: REVOKE privileges and DROP ROLE for temporary role"
echo "planned credential-file cleanup: remove temporary credential file ${TEMP_CREDENTIAL_FILE}"
echo "live gates required: --live --confirm-live, LIVE_MODE=true, DRY_RUN=false, PG_CONTAINER, PG_DATABASE, PG_ADMIN_ROLE"

audit_log "SELF_TEST_DRY_RUN" "PASS" "${TEMP_ROLE}" "no_db_write"
echo "dry-run safety: no roles created, no credentials created, no Postgres writes, no deletions performed"
