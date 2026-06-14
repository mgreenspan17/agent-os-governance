# Backup & Replication Governance (DNA Rule)

The Agent OS SSOT (Postgres) must never exist as a single point of failure. 
The system must implement a multi-layered backup and replication strategy 
once the organism reaches Infrastructure Maturity (Stage 3).

Required layers:

1. Local RAID for disk redundancy.
2. Nightly encrypted Postgres dumps to offsite object storage (Backblaze B2).
3. Weekly human-friendly snapshots to Google Drive or OneDrive.
4. Optional: Real-time streaming replication to a low-cost cloud VM.
5. Optional: Permanent archival of encrypted weekly dumps to IPFS/Filecoin.

This is a governance requirement. Implementation is deferred until the 
infrastructure layer is mature enough to support automated backup workflows.

## Related Governance

- constitution/foundation-governance.md
- constitution/event-governance.md
- constitution/indexing-governance.md
- constitution/intelligence-consolidation-governance.md
- constitution/eventlog-governance.md
