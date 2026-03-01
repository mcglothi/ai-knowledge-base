# Tools

Optional tools that extend AIKB capabilities. None are required for basic use.

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
