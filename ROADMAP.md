# Agent OS Governance — Security & Infrastructure Roadmap

**DashboardID:** GOV-DASH-001  
**Session:** W35-security-roadmap-001  
**Last Updated:** 2026-06-17T22:30:00Z  

---

## Active Security Items

### SECURITY-GOVERNANCE-001 — Secrets Keeper / Credential Broker Agent

**Status:** PLANNED / NOT IMPLEMENTED  
**Priority:** HIGH  
**Owner:** W35 Lane  
**Created:** 2026-06-17  

#### Purpose
Agents should not receive or retain permanent passwords. Agents should request temporary, scoped, revocable credentials for an approved lane/task. The keeper validates the request, issues limited access, logs usage, and revokes/rotates access after the task.

#### Required Concepts

1. **No permanent credentials in agent prompts.**
2. **No credentials printed in logs or final reports.**
3. **Agents request access using a structured access-request envelope.**
4. **The keeper validates:**
   - Requesting agent
   - Lane ID
   - Approved task
   - Target system
   - Allowed actions
   - Expiration time
   - User approval status
5. **The keeper issues:**
   - Temporary user/password, token, or one-time credential
   - Minimum required permissions only
   - Expiration/revocation metadata
6. **The keeper records:**
   - Who requested access
   - What was issued
   - Scope
   - Start time
   - End time
   - Revocation status
   - Audit notes
7. **The keeper revokes or rotates access when the task is complete.**
8. **Confused agents must stop and ask for lane/task clarification instead of guessing across multiple active lanes.**

#### Postgres Example Architecture
Instead of agents using the permanent `ssot` password, future design should support temporary scoped users such as:

| Role Name | Purpose | Permissions | Expiration |
|---|---|---|---|
| `w35_ingest_temp` | Ingestion tasks | INSERT only on target tables | Task completion |
| `dashboard_readonly` | Dashboard queries | SELECT only | 24 hours |
| `doc_intake_service` | Document intake service | INSERT/UPDATE on intake tables | Service lifetime |
| `admin_rotation_only` | Credential rotation | ALTER ROLE only | Rotation window |

Each role should have least-privilege permissions and explicit expiration/revocation rules.

#### Implementation Notes
- This item requires design of a credential broker service or integration with existing secret management (e.g., HashiCorp Vault, AWS Secrets Manager, or a lightweight local solution).
- Must integrate with the existing governance framework and run ledger for audit trails.
- Should support the `dry_run` and `allow_writes` safety policy defaults.

---

## Pending Manual Items

### POSTGRES-PASSWORD-ROTATION-001 — Rotate Exposed `ssot` Password

**Status:** PENDING / MANUAL CLEANUP  
**Priority:** MEDIUM (blocked by SECRET-GOVERNANCE-001 design decision)  
**Owner:** W35 Lane  
**Created:** 2026-06-17  
**Reference:** `tmp_rotation_note.md`

#### Current Situation
The `ssot` Postgres password was exposed in agent conversation logs and needs rotation. A detailed rotation plan exists in `tmp_rotation_note.md`.

#### Recommendation
**Position:** This rotation should still happen, but the timing depends on the secrets keeper implementation:

- **If Secrets Keeper is implemented soon (within 1-2 weeks):** Wait and rotate as part of the initial secrets keeper setup, creating temporary scoped roles from the start.
- **If Secrets Keeper implementation is delayed:** Proceed with manual rotation now using the plan in `tmp_rotation_note.md`, then transition to the secrets keeper architecture when ready.

#### Immediate Action Required
**YES** — If no secrets keeper is available within the next sprint, the manual rotation should proceed to close the security gap. The exposed password is a known risk.

---

## Version History

| Version | Date | Changes |
|---|---|---|
| 0.1.0 | 2026-06-17 | Initial roadmap — SECURITY-GOVERNANCE-001, POSTGRES-PASSWORD-ROTATION-001 |

---

*Co-Authored-By: Oz <oz-agent@warp.dev>*  
*DashboardID: GOV-DASH-001 | Session: W35-security-roadmap-001*
