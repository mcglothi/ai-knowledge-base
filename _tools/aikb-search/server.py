#!/usr/bin/env python3
"""
AIKB Search — MCP Server

Exposes the aikb_search tool to any MCP client (Claude Code, Claude Desktop).
Runs as a stdio subprocess; register with:

    claude mcp add aikb-search -s user -- \
        /path/to/_tools/aikb-search/.venv/bin/python /path/to/_tools/aikb-search/server.py

Run setup.sh to install dependencies and register automatically.
On first call, auto-builds the index if the DB doesn't exist yet.
"""

import sys
from pathlib import Path

# Ensure sibling modules are importable regardless of cwd
sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import FastMCP
from indexer import DB_PATH, build_index
from search import format_results, search

mcp = FastMCP(
    "AIKB Search",
    instructions=(
        "Search the AI Knowledge Base (AIKB) — personal knowledge store covering "
        "projects, work context, infrastructure, and any other domains you track. "
        "Use aikb_search for freeform or diagnostic queries where you don't know "
        "which file to load: 'what is currently broken?', 'what SSL certs expire soon?', "
        "'what needs attention?', 'what am I waiting on?'. "
        "Results include file path and section — load the specific file if you need full detail."
    ),
)


@mcp.tool()
def aikb_search(query: str, top_k: int = 5) -> str:
    """
    Search the AIKB knowledge base using hybrid BM25 + semantic retrieval.

    Returns the top matching file sections with excerpts and file paths.
    Use this for any question where you don't know which AIKB file to load,
    or for cross-cutting queries that might span multiple files.

    Args:
        query:  Natural language query. Examples:
                  "what SSL certs expire soon?"
                  "what is currently broken?"
                  "what am I waiting on?"
                  "project X pending tasks"
        top_k:  Number of results to return (default 5, max 10).
    """
    top_k = min(max(1, top_k), 10)

    if not DB_PATH.exists():
        return (
            "Index not built yet — building now (downloads ~23 MB model on first run)...\n"
            + _build_and_search(query, top_k)
        )

    try:
        results = search(query, top_k=top_k)
        return format_results(results)
    except FileNotFoundError:
        return _build_and_search(query, top_k)


def _build_and_search(query: str, top_k: int) -> str:
    try:
        build_index(verbose=False)
        results = search(query, top_k=top_k)
        return format_results(results)
    except Exception as e:
        return f"Error building index or searching: {e}"


if __name__ == "__main__":
    mcp.run()
