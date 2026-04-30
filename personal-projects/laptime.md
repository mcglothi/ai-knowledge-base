---
tags: [laptime, local-llm, benchmarks, simulator, hardware, affiliate, react, vite]
last_updated: 2026-04-11
---

# LapTime
**Last Updated:** 2026-04-11
**Summary:** Premium local-LLM hardware buying simulator that combines benchmark metrics with an experiential playback UI so buyers can feel how setups behave before purchasing.

## Environment Requirements
- **Platform:** Any machine with Node.js
- **Tools:** Node.js 20+, npm
- **Frontend:** React + Vite

## Overview
- **Objective:** Turn benchmark numbers into a buyer-facing "test drive" for local AI hardware, models, and quantizations.
- **Positioning:** "PCPartPicker meets a local-LLM test drive."
- **Monetization:** Affiliate hardware links, buyer guides, sponsored comparisons, and premium comparison/report features later.
- **Initial Differentiator:** Visualize prompt ingest, time to first token, and streaming response speed instead of only showing benchmark tables.

## Status
- **Repository:** GitHub repo at `mcglothi/laptime`
- **Phase:** 🔨 Active buildout
- **Current Build:** React/Vite app now includes benchmark-backed simulator controls, custom speed/preset tuning, side-by-side comparison, a dedicated model browser, searchable selectors with family filters, color-coded fit-state guardrails, and a segmented playback timeline backed by LocalScore plus community reference entries. The hardware catalog now covers a broader Apple lineup (M2/M3/M4/M5 laptops, minis, and Studios), newer Blackwell consumer GPUs, GB10-class systems such as DGX Spark and partner variants, and an initial AMD Strix Halo batch. Hardware selectors now support platform filtering so the larger catalog stays usable, mobile filter chips now scroll cleanly, explicit form attributes are in place for better accessibility, unfit combinations visibly block the playback area with a stronger memory-bottleneck state, and the site now includes an in-app methodology section that explains how exact benchmark rows, modeled estimates, and community references are separated.
- **Pricing Note:** Hardware price labels are currently hidden in the UI because rapid market swings and memory shortages were making the displayed pricing stale and misleading between deploys.
- **Interaction Upgrades:** Comparison now includes a racing-style lap view where both setups progress down their lanes using the same playback clock, and the simulator now has a context-size slider that scales prompt ingest time while assembling longer realistic prompt samples instead of switching to lorem ipsum filler.
- **Architecture:** Main screen has been split into focused React components so future polish can move faster without keeping all product sections in a single file.
- **Hosting Direction:** Cloudflare Pages is the preferred deployment target for `laptime.run`.
- **Deployment:** Cloudflare Pages project `laptime` is live at `laptime.pages.dev`, with `laptime.run` and `www.laptime.run` attached. GitHub Actions deployment to Cloudflare Pages is now working via Wrangler CI using repository secrets.
- **Domain:** `laptime.run` is live as the primary project domain.
- **README:** GitHub README now points prominently to `https://laptime.run` and is polished for sharing with engineers.
- **Outreach:** First public promotion push started on 2026-03-23 across NVIDIA Developer Forums, Hugging Face community surfaces, Discord communities, and attempted Reddit/Level1Techs posts with account-trust limitations noted.
- **Analytics:** Cloudflare Web Analytics (RUM) is active via the Pages beacon. A reusable helper script now lives at `laptime/scripts/cloudflare-rum-summary.sh` and queries the account-level GraphQL dataset `rumPageloadEventsAdaptiveGroups` filtered by `requestHost: "laptime.run"` and `bot: 0`, which is the correct API surface for referrers and visit counts.
- **Next Data Pass:** On 2026-03-24, follow-up Hugging Face MCP work expanded LapTime's `Mac Studio M3 Ultra 512 GB` source-backed catalog using inferencerlabs MLX cards. In addition to the earlier Qwen3.5 `9B`, `27B`, `35B-A3B`, and `122B-A10B` rows, the app now includes Qwen3.5 `0.8B`, `2B`, and `4B` Apple-silicon runtime rows plus a source-backed `Nemotron 3 Super 120B-A12B` row. These still use published decode throughput from the model cards while prefill and TTFT remain transparently modeled from LapTime's LocalScore-backed baseline. Next step: find Hugging Face-hosted cards or adjacent primary sources that expose direct prompt-throughput / TTFT data or named hardware beyond the current M3 Ultra 512 GB lane.
- **Large-Model Audit Fix:** On 2026-03-26, a public NVIDIA forum correction exposed that LapTime was materially underestimating DGX Spark performance for `GPT OSS 120B`. Root cause: the app was still treating GPT OSS like a generic dense `Q4` estimate instead of an `MXFP4` MoE-style runtime with a much smaller active-parameter footprint. The fix updated `GPT OSS 20B/120B` to use `MXFP4` labels plus active-parameter scaling, added a labeled `community-runtime` playback row for `DGX Spark + GPT OSS 120B` based on the NVIDIA Developer Forums `vLLM` post, and expanded the methodology UI so community runtime rows are separated from exact benchmarks, source-backed model-card rows, and pure estimates.
- **Benchmark Evaluation (2026-03-26):** The first formal product benchmark is recorded at `_runtime/benchmarks/laptime-2026-03-26.md`. Bottom line: LapTime currently leads on buyer-facing UX, TTFT/prompt-ingest framing, and methodology transparency, but the hard-coded `benchmarkData.js` catalog is now the main scaling risk. Recommended next step is to pivot from manually broadening static rows toward dynamic calculation, shareable comparison URLs, and bring-your-own-model ingestion from Hugging Face metadata.
- **Audit Direction:** The highest-risk rows are now the remaining large models whose behavior still depends on sparse architectures, backend-specific quants, or incomplete runtime evidence. In practice that means continuing to review Kimi, Nemotron, and any future MoE entries before trusting generic size-based extrapolation.
- **User Ingestion Exploration:** On 2026-03-24, explored strategies for ingesting user-submitted benchmark data. Identified four primary paths: "Verified by WebLLM" (in-browser benchmarking via WebGPU), a structured "Add a Lap" form (using Cloudflare Workers + D1), a "Benchmark Log Parser" for power-user CLI output, and a community-driven Google Sheet/CSV sync for low-infrastructure scaling.
- **Submission Review Utility:** AIKB now includes `_tools/laptime/review_submissions.py`, a GitHub-issue reviewer that pulls LapTime submission issues, parses the raw benchmark log, matches candidate hardware/model rows against the live LapTime catalog, checks structured fields for consistency, and emits both conservative `PASS` / `REVIEW` / `FAIL` guidance and promotion-ready JSON payloads for human-approved rows.
- **House Benchmark Bridge (2026-04-04):** Added an initial internal bridge design for feeding Hopper, and later Newton, benchmark results back into LapTime without auto-writing the public catalog. New repo assets: `laptime/docs/house-benchmark-bridge.md` documents the proposed normalized JSON artifact plus promotion rules, and `laptime/scripts/review-house-benchmark.mjs` compares a normalized house benchmark candidate against the live `benchmarkData.js` catalog to flag new-row opportunities, runtime divergences, and fit contradictions. This is specifically meant to catch cases like "modeled GB10 fit looked fine, but the real Hopper backend path was not a safe verified fit."
- **Open WebUI Extension API (2026-04-04):** LapTime now has an initial API-oriented integration path for a lightweight Open WebUI extension instead of a hard fork. New repo assets: `laptime/functions/api/runtime-telemetry.js`, `laptime/src/lib/runtimeTelemetry.js`, and `laptime/docs/open-webui-extension-api.md`. The endpoint resolves a hardware/model selection into LapTime-estimated prefill, decode, TTFT, coverage tier, and fit status, and it can also accept observed decode/TTFT numbers so the extension can show a compact "estimated vs live" comparison. Current Hopper aliasing resolves `hopper` to the GB10 / DGX Spark class. Model alias coverage is still strongest for models already present in LapTime's catalog; non-catalog Open WebUI aliases currently return suggestions rather than pretending to have a precise match.
- **Extension Scaffold Follow-up (2026-04-04):** Added `laptime/docs/open-webui-extension-snippet.js` as a minimal fetch-and-render example for an Open WebUI-side badge/card, plus explicit Hopper demo-model aliasing in `runtimeTelemetry.js` so names like `qwen3.5:122b-a10b`, `gpt-oss:120b`, `gemma3:27b`, `Qwen MoE 30B`, and `Qwen Coder 30B` can map to reasonable LapTime rows instead of relying purely on fuzzy matching. The strongest current path is still exact matches for models already in LapTime; alias-based mappings should be treated as intentional approximations and expanded as the catalog grows.
- **Hopper Overlay Deployment (2026-04-04):** Built and deployed the first Hopper-side Open WebUI overlay hook. Repo assets now include `laptime/integrations/open-webui/laptime-telemetry-overlay.js` and `laptime/scripts/deploy-hopper-openwebui-overlay.sh`. The overlay is injected by a single script tag in Hopper's packaged `frontend/index.html`, served from `open_webui/frontend/static`, and calls `https://laptime.run/api/runtime-telemetry` with `hardwareName=hopper`. It stays hidden until a model is detected, then shows a compact LapTime estimate card with fit status plus optional live TTFT/decode deltas inferred from streamed chat responses. Deployment note: Cloudflare Pages Functions worked without an explicit `--functions` flag in the current Wrangler/GitHub Action stack; adding that flag caused deploy failures under `wrangler-action@v3`.
- **UI/UX Rethink (2026-04-11):** Replaced the single long-scroll page with a 3-route SPA using client-side routing (no library — pushState + popstate). Routes: `/` (Simulate — primary tool, unchanged functionally), `/race` (Comparison + Submission together), `/reference` (Catalog + Methodology + Source Explorer). A persistent site nav bar sits below the masthead with active-tab underline. Reference page catalog cards now have a "Simulate →" button that loads the model and jumps to `/`. Race page "Model / Track" card is now an interactive search+select picker. Share URLs updated to use page paths instead of fragment hashes. Deployed to `laptime.run` via Cloudflare Pages (commit `157f393`).

## Near-Term Roadmap
- [x] Pick product name and brand direction (`LapTime`)
- [x] Create initial web app scaffold
- [x] Build first-pass landing page and playback simulator shell
- [x] Add LocalScore-backed seed metrics and custom workload/speed controls
- [x] Add side-by-side comparison and interactive source explorer
- [x] Split the main app into smaller React sections for cleaner iteration
- [x] Choose Cloudflare Pages as the initial hosting path for `laptime.run`
- [ ] Replace synthetic metrics with real benchmark ingestion
- [ ] Add a Hopper/Newton house-benchmark bridge so private calibrated runs can review and correct LapTime rows before public promotion
- [x] Use the Hugging Face MCP in the next Codex session to collect hardware-specific Qwen3.5 runtime benchmarks and upgrade the current footprint-based estimates
- [ ] Expand source-backed Qwen3.5 runtime coverage beyond the current M3 Ultra 512 GB pass and replace modeled prefill/TTFT where direct measurements exist
- [ ] Add shareable comparison URLs and stronger dynamic fit math before broadening the static catalog further
- [ ] Add bring-your-own-model simulation from Hugging Face config metadata so unlisted models do not require manual catalog edits first
- [ ] Create benchmark explorer and hardware landing pages
- [ ] Expand attribution, methodology, and source pages beyond the current in-app trust section
- [ ] Explore a stronger racing-style comparison visualization, context-size slider, and possible WebLLM "run your own lap" benchmark mode
