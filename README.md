# Agent OS Governance — DNA v0.1

**DashboardID:** GOV-DASH-001  
**Session:** GOV-init-3607effd  
**Phase:** 1 (Foundation — Scaffold Complete)

This repository contains the foundational governance, schemas, and constitutional rules for the Agent Operating System.

---

## Repository Structure (Verified on GitHub)

| Directory | Purpose | Status |
|---|---|---|
| `constitution/` | Core principles, operating rules, AI coordination contracts | Scaffolded (ready for content) |
| `policies/` | Specific governance policies (safety, security, review, access) | Scaffolded (ready for content) |
| `profiles/` | Role definitions, agent capability profiles, permissions | Scaffolded (ready for content) |
| `prompts/` | Agent prompt templates, instruction sets, behavioral guides | Scaffolded (ready for content) |
| `schemas/` | Canonical object models, edge definitions, data contracts | Scaffolded (ready for content) |
| `sources/` | Source adapter contracts, provenance tracking, integration specs | Scaffolded (ready for content) |
| `state/` | State management rules, lifecycle policies, checkpoint specs | Scaffolded (ready for content) |

All directories contain `.gitkeep` files to preserve structure in Git.

---

## Foundation Contracts (From NIP `docs/FOUNDATION_CONTRACTS.md`)

The following contracts are defined and should be implemented in this governance repo:

### Canonical Object Model
- `object_id`, `source_type`, `source_id`, `external_id`, `object_kind`
- `path_or_url`, `name`, `mime_type`, `size_bytes`
- `content_hash`, `metadata_hash`, `parent_ref`
- `lifecycle_status`, `sensitivity_status`
- `metadata_json`, `first_seen_at`, `last_seen_at`

### Canonical Edge Model
- `edge_id`, `from_object_id`, `to_object_id`
- `edge_type`, `edge_status`, `source_evidence`, `confidence`
- `first_seen_at`, `last_seen_at`, `is_active`
- **Edge types:** `parent_of`, `child_of`, `duplicate_of`, `derived_from`, `references`, `belongs_to_project`, `unresolved_parent_reference`, `source_of`, `produced_by`

### Source Adapter Contract
- Methods: `validate_capabilities()`, `discover()`, `summarize()`, `normalize()`, `detect_changes()`, `redact_for_logs()`
- **Rule:** All adapters must be read-only by default.

### Safety Policy
- `dry_run` default: **true**
- `allow_writes` default: **false**
- `destructive_actions_allowed`: **false** unless explicit approval gate
- No private content logging; secrets must be redacted.

### Run Ledger
- Every run requires: `run_id`, `run_type`, `source_type`, `adapter_name`, `adapter_version`
- Tracking: `params_json`, `status`, `counts_json`, `error_summary_json`
- Timing: `started_at`, `completed_at`, `duration_ms`, `checkpoint_ref`
- Safety flags: `dry_run`, `allow_writes`

### Review Queue
- Fields: `review_id`, `object_id`, `proposed_action`, `sensitivity_status`
- Legal/financial flags, project correlation, evidence refs
- Actions: `keep`, `archive_candidate`, `duplicate_candidate`, `delete_candidate`, `needs_review`, `sensitive`, `legal_financial`, `project_related`, `unknown`

---

## Operating Tracks

| Track | Description |
|---|---|
| **Foundation / Platform** | Shared contracts, FastAPI services, PostgreSQL, run ledger, source adapters, job scheduler, monitoring, backup/restore, agent coordination |
| **Cleanup & Rescue** | Inventory-first cleanup for documents, files, scans, Notion, Drive, databases, local/server folders, duplicates, and review queues |
| **Revenue Workflows** | Tools/workflows that make or save money, including real estate automation, document processing, client intake, and operational systems |
| **Governance & Controls** | AI coordination, approvals, audit trails, safety gates, internal controls, branch/PR discipline, run policies |

---

## Implementation Pause Rule

**Paused until further review:**
- New source adapters
- Broad indexing
- Cleanup automation
- Destructive actions
- Duplicate run/state systems

**Can continue:**
- Docs/specs
- Tests for safety behavior
- Interface scaffolds
- Read-only prototypes
- Policy-gate design

---

## Next Development Steps

### Phase 2 — Populate Governance Content

1. **Constitution** (`constitution/`)
   - [ ] Write `CONSTITUTION.md` with core operating principles
   - [ ] Define AI coordination rules and approval gates
   - [ ] Document governance hierarchy and decision authority

2. **Policies** (`policies/`)
   - [ ] Create `SAFETY_POLICY.md` (dry-run defaults, destructive action gates)
   - [ ] Create `SECURITY_POLICY.md` (secrets handling, access controls)
   - [ ] Create `REVIEW_POLICY.md` (review queue workflows, escalation paths)
   - [ ] Create `DATA_PROVENANCE.md` (source tagging, audit trails)

3. **Schemas** (`schemas/`)
   - [ ] Create `canonical_object.json` (CanonicalObjectModel schema)
   - [ ] Create `canonical_edge.json` (CanonicalEdgeModel schema)
   - [ ] Create `run_ledger.json` (RunLedger schema)
   - [ ] Create `review_queue.json` (ReviewQueue schema)
   - [ ] Create `safety_policy.json` (SafetyPolicy schema)

4. **Sources** (`sources/`)
   - [ ] Create `SOURCE_ADAPTER_CONTRACT.md` (adapter interface spec)
   - [ ] Document existing source adapters (Notion, Drive, local files, databases)
   - [ ] Define provenance tracking format

5. **State** (`state/`)
   - [ ] Create `STATE_MANAGEMENT.md` (lifecycle rules, checkpoint specs)
   - [ ] Define session naming convention (random name + UUID + ID)
   - [ ] Document state transition rules

6. **Profiles** (`profiles/`)
   - [ ] Create `AGENT_PROFILES.md` (role definitions, capabilities)
   - [ ] Define permission matrix per agent type

7. **Prompts** (`prompts/`)
   - [ ] Create `PROMPT_LIBRARY.md` (reusable prompt templates)
   - [ ] Document behavioral guides for each agent role

### Phase 3 — Integration & Validation

- [ ] Implement JSON Schema validation for all schema files
- [ ] Create CI checks that validate constitution/policy compliance
- [ ] Build a governance audit report generator
- [ ] Add integration with Notion for policy/dashboard sync
- [ ] Implement the Implementation Pause Rule enforcement checks

### Phase 4 — Production Readiness

- [ ] Add automated policy compliance testing
- [ ] Create governance dashboard (link to Notion via DashboardID: GOV-DASH-001)
- [ ] Document rollback procedures for all destructive actions
- [ ] Add monitoring and alerting integration
- [ ] Finalize versioning strategy (semantic: major.minor.patch)

---

## Version History

| Version | Date | Changes |
|---|---|---|
| 0.1.0 | 2026-06-14 | Initial scaffold — DNA v0.1, directory structure, README |

---

## License

MIT

---

*Co-Authored-By: Oz <oz-agent@warp.dev>*  
*DashboardID: GOV-DASH-001 | Session: GOV-init-3607effd*
