# Git Hygiene Governance

## Git Hygiene Rules

The organism must maintain repository hygiene across all local environments.

The Git hygiene system must:
- scan all local repositories (WSL, server, C:)
- detect unpushed commits and branches
- push or archive according to policy
- log each action as an EventLog event

## Trigger Conditions

Git hygiene must run on:
- initial cleanup
- periodic tidying
- after major governance changes

## Related Governance

- constitution/eventlog-governance.md
- constitution/foundation-governance.md
- constitution/indexing-governance.md
- constitution/idea-capture-governance.md
