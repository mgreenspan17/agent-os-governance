# Envelope Governance

## Mandatory Envelope Fields

All agent-to-agent and agent-to-system messages must include an envelope with:
- to
- from
- timestamp
- message_id (UUID7)
- blake3_hash
- token_count
- completion_time_estimate
- agent_id
- agent_capability_profile
- intent_classification
- correlation_id
- event_id linkage

## Loggability Rule

Every message must be loggable as an EventLog entry.

## EventLog Mapping Rule

Envelope fields must map cleanly to EventLog fields, including:
- producer_id
- correlation_id
- hash
- metadata

## Related Governance

- constitution/eventlog-governance.md
- constitution/event-governance.md
- constitution/foundation-governance.md
- constitution/idea-capture-governance.md
- constitution/indexing-governance.md
