# Credential Broker Lite v0

Credential Broker Lite v0 provides a local, auditable pattern for temporary, scoped database access requests. In this phase, it focuses on safe planning and dry-run self-test behavior in repository code.

## Purpose and Security Model

- Issue planning for temporary, least-privilege credentials only.
- Never issue permanent credentials to agents.
- Never issue superuser credentials to agents.
- Never print passwords or full database URLs.
- Keep dry-run as the default path for safety.
- Require separate explicit approval before any live execution lane.

## Why the Readonly Self-Test Runner Exists

PowerShell/SSH nested quoting made remote one-liner role tests fragile and error-prone. The self-test runner is designed so runtime validation can be performed later as a local script on the target node, rather than via remote one-liners.

Remote PowerShell -> SSH -> Bash -> psql one-liner DB role tests are disallowed for live role operations.

For approval-gated live role lifecycle testing, tests must run locally on dev-node1 using the server-side runner.

## Files

- broker.sh: broker CLI with status, preflight, and gated readonly self-test commands.
- self_test_readonly.sh: readonly lifecycle self-test runner with gated live path.
- .broker_config.example: non-secret configuration template.
- grants/.gitkeep: keeps grants directory tracked.

## Dry-Run Usage

Run directly:

```bash
./credential-broker/self_test_readonly.sh --dry-run
```

Run via broker:

```bash
./credential-broker/broker.sh self-test-readonly --dry-run
```

Run preflight checks only (no database writes):

```bash
./credential-broker/broker.sh preflight
```

Dry-run prints the planned temporary role lifecycle only:

1. planned temporary role name
2. planned grants
3. planned SELECT test
4. planned INSERT denial test
5. planned CREATE TABLE denial test
6. planned revoke/drop cleanup
7. planned credential-file cleanup

Dry-run does not create roles, issue credentials, write to Postgres, or delete anything.

## Live Mode

Live mode is implemented but heavily gated and must be run only in an approved server-side lane.

### Required Live Gates

Live mode stops before any database write unless all gates pass:

1. explicit `--live`
2. explicit `--confirm-live`
3. `LIVE_MODE=true`
4. `DRY_RUN=false`
5. configured `PG_CONTAINER`
6. configured `PG_DATABASE`
7. configured `PG_ADMIN_ROLE`
8. configured or defaulted `READONLY_SCHEMA` and `READONLY_TEST_TABLE`

### Live Test Purpose

The live path is designed for one controlled temporary readonly role lifecycle test:

1. create temporary readonly role
2. grant minimal readonly privileges for configured test table
3. verify SELECT works
4. verify INSERT is denied
5. verify CREATE TABLE is denied
6. revoke privileges
7. drop temporary role
8. remove temporary credential file

### No-Secret Output Rules

The scripts intentionally avoid printing:

1. passwords
2. password hashes
3. tokens
4. full database URLs
5. credential file contents

Audit entries are redacted and contain only timestamp, action, status, and temporary role name.

### Expected Server-Side Execution Flow

1. run `./credential-broker/broker.sh preflight`
2. verify all required gates/config values are set
3. run approved live command:

```bash
./credential-broker/broker.sh self-test-readonly --live --confirm-live
```

4. verify cleanup completed and no `.secret` file remains in `credential-broker/grants/`

### Rollback / Stop Conditions

Stop immediately and investigate if any of these occur:

1. any live gate check fails
2. SELECT verification fails
3. INSERT denial check unexpectedly succeeds
4. CREATE TABLE denial check unexpectedly succeeds
5. cleanup step reports failure
6. any credential artifact remains after run

## Future Live Test Verification Checklist

Any future approval-gated live test run must verify all of the following:

1. temporary role created
2. SELECT succeeds
3. INSERT, UPDATE, and DELETE are denied
4. CREATE TABLE is denied
5. permissions revoked
6. role dropped
7. credential file deleted
8. no credential files remain
