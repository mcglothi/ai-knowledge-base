# Search Setup

**Summary:** How to set up the `aikb-search` MCP server for natural language queries across your AIKB.

---

## What it does

The `aikb-search` MCP server adds an `aikb_search` tool to your AI agent. Instead of loading files by keyword, the agent can ask freeform questions:

```
aikb_search("what is currently broken?")
aikb_search("what SSL certs expire soon?")
aikb_search("what am I waiting on from clients?")
aikb_search("project X deployment steps")
```

Results include the file path, section heading, and a text excerpt. The agent loads the specific file only if it needs full detail.

**How it works:** hybrid retrieval — BM25 keyword search (SQLite FTS5) merged with semantic similarity (fastembed / all-MiniLM-L6-v2, runs fully locally) via Reciprocal Rank Fusion. No API key required.

---

## Prerequisites

- Python 3.10+
- Claude Code (for automatic MCP registration — Gemini CLI registration is manual, see below)
- A local AIKB clone (the server reads files directly from disk)

---

## Quick setup

```bash
bash _tools/aikb-search/setup.sh
```

This does everything in one shot:
1. Creates a Python venv at `_tools/aikb-search/.venv/`
2. Installs dependencies (`fastembed`, `fastmcp`, `numpy`, `pyyaml`)
3. Downloads the embedding model (~23 MB, cached in `~/.cache/fastembed/`)
4. Builds the initial search index
5. Installs a git post-commit hook that rebuilds the index automatically when `.md` files change
6. Registers the MCP server with Claude Code

Start a new Claude Code session after setup — the `aikb_search` tool will be available immediately.

---

## Rebuilding the index manually

The post-commit hook keeps the index current automatically. If you need to rebuild manually:

```bash
# Incremental — only reindexes changed files (fast)
_tools/aikb-search/.venv/bin/python _tools/aikb-search/indexer.py

# Full rebuild — reindexes everything
_tools/aikb-search/.venv/bin/python _tools/aikb-search/indexer.py --force
```

---

## Gemini CLI registration

`setup.sh` registers with Claude Code only. For Gemini CLI, register manually:

```bash
PYTHON_BIN="$(pwd)/_tools/aikb-search/.venv/bin/python"
SERVER_PY="$(pwd)/_tools/aikb-search/server.py"

gemini mcp add aikb-search "$PYTHON_BIN" "$SERVER_PY"
```

---

## What gets indexed

The indexer walks all `.md` files in your AIKB and `_state.yaml`. It skips:
- `_tools/` — the tool itself
- `_agents/` — agent instruction files (not knowledge content)
- `_templates/` — blank templates

Everything else — `personal/`, `projects/`, `work/`, and any custom domains you've created — is indexed and searchable.

Files are split at H2 headings (`##`) so each section is independently retrievable. A query about SSL certs won't pull in unrelated sections from the same file.

---

## What the index is NOT

- **Not a replacement for reading files.** Results give you file + section + excerpt. If the agent needs full detail, it should read the file directly.
- **Not perfectly precise.** Semantic similarity finds conceptually related content, which is useful but not always exact. Verify important details by reading the source file.
- **Not synced to GitHub.** The index is local only (`_tools/aikb-search/aikb_index.db`, git-ignored). Each machine builds its own.

---

## Re-running setup on a new machine

`setup.sh` is idempotent — safe to re-run:

```bash
bash _tools/aikb-search/setup.sh
```

It will recreate the venv, upgrade dependencies, rebuild the index, and re-register the MCP server.

---

## Troubleshooting

**"Index not built yet" on first query**
→ The server builds the index on first use automatically. Subsequent queries are fast.

**"fastembed not found" or import errors**
→ The MCP server must use the venv Python, not the system Python. Re-run `setup.sh` to fix the registration.

**Index is stale after adding files**
→ The post-commit hook triggers automatically on commit. If you added files without committing, run `indexer.py` manually.

**Claude Code doesn't see the tool after setup**
→ Restart Claude Code — MCP servers are registered at startup.
