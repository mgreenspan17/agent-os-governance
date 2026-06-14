# Event Governance

## Event Monitor Requirements

The system must maintain a real-time event monitor that records every action, change, decision, and update across all agents, systems, pipelines, and repositories. All events must be normalized into a shared schema and written into the Event DB, which serves as the chronological SSOT for “what happened.”

Each event must include:
- id
- timestamp
- actor (agent, human, or system)
- system (orchestrator, Cody, Warp, Postgres, pipeline, etc.)
- type (file_change, governance_update, prompt_sent, task_completed, etc.)
- context (repo, path, branch, process, project)
- payload (structured details)
- links (parent event, related events, process id, task id)

The event monitor must never editorialize. It records facts only.

## Historian Agent Requirements

The Historian agent must read from the Event DB and generate narrative explanations, timelines, and “how did we get here” answers. It must be able to produce:

- per-path histories
- per-agent histories
- per-process histories
- per-project histories
- organism-wide timelines
- narrative summaries
- release notes and changelogs

The Historian must be able to reconstruct any path through the event graph on demand.

---

## Related Governance

- constitution/eventlog-governance.md
- constitution/historian-governance.md
- constitution/history-governance.md
- constitution/foundation-governance.md
- constitution/idea-capture-governance.md
