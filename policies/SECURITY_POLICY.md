# Security Policy

**Policy ID:** POL-SECURITY-001
**Authority Level:** Policy
**Enforcement:** Mandatory
**Version:** 1.0.0
**Created:** 2026-06-14
**Related Constitution:** constitution/foundation-governance.md, constitution/eventlog-governance.md, constitution/envelope-governance.md

---

## Purpose

This policy defines the security constraints for all agents, systems, and workflows operating within the Agent OS. It governs secrets management, access controls, credential handling, and authentication to ensure the integrity and confidentiality of all governance artifacts and data sources.

---

## 1. Secrets Management

### 1.1 Rule

All secrets (API tokens, passwords, keys, credentials) must be managed through secure channels and **never** stored in plaintext within code, configuration files, or governance artifacts.

### 1.2 Storage Requirements

- Secrets must be stored in one of the following:
  - Environment variables (for local development).
  - Cloud secret manager (e.g., AWS Secrets Manager, GCP Secret Manager).
  - Encrypted credential files with restricted file permissions (mode 600 or equivalent).
- Secrets must **never** be stored in:
  - Source code repositories.
  - Governance files (constitution, policies, schemas, tangents).
  - Log files or EventLog entries.
  - Classification snapshots or workspace extraction artifacts.
  - Public-facing documentation or dashboards.

### 1.3 Rotation Policy

- API tokens must be rotated at least every 90 days.
- Credentials must be rotated immediately upon:
  - Suspected compromise.
  - Agent or system decommissioning.
  - Personnel change (human operator leaves or changes role).
- Rotation events must be logged to EventLog with `event_type: secret_rotated`.

### 1.4 Redaction in Logs

- All log output (agent logs, system logs, EventLog entries) must redact secrets using semantic placeholders: `{{SECRET_NAME}}`.
- Redaction must occur **before** the log is written, not after.
- No raw secret values may appear in any log file, console output, or diagnostic artifact.

---

## 2. Access Control

### 2.1 Principle of Least Privilege

- Every agent, adapter, and system must operate with the minimum permissions required to perform its function.
- Read-only access is the default for all data sources.
- Write access requires explicit authorization (see SAFETY_POLICY.md Section 2).

### 2.2 Agent Authentication

- All agents must authenticate before accessing any data source or governance artifact.
- Authentication must use:
  - OAuth 2.0 or equivalent token-based authentication for external APIs.
  - SSH keys or personal access tokens for git operations.
  - Service account credentials for database access.
- Agent credentials must be scoped to the minimum required permissions (e.g., Notion integration with read-only scope).

### 2.3 Human Operator Authentication

- Human operators must authenticate via:
  - MFA-enabled accounts for all external systems.
  - Individual credentials (no shared accounts).
- Operator actions that modify governance artifacts must include:
  - Operator ID in the EventLog entry.
  - Timestamp of the action.
  - Justification for the modification.

### 2.4 Access Revocation

- Access must be revoked immediately when:
  - An agent is decommissioned.
  - A human operator role changes or leaves.
  - A credential is suspected of compromise.
  - A system is migrated or replaced.
- Revocation events must be logged to EventLog with `event_type: access_revoked`.

---

## 3. Credential Scoping

### 3.1 Notion API

- Integration tokens must be scoped to **read-only** unless explicitly required for write operations.
- Workspace access must be limited to specific pages or databases that are part of the ingestion pipeline.
- No access to private or sensitive pages without explicit approval.

### 3.2 GitHub

- Personal access tokens must be scoped to `repo` for the specific repository only.
- No admin or organization-level permissions unless required for repository management.
- Tokens must not have access to other repositories or organizations.

### 3.3 Database Access

- Database credentials must be scoped to specific schemas and tables.
- No `DROP`, `TRUNCATE`, or `ALTER` permissions unless explicitly granted for migration operations.
- Read-only credentials are preferred for all ingestion and indexing operations.

### 3.4 Cloud Storage (GCS, S3, B2)

- Storage credentials must be scoped to specific buckets or containers.
- No public access or anonymous read permissions.
- Encryption at rest must be enabled for all stored data.

---

## 4. Data Encryption

### 4.1 In Transit

- All data transmitted between agents, systems, and external services must use TLS 1.2 or higher.
- No plaintext HTTP connections to any API or data source.
- Certificate pinning is recommended for high-security operations.

### 4.2 At Rest

- All governance artifacts stored in version control are encrypted via git's native mechanisms.
- Sensitive data in classification snapshots must be encrypted or redacted before storage.
- Database backups must be encrypted with AES-256 or equivalent.

### 4.3 Key Management

- Encryption keys must be managed through a dedicated key management service.
- Keys must not be stored in code, configuration files, or governance artifacts.
- Key rotation must follow the same schedule as secret rotation (Section 1.3).

---

## 5. Audit and Compliance

### 5.1 Event Logging

- All security-relevant events must be logged to EventLog:
  - `secret_rotated` — Credential rotation events.
  - `access_granted` — New access permissions assigned.
  - `access_revoked` — Access permissions removed.
  - `security_violation` — Detected security policy violations.
  - `authentication_failure` — Failed authentication attempts.
  - `unauthorized_access_attempt` — Attempts to access restricted resources.

### 5.2 Compliance Review

- Security policies must be reviewed:
  - After any security incident or breach.
  - Quarterly as part of routine governance maintenance.
  - When new agents, systems, or data sources are added.
- Review results must be documented in a security audit report and stored in `docs/SECURITY_AUDIT.md`.

### 5.3 Incident Response

- Security incidents must follow this escalation path:
  1. **Detect** — Automatic monitoring or manual report identifies the incident.
  2. **Contain** — Isolate affected systems and revoke compromised credentials.
  3. **Assess** — Determine scope, impact, and root cause.
  4. **Remediate** — Fix vulnerabilities, restore systems, update policies.
  5. **Review** — Document lessons learned and update this policy.
- All incidents must be logged to EventLog with `event_type: security_incident`.

---

## 6. Related Policies

- [SAFETY_POLICY.md](SAFETY_POLICY.md) — Dry-run defaults, destructive action gates, content protection
- [REVIEW_POLICY.md](REVIEW_POLICY.md) — Review queue workflows and escalation
- [DATA_PROVENANCE.md](DATA_PROVENANCE.md) — Source tagging and audit trails

---

## 7. Related Constitution

- constitution/foundation-governance.md — Build-on-Current-Architecture Rule
- constitution/eventlog-governance.md — EventLog Spine Rule
- constitution/envelope-governance.md — Loggability Rule, EventLog Mapping Rule
- constitution/idea-capture-governance.md — Duplicate Detection and Intent Merging

---

*Co-Authored-By: Oz <oz-agent@warp.dev>*
*DashboardID: GOV-DASH-001 | Session: GOV-phase2-policy-security*
*Policy ID: POL-SECURITY-001 | Version: 1.0.0*
