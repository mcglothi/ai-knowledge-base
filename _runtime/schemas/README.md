# Runtime Memory Schemas

**Last Updated:** 2026-03-07
**Summary:** JSON schema references for runtime memory events, candidates, retrieval records, and conflict records, including chunk-aware retrieval metadata.

---

## Files

- `runtime-event.schema.json` — event ingestion contract
- `memory-candidate.schema.json` — candidate queue contract
- `memory-record.schema.json` — normalized retrieval result contract, now including `chunk_id` plus optional section metadata for canonical markdown chunks
- `memory-conflict.schema.json` — conflict candidate contract
