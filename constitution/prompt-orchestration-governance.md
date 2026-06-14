# Prompt Orchestration Governance Rule

## Continuous Execution Principle

If the orchestrator does not require an agent's output to proceed, it must generate the longest, most complete, multi-step prompt possible for that agent, covering all open tasks in the queue that do not depend on external results.

The orchestrator must only pause prompt generation when:

1. A dependency requires reading an agent's output.
2. A branching decision requires interpretation.
3. A safety or governance rule requires human confirmation.

Agents are expected to infer intermediate steps on their own when given sufficient intent. The orchestrator must maximize agent autonomy and minimize unnecessary round-trips.

This rule exists to:
- reduce latency
- increase throughput
- minimize human involvement
- reduce context switching
- maximize concurrency
- allow agents to operate at full capability

## Related Governance

- constitution/foundation-governance.md
- constitution/idea-capture-governance.md
- constitution/event-governance.md
- constitution/envelope-governance.md
