# Runtime Memory Schemas

**Last Updated:** 2026-04-20
**Summary:** JSON schema references for runtime memory events, candidates, retrieval records, and conflict records, including chunk-aware retrieval metadata.

---

## Files

- `runtime-event.schema.json` — event ingestion contract
- `im-message.schema.json` — cross-agent IM mailbox contract (NDJSON)
- `memory-candidate.schema.json` — candidate queue contract
- `memory-record.schema.json` — normalized retrieval result contract, now including `chunk_id` plus optional section metadata for canonical markdown chunks
- `memory-conflict.schema.json` — conflict candidate contract
