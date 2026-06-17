# Review Policy

**Policy ID:** POL-REVIEW-001
**Authority Level:** Policy
**Enforcement:** Mandatory
**Version:** 1.0.0
**Created:** 2026-06-14
**Related Constitution:** constitution/history-governance.md, constitution/intelligence-consolidation-governance.md, constitution/eventlog-governance.md

---

## Purpose

This policy defines the review queue workflows, escalation paths, and approval processes for all governance actions, safety violations, and system changes within the Agent OS. It ensures that every meaningful action is reviewed, approved, and tracked before execution.

---

## 1. Review Queue Structure

### 1.1 Required Fields

Every item in the Review Queue must include:

| Field | Type | Description |
|---|---|---|
| `review_id` | string | Unique identifier for this review (UUID7 format). |
| `object_id` | string | Identifier of the object being reviewed (file, event, artifact). |
| `proposed_action` | enum | One of: `keep`, `archive_candidate`, `duplicate_candidate`, `delete_candidate`, `needs_review`, `sensitive`, `legal_financial`, `project_related`, `unknown`. |
| `sensitivity_status` | enum | `public`, `internal`, `sensitive`, `confidential`. |
| `legal_financial_flag` | boolean | True if the object has legal or financial implications. |
| `project_related_flag` | boolean | True if the object is part of an active project. |
| `reason_codes` | array | List of codes explaining why this review was triggered. |
| `evidence_refs` | array | References to supporting evidence (file paths, event IDs, URLs). |
| `reviewer` | string | ID of the human or agent assigned to review. |
| `approval_status` | enum | `pending`, `approved`, `rejected`, `escalated`, `completed`. |
| `executed_at` | datetime | Timestamp when the action was executed (null if pending). |
| `reversible_until` | datetime | Deadline after which the action cannot be rolled back. |

### 1.2 Review Actions

| Action | Description | Reversible |
|---|---|---|
| `keep` | Object is valid and should remain unchanged. | N/A |
| `archive_candidate` | Object should be archived for future reference. | Yes (until archival completes) |
| `duplicate_candidate` | Object duplicates an existing artifact and should be merged. | Yes |
| `delete_candidate` | Object should be permanently deleted. | No (requires human approval) |
| `needs_review` | Object requires human evaluation before any action. | N/A |
| `sensitive` | Object contains sensitive content and needs restricted handling. | Yes |
| `legal_financial` | Object has legal or financial implications requiring expert review. | Yes |
| `project_related` | Object is part of an active project and should be preserved. | N/A |
| `unknown` | Object cannot be classified and requires investigation. | N/A |

---

## 2. Review Workflow

### 2.1 Queue Population

Review Queue items are automatically created when:

- A safety violation is detected (see SAFETY_POLICY.md Section 6).
- A security incident is reported (see SECURITY_POLICY.md Section 5.3).
- A destructive action is requested (see SAFETY_POLICY.md Section 4).
- An intelligence consolidation merge is proposed (see constitution/intelligence-consolidation-governance.md).
- A governance file is modified without following the proper process.

### 2.2 Review Assignment

| Item Type | Assigned To | SLA |
|---|---|---|
| Safety violation | Human operator (Mannie) | Immediate |
| Security incident | Human operator + Security agent | Immediate |
| Destructive action request | Human operator (Mannie) | Within 24 hours |
| Intelligence consolidation merge | Analyst agent → Architect agent → Human (if disputed) | Within 7 days |
| Governance file modification | Architect agent → Human (if disputed) | Within 3 days |
| Unknown classification | Scout agent → Analyst agent → Human (if unresolved) | Within 5 days |

### 2.3 Review Process

1. **Triage** — Scout agent classifies the item and assigns a priority level.
2. **Analysis** — Analyst agent reviews the evidence, checks related governance, and proposes an action.
3. **Approval** — Architect agent approves or rejects the proposed action.
4. **Execution** — If approved, the action is executed and logged to EventLog.
5. **Reversal Window** — A `reversible_until` timestamp is set (default: 7 days from execution).
6. **Closure** — After the reversal window expires, the item is marked `completed`.

### 2.4 Escalation Paths

| Trigger | Escalation Path |
|---|---|
| Safety violation with data loss risk | Scout → Analyst → Architect → Human (immediate) |
| Security breach | Scout → Human (immediate) → Security agent |
| Destructive action without rollback plan | Architect → Human (mandatory approval) |
| Intelligence consolidation dispute | Analyst → Architect → Human (tiebreaker) |
| Governance modification affecting multiple files | Architect → Human (impact assessment required) |
| Unknown classification unresolved after 5 days | Scout → Analyst → Architect → Human |

---

## 3. Approval Gates

### 3.1 Automatic Approval

The following items are **automatically approved** without human intervention:

- `keep` actions on non-sensitive, non-legal objects.
- `archive_candidate` actions with no legal/financial implications.
- `duplicate_candidate` merges where both source and target are verified by Analyst agent.

### 3.2 Human Approval Required

The following items **require explicit human approval**:

- `delete_candidate` actions on any object.
- `sensitive` actions on objects with `sensitivity_status: sensitive` or `confidential`.
- `legal_financial` actions on objects with legal or financial implications.
- Any destructive action (see SAFETY_POLICY.md Section 4).
- Modifications to constitution files.
- Changes to schema definitions.

### 3.3 Approval Documentation

Every human approval must include:

- Approver ID (human operator name or agent ID).
- Timestamp of approval.
- Justification for the decision.
- Any conditions or constraints attached to the approval.
- Reference to the Review Queue item (`review_id`).

All approvals are logged to EventLog with `event_type: review_approved` or `event_type: review_rejected`.

---

## 4. Reversal Procedures

### 4.1 Reversal Window

Every executed action has a `reversible_until` timestamp:

| Action Type | Reversal Window |
|---|---|
| Archive | 7 days |
| Merge (duplicate removal) | 14 days |
| Delete (non-production) | 3 days |
| Delete (production) | Not reversible (must be recreated from backup) |
| Governance modification | 30 days |
| Schema change | 14 days |

### 4.2 Reversal Process

1. **Request** — A reversal request is submitted to the Review Queue.
2. **Assess** — Analyst agent evaluates the impact of reversal.
3. **Approve** — Human operator approves the reversal (mandatory for production deletions).
4. **Execute** — The reversal is performed and logged to EventLog with `event_type: reversal_executed`.
5. **Verify** — Scout agent verifies the system state matches the pre-action state.

---

## 5. Review Metrics and Reporting

### 5.1 Key Metrics

| Metric | Target |
|---|---|
| Average triage time | < 1 hour |
| Average analysis time | < 24 hours |
| Approval rate | > 80% |
| Escalation rate | < 10% |
| Reversal rate | < 5% |
| SLA compliance | > 95% |

### 5.2 Reporting

- Weekly review summary generated and stored in `docs/REVIEW_SUMMARY_YYYY-WXX.md`.
- Monthly metrics dashboard updated and linked to Notion (DashboardID: GOV-DASH-001).
- Quarterly review policy audit to ensure alignment with current governance needs.

---

## 6. Related Policies

- [SAFETY_POLICY.md](SAFETY_POLICY.md) — Safety violation detection and response
- [SECURITY_POLICY.md](SECURITY_POLICY.md) — Security incident escalation
- [DATA_PROVENANCE.md](DATA_PROVENANCE.md) — Source tagging and audit trails

---

## 7. Related Constitution

- constitution/history-governance.md — History Types, reconstructable histories
- constitution/intelligence-consolidation-governance.md — Three-Layer Review Stack
- constitution/eventlog-governance.md — EventLog Spine Rule, Required Event Alignment Fields
- constitution/idea-capture-governance.md — Duplicate Detection and Intent Merging

---

*Co-Authored-By: Oz <oz-agent@warp.dev>*
*DashboardID: GOV-DASH-001 | Session: GOV-phase2-policy-review*
*Policy ID: POL-REVIEW-001 | Version: 1.0.0*
