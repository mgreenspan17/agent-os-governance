# EventLog Governance

## Core Goal

EventLog is the single immutable, append-only source of truth for all meaningful events across systems in the organism.

## EventLog Spine Rule

EventLog is the spine of the organism.

All governance actions must be represented as events, including:
- file creation
- file updates
- decisions
- vetoes
- approvals

## Required Event Alignment Fields

Every event written to EventLog must support and preserve these fields:
- event_type
- category
- source_system
- producer_id
- idempotency_key
- hash
- raw_payload

These fields must be stable enough to support replay, auditing, deduplication, and historical reconstruction.

## Related Governance

- constitution/foundation-governance.md
- constitution/history-governance.md
- constitution/idea-capture-governance.md
- constitution/indexing-governance.md
- constitution/event-governance.md
- constitution/historian-governance.md
- constitution/envelope-governance.md
- constitution/git-hygiene-governance.md
