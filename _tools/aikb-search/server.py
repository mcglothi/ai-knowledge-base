#!/usr/bin/env python3
"""
AIKB Search + Memory — MCP Server

Exposes aikb_search and aikb_remember to any MCP client (Claude Code, Gemini CLI, etc.).
Runs as a stdio subprocess; register with:

    claude mcp add aikb-search -s user -- \
        /path/to/_tools/aikb-search/.venv/bin/python /path/to/_tools/aikb-search/server.py

Run setup.sh to install dependencies and register automatically.
On first call, auto-builds the index if the DB doesn't exist yet.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# Ensure sibling modules are importable regardless of cwd
sys.path.insert(0, str(Path(__file__).parent))

from fastmcp import FastMCP
from indexer import DB_PATH, build_index
from search import format_results, search

AIKB_ROOT = Path(__file__).resolve().parents[2]
EVENTS_DIR = AIKB_ROOT / "_runtime" / "events"

_SECRET_HINTS = ("password", "api_key", "apikey", "token", "secret", "private key")

mcp = FastMCP(
    "AIKB Search",
    instructions=(
        "Search and write to the AI Knowledge Base (AIKB) — personal knowledge store covering "
        "projects, work context, infrastructure, and any other domains you track. "
        "Use aikb_search for freeform or diagnostic queries where you don't know "
        "which file to load: 'what is currently broken?', 'what SSL certs expire soon?', "
        "'what needs attention?', 'what am I waiting on?'. "
        "Use aikb_remember to write a durable memory (decision, observation, change, or "
        "blocker) to the runtime event log for later review and promotion. "
        "Results include file path and section — load the specific file if you need full detail."
    ),
)


@mcp.tool()
def aikb_search(
    query: str,
    top_k: int = 5,
    as_of: str = "",
    before: str = "",
    after: str = "",
) -> str:
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
        as_of:  Filter results to as they existed on this date (YYYY-MM-DD).
        before: Exclude results modified after this date (YYYY-MM-DD).
        after:  Exclude results modified before this date (YYYY-MM-DD).
    """
    top_k = min(max(1, top_k), 10)

    def parse_date(ds: str) -> float | None:
        if not ds:
            return None
        try:
            # Treat YYYY-MM-DD as midnight UTC
            dt = datetime.fromisoformat(ds).replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except ValueError:
            print(f"Warning: Invalid date format '{ds}'. Expected YYYY-MM-DD.", file=sys.stderr)
            return None

    # as_of is equivalent to before
    d_before = parse_date(before) or parse_date(as_of)
    d_after  = parse_date(after)

    if not DB_PATH.exists():
        return (
            "Index not built yet — building now (downloads ~23 MB model on first run)...\n"
            + _build_and_search(query, top_k, d_before, d_after)
        )

    try:
        results = search(query, top_k=top_k, before=d_before, after=d_after)
        return format_results(results)
    except FileNotFoundError:
        return _build_and_search(query, top_k, d_before, d_after)


@mcp.tool()
def aikb_remember(
    summary: str,
    project: str,
    type: str = "observation",
    agent: str = "mcp-client",
    sensitivity: str = "normal",
    promote_hint: str = "candidate",
) -> str:
    """
    Write a durable memory event to AIKB's runtime event log.

    The event is appended to _runtime/events/YYYY-MM-DD.ndjson and queued for
    candidate review. It does NOT modify canonical AIKB docs directly — it enters
    the governed review pipeline (build_candidates → review → promote).

    Use this whenever you learn something a future agent should know:
      - A decision was made and the rationale should be preserved
      - A system's state changed in a way not yet reflected in AIKB
      - A blocker or gotcha was discovered
      - A task was completed or a new one identified

    Args:
        summary: What to remember. Be specific and factual. Do NOT include passwords,
                 tokens, or secrets — reference them as '[Stored in password manager: Name]'.
        project: The AIKB file this memory relates to, e.g. 'projects/my-project.md'.
                 Use 'general' if no specific file applies.
        type: One of 'decision', 'observation', 'change', 'blocker'.
        agent: Name of the calling agent (auto-filled from MCP context when omitted).
        sensitivity: 'normal' (default, eligible for auto-promotion) or
                     'restricted' (never auto-promoted, requires manual review).
        promote_hint: 'candidate' (queue for review, default) or
                      'ignore' (ephemeral capture, skip candidate pipeline).

    Returns a confirmation string with the event ID.
    """
    # Reject potential secrets
    lower_summary = summary.lower()
    if any(hint in lower_summary for hint in _SECRET_HINTS):
        return (
            "Refused: summary appears to contain a secret. "
            "Store the credential in your password manager and reference it as "
            "'[Stored in password manager: <Item Name>]' instead."
        )

    # Validate type
    valid_types = {"decision", "observation", "change", "blocker"}
    if type not in valid_types:
        return f"Refused: type must be one of {sorted(valid_types)}, got '{type}'."

    valid_sensitivity = {"normal", "restricted"}
    if sensitivity not in valid_sensitivity:
        sensitivity = "normal"

    valid_promote = {"candidate", "ignore"}
    if promote_hint not in valid_promote:
        promote_hint = "candidate"

    now = datetime.now(timezone.utc)
    event_id = f"evt_{now.strftime('%Y%m%d_%H%M%S_%f')}_{uuid4().hex[:6]}"
    session_id = f"mcp-{now.strftime('%Y%m%d%H%M%S')}"

    event = {
        "id": event_id,
        "ts_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_id": session_id,
        "agent": agent,
        "type": type,
        "project": project,
        "summary": summary.strip(),
        "evidence": [],
        "sensitivity": sensitivity,
        "promote_hint": promote_hint,
    }

    date_str = now.strftime("%Y-%m-%d")
    out_file = EVENTS_DIR / f"{date_str}.ndjson"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        with out_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=True) + "\n")
    except OSError as e:
        return f"Error writing event: {e}"

    return (
        f"Remembered: {event_id}\n"
        f"  type: {type}\n"
        f"  project: {project}\n"
        f"  summary: {summary[:120]}{'...' if len(summary) > 120 else ''}\n"
        f"  file: {out_file.relative_to(AIKB_ROOT)}\n"
        f"  promote_hint: {promote_hint}\n"
        "Run 'python3 _tools/memory-pipeline/build_candidates.py' to queue for review."
    )


def _build_and_search(query: str, top_k: int, before: float | None, after: float | None) -> str:
    try:
        build_index(verbose=False)
        results = search(query, top_k=top_k, before=before, after=after)
        return format_results(results)
    except Exception as e:
        return f"Error building index or searching: {e}"


if __name__ == "__main__":
    mcp.run()
