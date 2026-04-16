# Tools

Optional tools that extend AIKB capabilities. None are required for basic use.

---

## Intelligence Tools

Optional scripts to automate the retrieval and structuring of your AI Knowledge Base:

- **Ambient Context Injection** (`_tools/memory-pipeline/ambient_ask.sh`) — A wrapper for your AI CLI that automatically injects relevant facts from your AIKB into your prompt *before* the agent starts.
- **Temporal Knowledge Graph** (`_tools/memory-pipeline/build_temporal_graph.py`) — Generates a structured JSON graph of your knowledge, extracting entities like IPs and tools to track how they change over time.
- **Semantic Search** (`_tools/memory-pipeline/memory_search.py`) — A hybrid keyword/semantic search tool to quickly locate specific memories across your entire repository.

---

## tutorial — Onboarding orientation

A 4-minute, paginated terminal tutorial for anyone new to AI in the terminal. Covers the mental model shifts that matter: tool calls, approvals, AIKB memory, short prompts, and what to do when something goes wrong.

Offered automatically at the end of `install.sh`. Can also be run any time:
```bash
bash _tools/tutorial.sh
```

---

## feature-tour — Guided walkthrough of the AIKB power layer

A paginated terminal walkthrough for people who already understand the basics but want to learn how to get real leverage from AIKB as it grows.

Covers:
- the operator loop (`hud`, `focus set`, `closeout`)
- approvals as a trust surface
- operator intents for shorthand workflows
- semantic search as the first high-value addon
- a realistic first-week adoption sequence

Run it any time:
```bash
bash _tools/feature-tour.sh
```

---

## aikb-search — Semantic search MCP server

Adds an `aikb_search` tool to Claude Code (and other MCP clients) that lets agents query your AIKB with natural language instead of keyword grep.

**What it enables:**
- `"what is currently broken?"` — finds open incidents across all files
- `"what SSL certs expire soon?"` — surfaces time-sensitive state
- `"what am I waiting on?"` — finds pending/blocked items
- `"project X outstanding tasks"` — cross-file retrieval without knowing which file

**How it works:**
Hybrid retrieval — BM25 keyword search (SQLite FTS5) merged with semantic similarity (local embeddings via fastembed / all-MiniLM-L6-v2) using Reciprocal Rank Fusion. No API key required. The ~23 MB model downloads once and runs locally.

**Setup (one command):**
```bash
bash _tools/aikb-search/setup.sh
```

---

## memory-pipeline — Runtime capture and promotion helpers

Adds optional operator-facing tooling around `_runtime/`, including:
- `runtime_cli.py` for `hud`, `status`, `prompt`, `focus`, and one-off `capture`
- `approvals_cli.py` for managing `_pending_approvals.md`
- opt-in zsh hooks for conservative high-signal command capture into runtime events

See [`_tools/memory-pipeline/README.md`](memory-pipeline/README.md) for the full command surface and guardrails.
