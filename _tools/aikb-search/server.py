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

import yaml

# Ensure sibling modules are importable regardless of cwd
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "memory-pipeline"))

from fastmcp import FastMCP
from indexer import DB_PATH, build_index
from redaction import redact_text
from search import format_results, search

AIKB_ROOT = Path(__file__).resolve().parents[2]
EVENTS_DIR = AIKB_ROOT / "_runtime" / "events"
SUPPRESSIONS_PATH = AIKB_ROOT / "_runtime" / "suppressions.yaml"
_FEEDBACK_ISSUES = {"stale", "wrong", "incomplete", "duplicate"}

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
    include_related: bool = True,
    as_of: str = "",
    before: str = "",
    after: str = "",
    domain: str = "",
    project: str = "",
    kind: str = "",
) -> str:
    """
    Search the AIKB knowledge base using hybrid BM25 + semantic retrieval,
    with optional relationship expansion and temporal filtering.

    Args:
        query: Natural language query. Examples:
                  "what SSL certs expire soon?"
                  "what is currently broken?"
                  "what am I waiting on?"
                  "project X pending tasks"
        top_k: Number of results to return (default 5, max 10).
        include_related: Include graph-linked chunks from related files/sections.
        as_of: Snapshot cutoff date (YYYY-MM-DD), equivalent to "as of" queries.
        before: Return chunks dated on/before this date (YYYY-MM-DD).
        after: Return chunks dated on/after this date (YYYY-MM-DD).
        domain: Filter by top-level directory (e.g. "home-lab", "personal").
        project: Filter by project name in file path or tags.
        kind: Filter by content type: doc, event, script, state, candidate.
    """
    top_k = min(max(1, top_k), 10)

    as_of = as_of.strip() or None
    before = before.strip() or None
    after = after.strip() or None
    domain = domain.strip() or None
    project = project.strip() or None
    kind = kind.strip() or None

    if not DB_PATH.exists():
        return (
            "Index not built yet — building now (downloads ~23 MB model on first run)...\n"
            + _build_and_search(query, top_k, include_related, as_of, before, after, domain, project, kind)
        )

    try:
        results = search(
            query,
            top_k=top_k,
            include_related=include_related,
            as_of=as_of,
            before=before,
            after=after,
            domain=domain,
            project=project,
            kind=kind,
        )
        _log_telemetry(query, top_k, include_related, {"domain": domain, "project": project, "kind": kind, "as_of": as_of, "before": before, "after": after}, results)
        return format_results(results)
    except FileNotFoundError:
        return _build_and_search(query, top_k, include_related, as_of, before, after, domain, project, kind)


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
    # Redact credential-shaped content; proceed with redacted text.
    # Hint words alone (e.g. "the token refresh bug was fixed") never block.
    redaction = redact_text(summary)
    summary = redaction.text
    secret_notice = ""
    if redaction.redactions:
        secret_notice = (
            f" Warning: redacted credential-shaped content ({', '.join(redaction.redactions)}). "
            "Store the secret in your password manager and reference it as "
            "'[Stored in password manager: <Item Name>]'."
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
    if redaction.redactions:
        event["redactions"] = redaction.redactions

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
        + secret_notice
    )


@mcp.tool()
def aikb_request_compaction() -> str:
    """
    Request the CLI wrapper to compact or clear the current session context.
    Use this when context is getting too large (e.g., after reading large files, 
    running commands with massive output, or completing a sub-task).
    
    This will create a signal file that the AIKB CLI proxy intercepts to automatically
    inject the /compact or /compress command into your session.
    """
    trigger_file = Path("/tmp/.aikb_compact_request")
    try:
        trigger_file.touch(exist_ok=True)
        return "Compaction requested successfully. The CLI will compact the session momentarily."
    except Exception as e:
        return f"Failed to request compaction: {e}"


@mcp.tool()
def aikb_feedback(
    file: str,
    issue: str,
    section: str = "",
    note: str = "",
    proposed_correction: str = "",
) -> str:
    """
    Propose feedback about stale, wrong, incomplete, or duplicate AIKB knowledge.

    This does not mutate canonical docs. It appends a feedback event to the
    governed runtime pipeline for review.
    """
    try:
        issue = issue.strip().lower()
        if issue not in _FEEDBACK_ISSUES:
            return f"Refused: issue must be one of {sorted(_FEEDBACK_ISSUES)}, got '{issue}'."

        rel_file = _validate_relative_file(file)
        if rel_file is None:
            return f"Refused: file does not exist relative to AIKB root: {file}"

        section = section.strip()
        note = note.strip()
        summary = _feedback_summary(f"feedback({issue})", rel_file, section, note)
        detail = {"issue": issue, "note": note}
        if proposed_correction.strip():
            detail["proposed_correction"] = proposed_correction.strip()

        out_file = _append_feedback_event(summary, rel_file, section, detail)
        return f"Feedback recorded for {rel_file}{_section_suffix(section)} in {out_file.relative_to(AIKB_ROOT)}."
    except Exception as exc:
        return f"Failed to record feedback: {exc}"


@mcp.tool()
def aikb_forget(file: str, reason: str, section: str = "") -> str:
    """
    Propose suppressing a file or section from retrieval.

    This does not delete canonical content. It appends a reviewable suppression
    entry and logs a feedback event for the promotion pipeline.
    """
    try:
        rel_file = _validate_relative_file(file)
        if rel_file is None:
            return f"Refused: file does not exist relative to AIKB root: {file}"

        section = section.strip()
        reason = reason.strip()
        if not reason:
            return "Refused: reason is required."

        now = datetime.now(timezone.utc)
        entry = {
            "file": rel_file,
            "section": section,
            "reason": reason,
            "ts_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "agent": "aikb-search-mcp",
        }
        _append_suppression(entry)

        summary = _feedback_summary("forget", rel_file, section, reason)
        detail = {"issue": "stale", "note": reason, "suppression": entry}
        out_file = _append_feedback_event(summary, rel_file, section, detail, now=now)
        return f"Suppression proposed for {rel_file}{_section_suffix(section)} in {SUPPRESSIONS_PATH.relative_to(AIKB_ROOT)}; event logged to {out_file.relative_to(AIKB_ROOT)}."
    except Exception as exc:
        return f"Failed to propose suppression: {exc}"


def _section_suffix(section: str) -> str:
    return f" § {section}" if section else ""


def _validate_relative_file(file: str) -> str | None:
    rel = file.strip().lstrip("/")
    if not rel:
        return None
    path = (AIKB_ROOT / rel).resolve()
    try:
        path.relative_to(AIKB_ROOT)
    except ValueError:
        return None
    if not path.is_file():
        return None
    return str(path.relative_to(AIKB_ROOT))


def _feedback_summary(prefix: str, file: str, section: str, note: str) -> str:
    note_part = note[:120]
    return f"{prefix}: {file}{_section_suffix(section)} — {note_part}".strip()


def _append_feedback_event(
    summary: str,
    file: str,
    section: str,
    detail: dict,
    *,
    now: datetime | None = None,
) -> Path:
    now = now or datetime.now(timezone.utc)
    event = {
        "ts_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "agent": "aikb-search-mcp",
        "type": "feedback",
        "project": file,
        "summary": summary,
        "detail": {"file": file, "section": section, **detail},
    }
    out_file = EVENTS_DIR / f"{now.strftime('%Y-%m-%d')}.ndjson"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True) + "\n")
    return out_file


def _append_suppression(entry: dict):
    SUPPRESSIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    suppressions = []
    if SUPPRESSIONS_PATH.exists():
        try:
            loaded = yaml.safe_load(SUPPRESSIONS_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                suppressions = loaded
        except yaml.YAMLError:
            suppressions = []
    suppressions.append(entry)
    text = "# AIKB retrieval suppressions; review before keeping long term.\n"
    text += yaml.safe_dump(suppressions, sort_keys=False, allow_unicode=True)
    SUPPRESSIONS_PATH.write_text(text, encoding="utf-8")


def _log_telemetry(query: str, top_k: int, include_related: bool, filters: dict, results: list):
    try:
        telemetry_dir = AIKB_ROOT / "_runtime" / "telemetry" / "aikb-search"
        telemetry_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        out_file = telemetry_dir / f"{now.strftime('%Y-%m-%d')}.ndjson"

        active_filters = {k: v for k, v in filters.items() if v is not None}
        
        telemetry_results = []
        for i, r in enumerate(results):
            telemetry_results.append({
                "rank": i + 1,
                "file": r.get("file"),
                "section": r.get("section"),
                "score": r.get("score")
            })
            
        entry = {
            "ts_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "query": query,
            "top_k": top_k,
            "include_related": include_related,
            "filters": active_filters,
            "result_count": len(results),
            "results": telemetry_results
        }
        with out_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _build_and_search(
    query: str,
    top_k: int,
    include_related: bool,
    as_of: str | None,
    before: str | None,
    after: str | None,
    domain: str | None = None,
    project: str | None = None,
    kind: str | None = None,
) -> str:
    try:
        build_index(verbose=False)
        results = search(
            query,
            top_k=top_k,
            include_related=include_related,
            as_of=as_of,
            before=before,
            after=after,
            domain=domain,
            project=project,
            kind=kind,
        )
        _log_telemetry(query, top_k, include_related, {"domain": domain, "project": project, "kind": kind, "as_of": as_of, "before": before, "after": after}, results)
        return format_results(results)
    except Exception as e:
        return f"Error building index or searching: {e}"


if __name__ == "__main__":
    mcp.run()
