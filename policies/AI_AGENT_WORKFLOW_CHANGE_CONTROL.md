# AI Agent Workflow Change Control

**Effective date:** 2026-10-19  
**Status:** Proposed in pull request; human review required before merge.

## Purpose

Provide durable controls for changes in AI coding-agent models, agent modes, integrations, permissions, and event sources. This policy supplements the existing routing and approval rules; it does not replace the routing SSOT or profile handshake.

## Routing baseline

Keep the current division of responsibility unless a tested change is explicitly approved:

- **Codex/Cody:** repository implementation, code edits, tests, documentation, commits, and pull-request preparation.
- **Warp:** SSH/WSL, server operations, deployment, runtime verification, and terminal workflows.
- **Notion:** human-facing summaries, task tracking, and project memory; not a direct execution target.

A feature announcement or new model does not, by itself, justify changing this routing.

## Model and provider change control

1. Keep model/provider aliases in a versioned routing map. Prompts should name the required capability and task class before naming a specific model ID.
2. When a model is announced, renamed, deprecated, or access-restricted, verify the actual account, plan, region, client version, and rollout state before changing routing.
3. Do not auto-migrate on announcement alone. Update the routing map only after a smoke test covering representative code, tool use, latency/cost expectations, and failure behavior.
4. If a selected model or policy is unavailable, fail clearly and route to an approved fallback; do not silently substitute a higher-risk or more expensive model.

## Execution, policy freshness, and autonomy

1. Verify the active profile and current policy before autonomous execution. If policy freshness or managed-settings confirmation fails, block execution and report the reason.
2. Use explicit terminal states: `blocked`, `failed`, or `complete`. Do not indefinitely retry when the agent requires user input, credentials, approval, or a missing integration.
3. Agents may not enable credits, budgets, billing, security policies, credentials, or merge/production permissions. Those actions require explicit human authorization.
4. Generated commits and pull requests require human review before merge. Keep destructive operations and production changes behind the existing approval profiles.

## GitHub, credentials, and MCP

1. Prefer least-privilege GitHub Apps or narrow tokens over broad personal tokens. Grant only the repository and permission scope required by the workflow.
2. Do not place credentials, tokens, private keys, or sensitive repository content in prompts, logs, issue comments, or generated artifacts.
3. Treat MCP access as explicit: verify which server, account, scopes, and tools are active before execution. A local model or local terminal does not imply offline or credential-free execution.
4. Record the credential source and effective permission scope when adding or changing an integration.

## Event-source reliability

Do not depend on GitHub repository push-event email notifications for automation. Use GitHub Actions, webhooks, or an owned mail relay and test delivery/duplicate handling. Audit connected Gmail/n8n workflows before removing any legacy dependency.

## Verification checklist

Before adopting a consequential platform change:

- Search governed repositories and settings for deprecated or unavailable model IDs.
- Verify the active Codex/Warp client, model catalog, reasoning controls, permissions, and managed settings.
- Test private-repository access, MCP OAuth/scopes, and unattended-run behavior in a non-critical repository.
- Check GitHub budgets, credits, secret-scanning/push-protection status, and Actions/webhook delivery.
- Record evidence, decision, owner, and rollback path in the event log and Notion review page.

## Current decision

The current Codex/Cody-versus-Warp routing remains unchanged. The 2026-10-19 audit found no deprecated `gpt-5.5`, `gpt-5.6-terra`, `claude-opus-4.8`, or `claude-opus-5` references in the sampled governed repositories. GitHub push-email dependency was not found in repository source; connected Gmail/n8n workflows require a separate account-level audit.

## Primary evidence

- [GitHub: Copilot model deprecations](https://github.blog/changelog/2026-10-15-upcoming-deprecation-of-selected-github-copilot-models-in-mid-november/)
- [GitHub: AI Scan for pull requests GA](https://github.blog/changelog/2026-10-15-ai-scan-for-pull-requests-generally-available/)
- [GitHub: Agentic Autofix GA](https://github.blog/changelog/2026-10-15-agentic-autofix-for-code-scanning-alerts-general-availability/)
- [GitHub: managed settings enforcement](https://github.blog/changelog/2026-10-13-enterprise-managed-settings-enforcement-updates/)
- [GitHub: least-privilege GitHub Apps](https://github.blog/changelog/2026-10-13-github-app-improvements-for-least-privilege-and-management/)
- [GitHub: push-event email retirement](https://github.blog/changelog/2026-10-15-email-notifications-for-repository-push-events-have-been-retired)
- [Warp changelog](https://docs.warp.dev/changelog/2026/)
