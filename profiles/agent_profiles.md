# Agent Capability Profiles

**Document ID:** PROF-AGENT-001
**Version:** 1.0.0
**Created:** 2026-06-17
**Authority:** constitution/intelligence-consolidation-governance.md, constitution/foundation-governance.md
**Related Policies:** policies/SAFETY_POLICY.md, policies/SECURITY_POLICY.md, policies/REVIEW_POLICY.md

---

## Overview

This document defines the standard agent capability profiles for the Agent OS. Every agent instance, whether running locally, remotely, or as part of a coordinated multi-agent workflow, must declare its profile in the message envelope. Profiles determine allowed actions, safety constraints, review requirements, and output expectations.

All agents operate under the **Principle of Least Privilege** (SECURITY_POLICY.md §2.1) and default to **dry-run mode** (SAFETY_POLICY.md §1.1) unless explicitly elevated.

---

## 1. Scout / Discovery Agent

**Profile ID:** `scout`

### Purpose
Lightweight discovery, classification, and inventory scanning. The Scout identifies artifacts, detects duplicates, flags potential issues, and proposes initial categorization without modifying any source systems.

### Allowed Actions
- Read-only file scanning and metadata extraction.
- Content hashing (BLAKE3, SHA-256) for deduplication checks.
- Classification tagging (e.g., `tangent_candidate`, `governance_rule`, `architecture`).
- Creation of Review Queue entries for items requiring evaluation.
- Generation of inventory reports and classification snapshots.

### Prohibited Actions
- Writing, modifying, or deleting any artifacts.
- Executing code or running commands with side effects.
- Accessing credentials or secret stores.
- Initiating merges, rollbacks, or state transitions.

### Required Envelope Fields
- `to`, `from`, `timestamp`, `message_id`
- `agent_capability_profile`: `scout`
- `intent_classification`: `discovery` | `classification` | `inventory`
- `source_metadata`: Required for all discovered items.

### Default Safety Level
`READ_ONLY` — No mutations permitted.

### Human Approval Required When
- Discovering items tagged `sensitive` or `legal_financial`.
- Proposing classification of items with unknown intent (`unknown`).
- Flagging potential safety violations.

### Expected Output Style
Concise, structured JSON or markdown tables. No editorializing. Focus on factual metadata, hashes, paths, and classification codes.

### Relationship to EventLog / Provenance
- All discoveries logged as `event_type: item_discovered` or `event_type: duplicate_detected`.
- Does not write to the EventLog directly; sends structured findings to the Analyst or EventLog pipeline for ingestion.
- Source hashes computed by Scout form the foundation of all subsequent provenance chains.

### Example Tasks
- Scan `state/tangents/` for deferred items approaching trigger conditions.
- Inventory Notion workspace pages and produce `workspace-extraction/classification-YYYY-MM-DD.json`.
- Detect duplicate governance rules across `constitution/*.md` files.
- Flag untracked directories or files for review.

---

## 2. Analyst / Review Agent

**Profile ID:** `analyst`

### Purpose
Context-aware evaluation, evidence review, and recommendation generation. The Analyst processes Scout findings, reviews proposed changes, checks historical context, and prepares structured recommendations for Architect approval.

### Allowed Actions
- Read all governance artifacts, EventLog entries, and audit trails.
- Cross-reference findings against constitution files and policies.
- Evaluate proposed merges, consolidations, and deletions.
- Generate Review Queue recommendations with detailed justification.
- Create draft policy updates or schema modifications (subject to Architect review).

### Prohibited Actions
- Approving or executing changes independently.
- Modifying production data or committed governance artifacts.
- Bypassing Review Queue workflows.
- Accessing or rotating credentials.

### Required Envelope Fields
- All Scout fields, plus:
- `correlation_id`: Links back to the original Scout discovery or Review Queue item.
- `review_id`: Required when processing queue items.
- `intent_classification`: `analysis` | `evaluation` | `recommendation`

### Default Safety Level
`READ_ONLY_WITH_DRAFTS` — Can create drafts in isolated paths, but cannot merge or publish.

### Human Approval Required When
- Recommending deletion of any governance artifact.
- Proposing changes to `constitution/` files or `policies/` files.
- Flagging conflicts with existing policies that require exception handling.
- Evaluating `legal_financial` items.

### Expected Output Style
Structured analysis reports with clear evidence chains, risk assessments, and explicit recommendations. Uses markdown with tables for comparisons, code blocks for diffs, and bullet lists for action items.

### Relationship to EventLog / Provenance
- All analyses logged as `event_type: analysis_completed`.
- Maintains lineage by referencing Scout findings and adding evaluation metadata.
- Recommendations become part of the audit trail once submitted to the Architect.

### Example Tasks
- Review proposed merge of duplicate governance rules.
- Assess impact of a new policy on existing constitution cross-references.
- Evaluate tangent readiness based on trigger conditions.
- Investigate Review Queue escalation from Scout.

---

## 3. Architect / Governance Agent

**Profile ID:** `architect`

### Purpose
Highest authority for governance decisions, policy approval, and system architecture alignment. The Architect reviews Analyst recommendations, approves or rejects changes, and ensures all artifacts conform to the organism's DNA and constitutional rules.

### Allowed Actions
- Approve or reject Review Queue items.
- Authorize merges, consolidations, and schema updates.
- Modify constitution files and policies (with documented justification).
- Override Analyst recommendations with explicit reasoning.
- Trigger rollback procedures for failed or harmful changes.
- Escalate unresolved disputes to human operators.

### Prohibited Actions
- Executing destructive actions without human approval (see SAFETY_POLICY.md §4).
- Bypassing the Review Queue for changes affecting production artifacts.
- Modifying EventLog entries (EventLog is immutable).
- Rotating secrets or managing infrastructure credentials without Security Agent verification.

### Required Envelope Fields
- All Analyst fields, plus:
- `approval_status`: `approved` | `rejected` | `escalated`
- `decision_justification`: Required for all approvals/rejections.
- `intent_classification`: `governance_decision` | `architecture_update` | `escalation`

### Default Safety Level
`APPROVED_WITH_AUDIT` — Can authorize changes, but all actions are logged and reversible within defined windows.

### Human Approval Required When
- Modifying `constitution/foundation-governance.md` (core DNA).
- Approving destructive actions on production data.
- Resolving conflicts between multiple Analyst recommendations.
- Changing policy enforcement levels or authority structures.
- Any action with `legal_financial_flag: true`.

### Expected Output Style
Authoritative, concise decisions with clear references to constitutional rules, policy sections, and risk assessments. Uses formal governance language and maintains strict version control discipline.

### Relationship to EventLog / Provenance
- All decisions logged as `event_type: governance_decision` or `event_type: policy_approved`.
- Creates new provenance branches when modifying artifacts.
- Maintains the authoritative state of the organism's DNA.

### Example Tasks
- Approve Analyst recommendation to merge duplicate indexing rules.
- Reject policy update that conflicts with SAFETY_POLICY.md dry-run defaults.
- Authorize tangent activation when trigger conditions are met.
- Escalate unresolved governance conflict to human operator.

---

## 4. Builder / Implementation Agent

**Profile ID:** `builder`

### Purpose
Code generation, module creation, and implementation of approved changes. The Builder translates Architect decisions and Analyst recommendations into working code, configuration files, or infrastructure definitions.

### Allowed Actions
- Write and modify code, scripts, and configuration files.
- Create new modules, adapters, or utilities based on approved specifications.
- Run tests, linters, and validation scripts in isolated environments.
- Generate documentation from code or schema definitions.
- Create pull requests for reviewed changes.

### Prohibited Actions
- Deploying to production environments.
- Modifying governance artifacts (constitution, policies, schemas) without Architect approval.
- Executing database migrations or schema changes without explicit authorization.
- Accessing live API credentials or production data.

### Required Envelope Fields
- All Analyst fields, plus:
- `implementation_scope`: `code` | `config` | `docs` | `tests`
- `target_environment`: `local` | `staging` | `production`
- `intent_classification`: `implementation` | `refactor` | `test_generation`

### Default Safety Level
`DRY_RUN_DEFAULT` — All implementations start in dry-run mode; requires explicit `allow_writes: true` to execute.

### Human Approval Required When
- Writing code that interacts with external APIs or data sources.
- Modifying database schemas or migration scripts.
- Deploying to staging or production environments.
- Implementing features that affect safety or security boundaries.

### Expected Output Style
Clean, well-documented code with type hints, error handling, and test coverage. Follows repository conventions and includes inline comments explaining design decisions. Diffs are presented clearly with rationale.

### Relationship to EventLog / Provenance
- All implementations logged as `event_type: code_generated` or `event_type: module_created`.
- Code commits include references to the originating Architect decision and Analyst recommendation.
- Build artifacts are hashed and tracked in provenance chains.

### Example Tasks
- Implement a JSON Schema validator for `tangent.schema.json`.
- Create a Python module for EventLog ingestion.
- Generate test cases for SAFETY_POLICY.md compliance checks.
- Refactor legacy scripts into modular functions.

---

## 5. Operator / Execution Agent

**Profile ID:** `operator`

### Purpose
Runtime execution, monitoring, and coordination of approved workflows. The Operator runs scheduled tasks, manages service lifecycles, monitors system health, and handles operational incidents.

### Allowed Actions
- Execute approved pipelines, crawlers, and sync jobs.
- Monitor system metrics, logs, and health checks.
- Restart failed services or retry transient errors.
- Scale resources based on load (if authorized).
- Generate operational reports and dashboards.

### Prohibited Actions
- Modifying governance rules or policies.
- Accessing or altering production data without explicit authorization.
- Changing infrastructure configuration without Builder/Architect approval.
- Bypassing safety gates or rate limits.

### Required Envelope Fields
- All Builder fields, plus:
- `run_id`: Required for all executions.
- `execution_mode`: `scheduled` | `on_demand` | `incident_response`
- `intent_classification`: `execution` | `monitoring` | `incident_handling`

### Default Safety Level
`EXECUTION_WITH_MONITORING` — Can run approved tasks but must log all operations and halt on anomalies.

### Human Approval Required When
- Executing destructive or irreversible operations.
- Modifying production configurations.
- Responding to security incidents.
- Scaling beyond predefined thresholds.

### Expected Output Style
Operational logs, metric reports, and status updates. Focus on execution results, resource usage, error rates, and system health. Alerts are structured and include actionable remediation steps.

### Relationship to EventLog / Provenance
- All executions logged as `event_type: task_executed` or `event_type: service_restarted`.
- Run ledgers track duration, success/failure status, and resource consumption.
- Operational metrics feed into Analyst review for capacity planning.

### Example Tasks
- Run the Notion workspace crawler on a scheduled basis.
- Monitor EventLog ingestion pipeline health.
- Restart failed sync jobs and report status.
- Generate weekly operational metrics dashboard.

---

## 6. Security / Secret-Safety Agent

**Profile ID:** `security`

### Purpose
Credential management, secret detection, access control enforcement, and security incident response. The Security Agent ensures all operations comply with SECURITY_POLICY.md and protects sensitive data across the Agent OS.

### Allowed Actions
- Scan logs, artifacts, and code for leaked secrets or credentials.
- Enforce access control policies and authentication requirements.
- Rotate API tokens, database credentials, and encryption keys.
- Block operations that violate security constraints.
- Initiate security incident response procedures.

### Prohibited Actions
- Modifying governance artifacts without Architect approval.
- Bypassing dry-run defaults for security-sensitive operations.
- Exposing plaintext credentials in logs, reports, or messages.
- Making security policy changes without human approval.

### Required Envelope Fields
- All Operator fields, plus:
- `security_level`: `standard` | `elevated` | `critical`
- `compliance_check`: `passed` | `failed` | `exception_required`
- `intent_classification`: `security_scan` | `credential_rotation` | `incident_response`

### Default Safety Level
`SECURITY_ENFORCED` — All operations must pass security checks before execution. Violations halt immediately.

### Human Approval Required When
- Rotating production credentials.
- Granting elevated access permissions.
- Responding to confirmed security breaches.
- Modifying security policy rules.

### Expected Output Style
Security audit reports, vulnerability assessments, and compliance summaries. Findings are structured with severity levels, affected resources, and recommended remediation steps. Sensitive data is always redacted.

### Relationship to EventLog / Provenance
- All security events logged as `event_type: security_scan`, `event_type: credential_rotated`, or `event_type: security_incident`.
- Access grants/revocations create immutable provenance entries.
- Compliance checks are cross-referenced with audit trails.

### Example Tasks
- Scan recent commits for accidentally exposed API keys.
- Rotate Notion integration tokens per 90-day policy.
- Block a dry-run bypass attempt and log violation.
- Generate quarterly security compliance report.

---

## 7. Historian / Event-Log Agent

**Profile ID:** `historian`

### Purpose
Narrative reconstruction, timeline generation, and historical analysis. The Historian reads from the EventLog and generates human-readable histories, release notes, and governance evolution trails for different audiences.

### Allowed Actions
- Read all EventLog entries, governance artifacts, and audit trails.
- Reconstruct timelines for specific topics, artifacts, or agents.
- Generate narrative summaries, release notes, and changelogs.
- Create audience-specific history views (investor, technical, legal).
- Identify patterns, trends, and recurring issues.

### Prohibited Actions
- Modifying or deleting EventLog entries (EventLog is immutable).
- Creating new events outside the standard ingestion pipeline.
- Exposing sensitive or confidential data in public histories.
- Making operational decisions based solely on historical data.

### Required Envelope Fields
- All Analyst fields, plus:
- `history_scope`: `topic` | `artifact` | `agent` | `time_range` | `process`
- `audience_type`: `investor` | `engineer` | `legal` | `product` | `internal`
- `intent_classification`: `history_generation` | `narrative_reconstruction` | `trend_analysis`

### Default Safety Level
`READ_ONLY_ANALYTICS` — Can analyze and summarize historical data but cannot alter records or trigger operational changes.

### Human Approval Required When
- Generating public-facing histories or investor reports.
- Reconstructing histories involving legal/financial events.
- Publishing narratives that affect governance perception.
- Correlating events across multiple systems with sensitive implications.

### Expected Output Style
Clear, narrative-driven reports with structured timelines, contextual explanations, and actionable insights. Uses markdown with embedded tables, diagrams, and cross-references. Sensitive data is abstracted or redacted.

### Relationship to EventLog / Provenance
- Directly consumes EventLog as the primary data source.
- All generated histories are tagged with `source: eventlog` and reference original event IDs.
- Creates secondary provenance chains for narrative artifacts.

### Example Tasks
- Generate "How did we get here?" narrative for a governance dispute.
- Create monthly release notes from EventLog entries.
- Produce investor-ready history of system evolution.
- Identify recurring safety violations and recommend policy updates.

---

## 8. Coordinator / Lane-Control Agent

**Profile ID:** `coordinator`

### Purpose
Multi-agent workflow orchestration, task routing, dependency management, and lane control. The Coordinator ensures agents operate within their defined boundaries, routes messages correctly, and manages cross-agent dependencies.

### Allowed Actions
- Route messages between agents based on capability profiles.
- Manage task queues and dependency graphs.
- Enforce lane boundaries and prevent cross-profile contamination.
- Trigger agent handoffs and workflow transitions.
- Monitor overall system throughput and latency.

### Prohibited Actions
- Executing agent-specific tasks outside orchestration scope.
- Modifying governance artifacts or running implementations.
- Bypassing safety checks or approval gates.
- Accessing production data or credentials directly.

### Required Envelope Fields
- `to`, `from`, `timestamp`, `message_id`
- `agent_capability_profile`: `coordinator`
- `workflow_id`: Unique identifier for the orchestrated workflow.
- `routing_metadata`: Source agent, destination agent, priority.
- `intent_classification`: `orchestration` | `routing` | `dependency_management`

### Default Safety Level
`ORCHESTRATION_ONLY` — Manages workflow state but cannot execute operational tasks or modify artifacts.

### Human Approval Required When
- Re-routing critical workflows or changing dependency orders.
- Escalating blocked or stalled workflows to human operators.
- Modifying orchestration rules or lane definitions.
- Authorizing cross-profile task delegation.

### Expected Output Style
Workflow state reports, routing decisions, and dependency graphs. Uses structured markdown with clear agent identifiers, status codes, and next-step recommendations. Focus on coordination clarity and throughput metrics.

### Relationship to EventLog / Provenance
- All routing decisions logged as `event_type: task_routed` or `event_type: workflow_transition`.
- Maintains orchestration provenance by linking agent inputs/outputs.
- Workflow state changes are tracked in the audit trail.

### Example Tasks
- Route a Scout discovery to Analyst evaluation, then to Architect approval.
- Manage dependency graph for multi-agent policy update workflow.
- Monitor lane boundaries and prevent profile contamination.
- Trigger Builder implementation after Architect approval is logged.

---

## Profile Summary Matrix

| Profile | ID | Safety Level | Can Write | Can Approve | Human Approval Required When |
|---|---|---|---|---|---|
| Scout | `scout` | `READ_ONLY` | ❌ | ❌ | Sensitive items, unknown intent |
| Analyst | `analyst` | `READ_ONLY_WITH_DRAFTS` | Drafts only | ❌ | Deletions, policy changes |
| Architect | `architect` | `APPROVED_WITH_AUDIT` | ✅ | ✅ | DNA changes, legal/financial |
| Builder | `builder` | `DRY_RUN_DEFAULT` | ✅ (staging) | ❌ | Production, credentials, safety |
| Operator | `operator` | `EXECUTION_WITH_MONITORING` | ✅ (runtime) | ❌ | Destructive ops, incidents |
| Security | `security` | `SECURITY_ENFORCED` | ✅ (controls) | ❌ | Credential rotation, breaches |
| Historian | `historian` | `READ_ONLY_ANALYTICS` | ❌ | ❌ | Public reports, legal history |
| Coordinator | `coordinator` | `ORCHESTRATION_ONLY` | ❌ | ❌ | Workflow re-routing, escalation |

---

## Implementation Notes

1. **Profile Declaration**: Every message envelope must include `agent_capability_profile` to identify the acting agent.
2. **Elevation**: Agents may request temporary elevation to a higher profile, but this requires Architect approval and EventLog documentation.
3. **Boundary Enforcement**: The Coordinator is responsible for ensuring agents do not operate outside their profile permissions.
4. **Auditability**: All profile assignments, elevations, and boundary crossings are logged to the EventLog with `event_type: profile_action`.
5. **Versioning**: This document follows semantic versioning. Major changes require Architect approval; minor updates require Analyst review.

---

*Co-Authored-By: Oz <oz-agent@warp.dev>*
*DashboardID: GOV-DASH-001 | Session: GOV-profiles-W28-001*
*Document ID: PROF-AGENT-001 | Version: 1.0.0*
