# Tools

Optional tools that extend AIKB capabilities. None are required for basic use.

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

This installs dependencies, builds the index, installs a git post-commit hook for automatic re-indexing, and registers the MCP server with Claude Code.

See [`docs/search-setup.md`](../docs/search-setup.md) for full details, manual setup, and Gemini CLI registration.

---

## memory-pipeline — Runtime capture and promotion helpers

Adds optional operator-facing tooling around `_runtime/`, including:
- `runtime_cli.py` for `hud`, `status`, `prompt`, `focus`, and one-off `capture`
- `approvals_cli.py` for managing `_pending_approvals.md`
- opt-in zsh hooks for conservative high-signal command capture into runtime events

Useful starter commands:
```bash
python3 _tools/memory-pipeline/runtime_cli.py hud
python3 _tools/memory-pipeline/runtime_cli.py focus set --task "Review queue health" --verify "Run hud again"
python3 _tools/memory-pipeline/approvals_cli.py list
bash _tools/memory-pipeline/install_zsh_hooks.sh
```

See [`_tools/memory-pipeline/README.md`](memory-pipeline/README.md) for the full command surface and guardrails.
