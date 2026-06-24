# Data Provenance Policy

**Policy ID:** POL-PROVENANCE-001
**Authority Level:** Policy
**Enforcement:** Mandatory
**Version:** 1.0.0
**Created:** 2026-06-14
**Related Constitution:** constitution/indexing-governance.md, constitution/eventlog-governance.md, constitution/idea-capture-governance.md

---

## Purpose

This policy defines the data provenance, source tagging, and audit trail requirements for all artifacts within the Agent OS. Every piece of data, document, or governance artifact must be traceable back to its origin, ensuring clear lineage, accountability, and reproducibility.

---

## 1. Source Tagging

### 1.1 Rule

All data artifacts must be tagged with their specific source at the point of ingestion or creation.

### 1.2 Required Source Fields

Every artifact must include a `source_metadata` block with:

| Field | Type | Description |
|---|---|---|
| `source_type` | string | Type of source (e.g., `notion`, `github`, `local_file`, `gdrive`, `database`, `agent_generated`). |
| `source_id` | string | Unique identifier within the source system (e.g., Notion page ID, GitHub commit SHA, file path). |
| `source_url` | string | Direct URL or path to the source artifact. |
| `ingested_at` | datetime | ISO 8601 timestamp when the artifact was ingested or created. |
| `ingested_by` | string | Agent ID or human operator ID who performed the ingestion. |
| `source_hash` | string | BLAKE3 or SHA-256 hash of the source content at ingestion time. |

### 1.3 Source Hashing and Deduplication

- Every ingested artifact must have a content hash computed at ingestion.
- The hash is used to detect duplicates across multiple sources or repeated runs.
- If a duplicate is detected (same `source_hash`):
  - The artifact is **not** re-ingested.
  - A reference is added to the existing artifact's provenance chain.
  - An EventLog entry is created with `event_type: duplicate_detected`.

### 1.4 Source Examples

| Source | `source_type` | `source_id` Example |
|---|---|---|
| Notion page | `notion` | `bd220dd4c12d44cfb2d3b97c2e35148a` |
| GitHub repository | `github` | `mgreenspan17/agent-os-governance` |
| GitHub commit | `github_commit` | `dd2c3d9a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e` |
| Local file | `local_file` | `C:\Users\manni\projects\notion-ingestion-pipeline\src\cli\main.py` |
| Google Drive file | `gdrive` | `1a2b3c4d5e6f7g8h9i0j` |
| Database record | `database` | `notion_index.db:pages:page_123` |
| Agent-generated artifact | `agent_generated` | `GOV-phase2-policy-safety` |

---

## 2. Audit Trails

### 2.1 Rule

All changes to governance artifacts, data stores, and system configurations must be tracked in an immutable audit trail.

### 2.2 Audit Trail Structure

Each audit trail entry must include:

| Field | Type | Description |
|---|---|---|
| `audit_id` | string | Unique identifier for this audit entry (UUID7). |
| `timestamp` | datetime | ISO 8601 timestamp when the change occurred. |
| `actor` | string | Agent ID or human operator ID who made the change. |
| `action` | string | Type of action (e.g., `create`, `update`, `delete`, `merge`, `archive`). |
| `target` | string | Path or identifier of the affected artifact. |
| `before_hash` | string | Hash of the artifact before the change (null for creates). |
| `after_hash` | string | Hash of the artifact after the change (null for deletes). |
| `justification` | string | Reason for the change. |
| `related_event_id` | string | EventLog entry ID corresponding to this change. |
| `reversible` | boolean | Whether this change can be rolled back. |

### 2.3 Storage

- Audit trail entries are stored in the EventLog as immutable records.
- Audit summaries are generated weekly and stored in `docs/AUDIT_SUMMARY_YYYY-WXX.md`.
- Audit data is backed up with the same retention policy as the EventLog.

---

## 3. Data Lineage

### 3.1 Lineage Tracking

All governance artifacts must maintain a clear lineage from their origin to their current state.

### 3.2 Lineage Chain

Each artifact may include a `lineage` field that traces its history:

```json
{
  "lineage": [
    {
      "version": "1.0.0",
      "created_at": "2026-06-14T12:00:00Z",
      "created_by": "Cody",
      "source": "notion",
      "source_id": "bd220dd4c12d44cfb2d3b97c2e35148a",
      "action": "create"
    },
    {
      "version": "1.1.0",
      "updated_at": "2026-06-14T13:00:00Z",
      "updated_by": "Oz",
      "action": "update",
      "justification": "Added cross-references and safety policy links"
    }
  ]
}
```

### 3.3 Lineage Verification

- Periodic lineage audits verify that all artifacts have complete chains.
- Broken lineage chains trigger a Review Queue entry with `proposed_action: needs_review`.
- Lineage gaps must be resolved before the artifact is considered valid.

---

## 4. Retention and Archival

### 4.1 Retention Policy

| Artifact Type | Retention Period | Archival Method |
|---|---|---|
| EventLog entries | Permanent (immutable) | Not applicable |
| Governance artifacts (constitution, policies) | Permanent | Version-controlled backups |
| Classification snapshots | 1 year | Archive to cold storage |
| Audit summaries | 2 years | Archive to cold storage |
| Tangent artifacts | Until implemented or abandoned | Merge or archive |
| Temporary files | 30 days | Automatic deletion |

### 4.2 Archival Process

1. **Identify** — Scout agent flags artifacts approaching retention limit.
2. **Verify** — Analyst agent confirms no active dependencies.
3. **Archive** — Artifacts are compressed, hashed, and stored in archival location.
4. **Log** — EventLog entry created with `event_type: artifact_archived`.
5. **Purge** — Original artifacts are deleted after successful archival verification.

### 4.3 Legal Hold

- Artifacts under legal hold **cannot** be archived or deleted.
- Legal hold is triggered by a human operator with `legal_financial_flag: true`.
- Held artifacts are tagged with `hold_reason` and `hold_expires_at`.
- Legal hold events are logged to EventLog with `event_type: legal_hold_applied` or `event_type: legal_hold_released`.

---

## 5. Cross-Source Consistency

### 5.1 Rule

When the same data exists in multiple sources, the system must ensure consistency across all copies.

### 5.2 Consistency Checks

- Periodic consistency scans compare hashes across sources.
- Inconsistencies trigger a Review Queue entry with `proposed_action: duplicate_candidate`.
- The Analyst agent determines which copy is authoritative.
- Non-authoritative copies are updated or removed based on the resolution.

### 5.3 Conflict Resolution

| Scenario | Resolution |
|---|---|
| Same content, different hashes (encoding change) | Accept both, mark as encoding variant |
| Different content, same source ID | Flag as conflict, create Review Queue entry |
| Deleted in one source, modified in another | Flag as conflict, human review required |
| New artifact in one source, missing in another | Ingest into missing source if appropriate |

---

## 6. Related Policies

- [SAFETY_POLICY.md](SAFETY_POLICY.md) — Content protection, secret redaction
- [SECURITY_POLICY.md](SECURITY_POLICY.md) — Access control, audit and compliance
- [REVIEW_POLICY.md](REVIEW_POLICY.md) — Review queue workflows, escalation paths

---

## 7. Related Constitution

- constitution/indexing-governance.md — Source Ingestion and Indexing Requirements, Pre-Creation Check
- constitution/eventlog-governance.md — EventLog Spine Rule, Required Event Alignment Fields
- constitution/idea-capture-governance.md — Duplicate Detection and Intent Merging
- constitution/history-governance.md — History Requirements, reconstructable from source documents

---

*Co-Authored-By: Oz <oz-agent@warp.dev>*
*DashboardID: GOV-DASH-001 | Session: GOV-phase2-policy-provenance*
*Policy ID: POL-PROVENANCE-001 | Version: 1.0.0*
