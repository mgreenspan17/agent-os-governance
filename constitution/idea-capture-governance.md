# Idea Capture Governance

## Thoughts Must Become Things

The organism must not rely on human memory or AI memory for critical ideas.

Every idea, thought, or concept related to the organism must be:

- captured,
- classified,
- turned into a structural artifact (DNA or tangent),
- tied to the event log.

No idea may exist only in conversation. All ideas must have a structural home.

## Idea Capture Pipeline

For every new idea:

1. Capture:
   - record the idea text,
   - record the context (who, when, where, why).
2. Classify:
   - governance rule,
   - implementation task,
   - schema,
   - visualization,
   - ingestion/indexing,
   - history/query,
   - agent capability.
3. Evaluate:
   - can it be built on the current foundation?
   - if yes -> create or update a governance file and/or active task.
   - if no -> create or update a tangent file with dependencies and trigger conditions.
4. Archive:
   - tie the idea to the organism's DNA,
   - log the idea in the Event DB,
   - ensure it can be referenced later.

## Duplicate Detection and Intent Merging

Before creating a new governance or tangent file, the system must:

- search existing governance and tangents for similar intent,
- avoid duplicating rules or tasks,
- merge overlapping ideas,
- refine existing text where appropriate,
- preserve original meaning.

If a prompt or idea already exists:

- modify or extend it rather than creating a conflicting duplicate.

If the intent is new:

- create a new artifact and tie it to DNA.

## Related Governance

- constitution/foundation-governance.md
- constitution/indexing-governance.md
- constitution/intelligence-consolidation-governance.md
- constitution/eventlog-governance.md
- constitution/envelope-governance.md
