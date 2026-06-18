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

- broker.sh: minimal broker CLI, including self-test-readonly dry-run dispatch.
- self_test_readonly.sh: readonly lifecycle self-test runner, dry-run by default.
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

`--live` exists only as an explicit, separate runtime lane and requires independent approval. This repository implementation step does not execute live mode.

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
