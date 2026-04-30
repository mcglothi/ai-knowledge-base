---
tags: [aikb-memory-core, aikb, memory, extensions, truenas, dockge, sqlite, fastapi, ingestion, search]
hosts: [babbage]
last_updated: 2026-04-22
---

# AIKB Memory Core

**Last Updated:** 2026-04-22
**Summary:** Runtime extension service for AIKB memory workflows. Runs on TrueNAS (Dockge) and provides event ingest, redaction, hybrid retrieval, proposal harvesting, and Observer heartbeat context over episodic logs + AIKB content.

---

## Status

🟢 ACTIVE — deployed on TrueNAS Dockge and reachable at `https://memory.home.timmcg.net`.

---

## Purpose

AIKB remains long-term curated memory in markdown/git.
AIKB Memory Core is the operational memory runtime:

- ingest short-term episodic events (sessions/observer)
- redact sensitive tokens on ingest
- store append-only memory events with audit trail
- expose hybrid retrieval endpoint (event store + AIKB lexical search)
- generate **reviewable proposals** (`fact`, `preference`, `task`, `runbook_update`) from event streams

---

## Architecture (v0.2)

- **Service:** FastAPI (`app.main`)
- **Store:** SQLite + FTS5 (`memory_core.db`)
- **Deployment target:** TrueNAS Dockge stack (host-level, not on turing VM)
- **Canonical source:** `AIKB/_tools/extensions/aikb-memory-core`
- **Legacy cleanup:** Removed the old standalone `~/code/ai-memory-core` checkout on `feynman` after re-importing the service into AIKB.
- **Live build context:** `/mnt/VMs/mcglothi/Code/AIKB/_tools/extensions/aikb-memory-core` on `babbage`

Core endpoints:

- `POST /api/v1/events` — idempotent event ingest by `event_id`
- `GET /api/v1/search?q=...` — hybrid search across ingested events + AIKB via `rg`
- `POST /api/v1/proposals/harvest` — run harvester over new events
- `GET /api/v1/proposals` — list proposals by status/kind
- `GET /api/v1/proposals/{id}` — inspect proposal details
- `PATCH /api/v1/proposals/{id}` — set status (`new`, `approved`, `rejected`, `applied`)
- `POST /api/v1/observer/heartbeat` — low-risk machine context (`repo`, `branch`, `dirty`, `cwd`)
- `GET /api/v1/observer/latest` — latest heartbeat per machine
- `GET /api/v1/stats` — basic counters
- `GET /metrics` — Prometheus metrics
- `GET /health` — health status

---

## Security Boundaries (v0)

- Redaction runs before persistence by default (`MMC_REDACT_BY_DEFAULT=true`)
- AIKB mounted read-only in container (`/aikb:ro`)
- Persistent write path restricted to `/data`
- Optional API key gate (`MMC_API_KEY`) for ingest/search/proposals endpoints

Secrets reference:

- `[Stored in Vaultwarden: PAT/AIKB Memory Core/API Key]`

---

## Dockge Deployment

Compose file lives in the runtime repo:

- `AIKB/_tools/extensions/aikb-memory-core/infra/dockge/compose.yaml`
- Live Dockge stack on TrueNAS now builds from the in-repo extension path instead of a separate `/mnt/VMs/mcglothi/Code/ai-memory-core` checkout.

Expected persistent path on TrueNAS:

- `/mnt/Containers/ai-memory-core/data`

## DNS + NPM

- **FQDN:** `memory.home.timmcg.net`
- **Pi-hole DNS target:** `10.10.10.10` (NPM on TrueNAS)
- **NPM forward target:** `http://10.10.10.10:8077`
- **TLS:** wildcard cert `*.home.timmcg.net` (NPM cert ID 1)
- **NPM proxy host ID:** `38`
- **Auth:** Authentik forward-auth enabled for UI routes; `/health` and `/api/v1/*` bypass forward-auth
- **API security:** `/api/v1/*` requires `X-API-Key` (`MMC_API_KEY`)

## Usage Notes

- Default deployment mode is **centralized runtime on TrueNAS** with local collectors forwarding events.
- AIKB remains authoritative for durable memory; Memory Core stores operational/episodic data.
- Promotion to AIKB remains **human-reviewed** via proposal workflow to reduce memory poisoning risk.
- Proposal review/apply CLI: `AIKB/_tools/memory-pipeline/proposals_cli.py`
- Unified MCP search/proposal tool: `AIKB/_tools/memory-mcp/server.py`

---

## Deployment Notes (2026-03-05)

1. Synced `AIKB/_tools/extensions/aikb-memory-core` to TrueNAS path `/mnt/VMs/mcglothi/Code/ai-memory-core`.
2. Deployed stack via `ansible/ai/deploy_memory_core.yml`.
3. Updated Pi-hole hosts via `ansible/ai/update_pihole_dns.yml` (both primary and secondary).
4. NPM API credentials in Vaultwarden were stale; proxy host was added via DB+conf fallback on TrueNAS and NPM restarted.
5. Enabled Authentik snippet with path-level bypasses:
   - `/health` -> no Authentik challenge
   - `/api/v1/*` -> no Authentik challenge (API key required by app)
6. API key stored in Vaultwarden as `[Stored in Vaultwarden: PAT/AIKB Memory Core/API Key]` and verified against live `/api/v1/stats`.
7. Upgraded sync agent for incremental multi-provider ingest (`codex`, `claude`, `gemini`, ai-hub logs) with:
   - atomic state writes (`memory-sync-state.json`)
   - truncation/rotation handling (offset + inode)
   - retry/backoff and DLQ (`failed-events.jsonl`)
   - collector metrics textfile (`metrics.prom`) for alerting
8. Installed `ai-memory-sync` user timer on:
   - `feynman` (active, ingest verified)
   - `turing` (active, ingest verified)
9. Installed `ai-memory-sync` LaunchAgent on:
   - `tesla` (active, ingest verified on kickstart)
10. Added proposal harvester + review queue APIs and Prometheus metrics endpoint in Memory Core.
11. Added alert-rule template: `AIKB/_tools/extensions/aikb-memory-core/infra/monitoring/prometheus-rules-memory-core.yml`.
12. On 2026-03-07, switched the live Dockge stack to build from `/mnt/VMs/mcglothi/Code/AIKB/_tools/extensions/aikb-memory-core`, rebuilt the container to `aikb-memory-core 0.2.0`, and removed the stale `/mnt/VMs/mcglothi/Code/ai-memory-core` checkout on `babbage`.

## Fresh Context Handoff (2026-03-05)

### Completed in this cycle

1. Memory Core upgraded to **v0.2** runtime shape:
   - proposal queue tables + harvester cursor state
   - proposal APIs (`harvest/list/get/patch`)
   - Prometheus `/metrics` endpoint
2. Human review flow added:
   - `AIKB/_tools/memory-pipeline/proposals_cli.py`
   - supports `harvest`, `list`, `approve`, `reject`, `apply`
   - `apply` now uses preview-first chunk-aware writes via `write_gateway.py`
   - Memory Core harvester now emits richer proposal payloads by default, including `suggested_file`, `suggested_chunk_id`, `apply_mode`, and `proposed_markdown`
   - local adapter layer can still infer missing targeting fields from weaker payloads during preview/apply
3. Unified memory retrieval tool added:
   - `AIKB/_tools/memory-mcp/server.py`
   - tools: `memory_search`, `memory_proposals`, `memory_context`
4. Collector observability improved:
   - `ai-hub` sync agent now emits collector metrics textfile (`metrics.prom`)
   - DLQ count included for alerting
5. Runtime deployment validated:
   - TrueNAS container rebuilt/restarted from updated source
   - `/health`, `/metrics`, proposal harvest + list validated live
6. Memory command center moved into Turing Desktop v2 Memory facet (`ai.home`):
   - proposal list + detail review pane
   - status filter + reload
   - editable summary/payload + review notes
   - approve/reject actions via proxy endpoints
7. Proposal noise cleanup executed:
   - backlog noise auto-rejected in live queue
   - harvester filters hardened for `turn_context` / `session_meta` / local-command-caveat wrappers
8. Observer heartbeat wired into sync agent:
   - `sync_agent.py` now posts `/api/v1/observer/heartbeat` each run
   - verified `observer_machines=3` from `feynman`, `tesla`, and `turing`
9. Queue cleanup pass reduced noisy `new` proposals from 699 to 269 by rejecting obvious assistant-chatter, completion-blurt, and duplicate/misclassified proposals before upstreaming the new harvester logic live.

### Known caveats

1. NPM API credentials in current Vault entries are still failing auth for automation, so `/metrics` bypass update via playbook did not apply yet.
2. Internal endpoint is already usable for scraping: `http://10.10.10.10:8077/metrics`.
3. Proposal queue will need periodic hygiene until semantic ranking/auto-apply safeguards are in place.

### Calibration Note (2026-03-09)

- Ran a live calibration pass from Codex on `tesla` against the Memory Core proposal queue.
- Cleared the remaining 19 `new` proposals to `new=0`.
- Decision pattern: mark facts `applied` only when already canonical in AIKB, reject direct user asks, planning prompts, completion blurts, and unverified duplicate implementation claims from chat backfill.
- Main upstream hygiene gap: proposal generation is still over-capturing prompt/request text and assistant self-reporting from Gemini backfill, often targeting `home-lab/services/aikb-memory-core.md` by default.
- Follow-up hardening landed the same night in the in-repo extension: the harvester now suppresses prompt-style request residue and chat-backfill self-report wrappers before proposal creation.

### Health Repair (2026-04-22)

- Verified Memory Core ingest was fresh for `feynman`; recent KDE/Gemini activity was searchable in event storage even though ai-hub Harvest showed no recent proposal memories.
- Root cause: the default harvester cursor was still processing old March/April backfill in 250-event UI batches. Catch-up advanced the default cursor to `2026-04-13 03:53:21 UTC`.
- Added `ai-memory-harvester.timer` on `feynman` to run the harvester every 15 minutes with `max_events=2000`, using the existing Memory Core API key environment.
- Hardened harvester and hygiene filters for serialized tool-result/chat envelopes, `last-prompt` backfill records, and generic acknowledgements such as `lets do it`; redeployed the live `aikb-memory-core` container from the in-repo extension path.
- Ran live hygiene passes after catch-up; `new` proposals dropped to 88, with remaining items looking more reviewable than the raw envelope/tool-output backlog.
- Fixed `turing` Memory Core reachability by adding persistent `ai-memory-core-host-route.service`, routing `10.10.10.10/32` via `10.10.0.1` because direct on-link ARP for the TrueNAS host failed from `turing`.
- Verified fresh Observer heartbeats from `feynman`, `tesla`, and `turing` via `/api/v1/observer/latest`.
- Updated and restarted live ai-hub operator console on `turing`; Harvest now uses a 2,000-event batch and shows cursor progress in the review flow.

## Next Steps

1. Let the scheduled harvester finish catching the default cursor up to current events, watching `proposals_new` for noise spikes.
2. Fix NPM auth automation and apply `/metrics` proxy bypass for `memory.home`.
3. Wire Prometheus rule file into active monitoring stack:
   - `AIKB/_tools/extensions/aikb-memory-core/infra/monitoring/prometheus-rules-memory-core.yml`
4. Add decision-assist UX in proposal detail:
   - stronger destination guidance + explicit apply flow to AIKB file patch
5. Add optional semantic ranking in proposal generation (local LLM when Mac Studio arrives).
6. Add bounded auto-apply policies for low-risk sections after sufficient confidence history.
7. Add optional LLM review-assist for proposal triage (after local LLM is online):
   - run a model pass on each proposal for `approve/reject`, confidence, and rationale
   - show heuristic + LLM side-by-side in AI Hub Memory proposal detail
   - keep human approval as final gate; no autonomous merge by default

## Tesla Handoff Task (Next Session)

Start from this exact checkpoint:

1. Pull latest `ai-hub` on tesla and switch to the same working branch used for memory UI continuation.
2. Open `https://ai.home.timmcg.net` Memory facet and verify:
   - `Machines = 3`
   - proposal review pane shows recommendation chips and approve/reject labels
3. Implement **Apply to AIKB** flow from approved proposals:
   - preview target file + section
   - show diff before write
   - on confirm: write file, mark proposal `applied`, capture `applied_file`
4. Add keyboard triage shortcuts in Memory facet (`J/K`, `A`, `R`, `S`).
5. Re-run queue hygiene after apply flow lands and document outcome in this file.
