# Safety Policy

**Policy ID:** POL-SAFETY-001
**Authority Level:** Policy
**Enforcement:** Mandatory
**Version:** 1.0.0
**Created:** 2026-06-14
**Related Constitution:** constitution/foundation-governance.md, constitution/eventlog-governance.md, constitution/envelope-governance.md

---

## Purpose

This policy defines the safety constraints that all agents, systems, and workflows must follow when operating within the Agent OS. It ensures that no action causes unintended data loss, no private content is exposed in logs, and all operations respect the organism's DNA principles of staged, coherent growth.

---

## 1. Dry-Run Default

### 1.1 Rule

All operations that modify external systems, data stores, or governance artifacts **must default to dry-run mode**.

### 1.2 Implementation

- `dry_run` parameter defaults to `true` in all adapters, pipelines, and agents.
- A dry-run operation must:
  - Log what **would** be done (create, update, delete, archive).
  - Log the target paths, resource IDs, and expected outcomes.
  - **Not** perform any writes, mutations, or deletions.
  - Return a structured result indicating readiness for execution.
- Dry-run results must be logged to the EventLog with `event_type: dry_run_preview`.

### 1.3 Exceptions

- Read-only operations (discovery, indexing, classification, schema validation) do not require dry-run.
- Emergency rollback procedures may bypass dry-run with explicit approval (see Section 4).

---

## 2. Write Access Control

### 2.1 Rule

`allow_writes` defaults to `false` across all agents and adapters.

### 2.2 Implementation

- Every write operation requires:
  - An explicit `allow_writes: true` flag in the execution context.
  - A valid `run_id` from the Run Ledger.
  - A completed dry-run preview reviewed and approved (or explicitly overridden with documented justification).
- No source adapter may write directly to any data store. All writes must flow through the canonical storage service.
- Write batches must be atomic: either all succeed or all rollback.

### 2.3 Authorization Levels

| Level | Scope | Approval Required |
|---|---|---|
| L1 — Read | Discovery, indexing, classification | None (default) |
| L2 — Dry-Run Write | Preview operations with no mutations | None |
| L3 — Staging Write | Writes to isolated test/staging environments | Agent self-approval with EventLog |
| L4 — Production Write | Writes to production data stores | Human approval + EventLog + rollback plan |
| L5 — Destructive Write | Deletions, archives, schema migrations | Human approval + safety gate + rollback plan + EventLog |

---

## 3. Content Protection

### 3.1 No Private Content Logging

- Agent logs, EventLog entries, and system outputs **must never contain**:
  - Notion page content (except structural metadata like title, ID, parent).
  - Personal identifiers (names, emails, phone numbers).
  - Financial data, legal documents, or sensitive business information.
  - API tokens, keys, passwords, or credentials.

### 3.2 Secret Redaction

- All secrets must be redacted before logging, display, or storage.
- Redaction format: `{{SECRET_NAME}}` (semantic placeholder, not the actual value).
- Secret values must only exist in environment variables or secure credential stores.
- No secrets may be committed to version control under any circumstances.

### 3.3 Sensitive Material Handling

- Files or data tagged with `sensitivity_status: sensitive` must:
  - Not be indexed in full-text search.
  - Not be included in classification snapshots without explicit approval.
  - Be stored with restricted access controls.
  - Be referenced by hash only in public-facing artifacts.

---

## 4. Destructive Action Gates

### 4.1 Rule

Destructive actions (delete, archive, truncate, drop) are **prohibited by default**.

### 4.2 Override Process

A destructive action may only proceed when **all** conditions are met:

1. **Explicit approval** from a human operator (Mannie).
2. **Rollback plan** documented and tested in a staging environment.
3. **EventLog entry** created before execution with:
   - `event_type: destructive_action_approved`
   - Full description of the action and target.
   - Rollback procedure reference.
   - Approval timestamp and approver ID.
4. **Dry-run verification** completed within the last 24 hours.
5. **Backup** of affected data created before execution.

### 4.3 Prohibited Actions

The following actions are **never permitted** without the full override process:

- Deleting Notion pages, databases, or workspace content.
- Dropping database tables, schemas, or indexes.
- Removing git branches with unmerged governance content.
- Purging EventLog entries (EventLog is immutable and append-only).
- Overwriting existing constitution files without creating a backup.

---

## 5. Rate Limiting and Throttling

### 5.1 API Rate Limits

- All external API calls (Notion, GitHub, Google, etc.) must respect rate limits.
- Implement exponential backoff with jitter on 429 responses.
- Maximum retry attempts: 5 before escalation to EventLog.

### 5.2 Batch Size Limits

- `max_items` per batch: 100 (configurable per adapter).
- `page_size` for pagination: 50 (Notion API default).
- `max_depth` for recursive crawling: 10 levels.
- `timeout_seconds` per operation: 300 (5 minutes).

---

## 6. Safety Violation Response

### 6.1 Automatic Detection

- Any operation that violates this policy must:
  - Halt immediately.
  - Log a safety violation event to EventLog with `event_type: safety_violation`.
  - Return a structured error to the orchestrator.
  - Not proceed with any further operations until reviewed.

### 6.2 Review Process

- Safety violations trigger an automatic Review Queue entry.
- The Review Queue item must include:
  - The violating operation details.
  - The specific policy rule violated.
  - The affected resources.
  - Recommended remediation steps.
- A human operator must review and either:
  - Approve the operation with a policy exception (documented).
  - Reject the operation and rollback any partial changes.
  - Update the policy to accommodate the new use case.

---

## 7. Related Policies

- [REVIEW_POLICY.md](REVIEW_POLICY.md) — Review queue workflows and escalation
- [SECURITY_POLICY.md](SECURITY_POLICY.md) — Secrets handling and access controls
- [DATA_PROVENANCE.md](DATA_PROVENANCE.md) — Source tagging and audit trails

---

## 8. Related Constitution

- constitution/foundation-governance.md — Build-on-Current-Architecture Rule
- constitution/eventlog-governance.md — EventLog Spine Rule
- constitution/envelope-governance.md — Loggability Rule
- constitution/idea-capture-governance.md — Duplicate Detection and Intent Merging

---

*Co-Authored-By: Oz <oz-agent@warp.dev>*
*DashboardID: GOV-DASH-001 | Session: GOV-phase2-policy-safety*
*Policy ID: POL-SAFETY-001 | Version: 1.0.0*
