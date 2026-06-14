# Indexing Governance

## Source Ingestion and Indexing Requirements

The organism must eventually ingest and index all relevant sources, including:

- GitHub repositories,
- Notion workspaces,
- local files,
- AI-generated documents,
- MCP agent profiles,
- governance files,
- tangents,
- schemas,
- prompts,
- policies.

The indexing system must:

- build a map of all governance rules, tangents, schemas, definitions, and ideas,
- detect duplicates and overlaps,
- support queries by topic, artifact, audience, time range, process, and agent.

## Pre-Creation Check (IF EXISTS Rule)

Before creating new governance or tangent artifacts, the system must:

- check the index for existing related concepts,
- avoid duplicating intent,
- reference or extend existing artifacts where appropriate,
- only create new artifacts when the intent is truly new.

This is the intelligence equivalent of SQL IF EXISTS.

## Related Governance

- constitution/idea-capture-governance.md
- constitution/foundation-governance.md
- constitution/intelligence-consolidation-governance.md
- constitution/history-governance.md
- constitution/git-hygiene-governance.md
