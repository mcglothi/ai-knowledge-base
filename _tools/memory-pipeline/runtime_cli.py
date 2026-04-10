#!/usr/bin/env python3
"""Operator-facing runtime memory CLI for capture and status."""

from __future__ import annotations

import argparse
import json
import re
import socket
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.dont_write_bytecode = True

import ingest_runtime


ROOT = Path(__file__).resolve().parents[2]
EVENTS_DIR = ROOT / "_runtime" / "events"
CANDIDATES_DIR = ROOT / "_runtime" / "candidates"
QUEUE_FILE = ROOT / "_runtime" / "promotion-queue.md"
ACTIVE_FILE = ROOT / "_agents" / "active.md"
PENDING_APPROVALS_FILE = ROOT / "_pending_approvals.md"
HUD_STATE_DIR = ROOT / "_runtime" / "session-hud"
TEMPLATE_SYNC_STATE_FILE = ROOT / ".aikb-config.d" / "template-sync-state.json"
TEMPLATE_SYNC_SCRIPT = ROOT / "sync.sh"

STATUS_RE = re.compile(r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|")
CANDIDATE_ID_RE = re.compile(r"^\s*-\s+id:\s+(\S+)\s*$")
TABLE_ROW_RE = re.compile(r"^\|")
SEPARATOR_RE = re.compile(r"^\|[-\s|]+\|$")
ALIGNMENT_CELL_RE = re.compile(r"^:?-{3,}:?$")
LAST_WRITE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s+[A-Z]{2,4}$")
OPEN_APPROVAL_STATUSES = {"pending", "requested", "needs-review", "awaiting-review", "awaiting-approval"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    capture = subparsers.add_parser("capture", help="Capture one runtime event.")
    capture.add_argument("--agent", required=True)
    capture.add_argument("--session-id", required=True)
    capture.add_argument("--type", required=True, choices=sorted(ingest_runtime.EVENT_TYPES))
    capture.add_argument("--project", required=True)
    capture.add_argument("--summary", required=True)
    capture.add_argument("--evidence", action="append", default=[])
    capture.add_argument(
        "--sensitivity", default="normal", choices=sorted(ingest_runtime.SENSITIVITY)
    )
    capture.add_argument(
        "--promote-hint", default="candidate", choices=sorted(ingest_runtime.PROMOTE_HINT)
    )
    capture.add_argument("--date", help="Override date for output file (YYYY-MM-DD)")

    status = subparsers.add_parser("status", help="Summarize runtime memory state.")
    status.add_argument("--limit", type=int, default=3, help="How many recent rows to show per section.")

    hud = subparsers.add_parser("hud", help="Show the lightweight session HUD.")
    hud.add_argument("--limit", type=int, default=3, help="How many recent rows to show per section.")

    template_sync = subparsers.add_parser(
        "template-sync",
        help="Show template update state and optionally run a safe check-only sync probe.",
    )
    template_sync.add_argument(
        "--auto-check",
        action="store_true",
        help="Run ./sync.sh --check only when the saved check window is stale or missing.",
    )
    template_sync.add_argument(
        "--force-check",
        action="store_true",
        help="Run ./sync.sh --check immediately, even if the saved check window is still fresh.",
    )

    check_repo = subparsers.add_parser(
        "check-repo",
        help="Check a git repo for active AIKB claims and crash-recovery signals.",
    )
    check_repo.add_argument("--path", default=".", help="Path inside the repo to inspect.")

    claim_session = subparsers.add_parser(
        "claim-session",
        help="Create or update this agent's active-session repo/scope claim.",
    )
    claim_session.add_argument("--agent", required=True)
    claim_session.add_argument("--repo", required=True, help="Claimed repo name or AIKB.")
    claim_session.add_argument("--scope", required=True, help="Claimed scope/path glob.")
    claim_session.add_argument("--task", required=True, help="Brief task description.")
    claim_session.add_argument("--mode", default="local")
    claim_session.add_argument("--host", default=socket.gethostname())
    claim_session.add_argument("--timestamp", default="")

    release_session = subparsers.add_parser(
        "release-session",
        help="Remove this agent's active-session claim row.",
    )
    release_session.add_argument("--agent", required=True)
    release_session.add_argument("--host", default=socket.gethostname())

    prompt = subparsers.add_parser("prompt", help="Render a compact one-line prompt/status segment.")
    prompt.add_argument("--max-task", type=int, default=24, help="Max task length in prompt output.")

    closeout = subparsers.add_parser("closeout", help="Capture a structured session closeout event.")
    closeout.add_argument("--agent", default="codex")
    closeout.add_argument("--session-id", default="")
    closeout.add_argument("--project", default="", help="Override project label/path for the closeout event.")
    closeout.add_argument("--phrase", default="", help="Optional operator phrase that triggered closeout.")
    closeout.add_argument("--note", default="", help="Optional freeform note for the closeout summary.")
    closeout.add_argument("--limit", type=int, default=3, help="How many recent rows to sample for context.")
    closeout.add_argument("--dry-run", action="store_true", help="Print the event payload without writing it.")

    focus = subparsers.add_parser("focus", help="Set or inspect the HUD focus state.")
    focus_subparsers = focus.add_subparsers(dest="focus_command", required=True)

    focus_set = focus_subparsers.add_parser("set", help="Set the current objective and next verification step.")
    focus_set.add_argument("--task", required=True, help="Short description of the current objective.")
    focus_set.add_argument("--verify", default="", help="Next verification step to surface in the HUD.")
    focus_set.add_argument("--note", default="", help="Optional note to show in the HUD.")
    focus_set.add_argument("--session-key", default="", help="Override HUD state key (defaults to hostname).")

    focus_show = focus_subparsers.add_parser("show", help="Show the current focus state.")
    focus_show.add_argument("--session-key", default="", help="Override HUD state key (defaults to hostname).")

    focus_clear = focus_subparsers.add_parser("clear", help="Clear the current focus state.")
    focus_clear.add_argument("--session-key", default="", help="Override HUD state key (defaults to hostname).")

    return parser.parse_args()


def latest_matching(directory: Path, pattern: str) -> Path | None:
    matches = sorted(path for path in directory.glob(pattern) if path.is_file())
    return matches[-1] if matches else None


def count_events(path: Path | None) -> int:
    if not path or not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def recent_event_summaries(path: Path | None, limit: int) -> list[str]:
    if not path or not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        rows.append(
            f"{event.get('type', 'event')}: {event.get('summary', '').strip()} [{event.get('project', 'unknown')}]"
        )
    return rows[-limit:]


def count_candidates(path: Path | None) -> int:
    if not path or not path.exists():
        return 0
    return sum(
        1 for line in path.read_text(encoding="utf-8").splitlines() if CANDIDATE_ID_RE.match(line)
    )


def parse_queue() -> tuple[Counter[str], list[str]]:
    if not QUEUE_FILE.exists():
        return Counter(), []

    statuses: Counter[str] = Counter()
    rows: list[str] = []
    for line in QUEUE_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not TABLE_ROW_RE.match(stripped) or SEPARATOR_RE.match(stripped):
            continue
        if "Candidate ID" in stripped or "Reorg ID" in stripped:
            continue
        match = STATUS_RE.match(stripped)
        if not match:
            continue
        candidate_id, target, klass, confidence, status, reviewer, notes = [g.strip() for g in match.groups()]
        if not candidate_id.startswith("cand_"):
            continue
        statuses[status or "unknown"] += 1
        note_suffix = f" reviewer={reviewer}" if reviewer else ""
        rows.append(f"{candidate_id} -> {status} ({klass}, {confidence}) {target}{note_suffix}".strip())
    return statuses, rows


def parse_active_sessions(limit: int) -> list[str]:
    if not ACTIVE_FILE.exists():
        return []
    rows: list[str] = []
    in_comment = False
    for line in ACTIVE_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if "<!--" in stripped:
            in_comment = True
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        if not stripped.startswith("|") or "Agent" in stripped or SEPARATOR_RE.match(stripped):
            continue
        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if len(parts) == 5:
            agent, host, mode, last_write, task = parts
            repo = ""
            scope = ""
        elif len(parts) >= 7:
            agent, host, mode, last_write, repo, scope, task = parts[:7]
        else:
            continue
        if agent.startswith("*(") or "no active sessions" in agent.lower():
            continue
        location = f" repo={repo}" if repo and repo != "—" else ""
        scope_suffix = f" scope={scope}" if scope and scope != "—" else ""
        rows.append(f"{agent} on {host} [{mode}] @ {last_write}{location}{scope_suffix} :: {task}")
    return rows[-limit:]


def parse_active_session_rows() -> list[dict[str, str]]:
    if not ACTIVE_FILE.exists():
        return []
    rows: list[dict[str, str]] = []
    in_comment = False
    for line in ACTIVE_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if "<!--" in stripped:
            in_comment = True
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        if not stripped.startswith("|") or "Agent" in stripped or SEPARATOR_RE.match(stripped):
            continue
        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if len(parts) == 5:
            agent, host, mode, last_write, task = parts
            repo = ""
            scope = ""
        elif len(parts) >= 7:
            agent, host, mode, last_write, repo, scope, task = parts[:7]
        else:
            continue
        if agent.startswith("*(") or "no active sessions" in agent.lower():
            continue
        rows.append(
            {
                "agent": agent,
                "host": host,
                "mode": mode,
                "last_write": last_write,
                "repo": repo,
                "scope": scope,
                "task": task,
            }
        )
    return rows


def current_timestamp_text() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def active_table_header(lines: list[str]) -> tuple[int, str] | None:
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("|") and "Agent" in stripped:
            return idx, stripped
    return None


def active_table_separator_index(lines: list[str], header_index: int) -> int | None:
    for idx in range(header_index + 1, len(lines)):
        stripped = lines[idx].strip()
        if SEPARATOR_RE.match(stripped):
            return idx
    return None


def active_table_column_count(header_line: str) -> int:
    return len([part for part in header_line.strip("|").split("|")])


def active_placeholder_row(column_count: int) -> str:
    if column_count <= 0:
        column_count = 5
    cells = ["*(no active sessions)*"] + ["—"] * (column_count - 1)
    return "| " + " | ".join(cells) + " |"


def update_active_last_updated(lines: list[str]) -> list[str]:
    stamp = datetime.now().astimezone().strftime("%Y-%m-%d")
    updated: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith("**Last Updated:**"):
            updated.append(f"**Last Updated:** {stamp}")
            replaced = True
        else:
            updated.append(line)
    return updated if replaced else lines


def active_row_matches(parts: list[str], agent: str, host: str) -> bool:
    if not parts:
        return False
    return len(parts) >= 2 and parts[0] == agent and parts[1] == host


def upsert_active_session(
    agent: str,
    host: str,
    mode: str,
    timestamp: str,
    repo: str,
    scope: str,
    task: str,
) -> None:
    lines = ACTIVE_FILE.read_text(encoding="utf-8").splitlines()
    header_info = active_table_header(lines)
    if not header_info:
        raise SystemExit(f"Could not find active-session table header in {ACTIVE_FILE}")
    header_index, header_line = header_info
    separator_index = active_table_separator_index(lines, header_index)
    if separator_index is None:
        raise SystemExit(f"Could not find active-session table separator in {ACTIVE_FILE}")
    column_count = active_table_column_count(header_line)
    row = f"| {agent} | {host} | {mode} | {timestamp} | {repo} | {scope} | {task} |"

    start = separator_index + 1
    end = start
    while end < len(lines):
        stripped = lines[end].strip()
        if stripped.startswith("|"):
            end += 1
            continue
        break

    new_rows: list[str] = []
    replaced = False
    for line in lines[start:end]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if parts and (parts[0].startswith("*(") or "no active sessions" in parts[0].lower()):
            continue
        if active_row_matches(parts, agent, host):
            if not replaced:
                new_rows.append(row)
                replaced = True
            continue
        new_rows.append(line)
    if not replaced:
        new_rows.append(row)
    if not new_rows:
        new_rows.append(active_placeholder_row(column_count))

    lines = lines[:start] + new_rows + lines[end:]
    ACTIVE_FILE.write_text("\n".join(update_active_last_updated(lines)).rstrip() + "\n", encoding="utf-8")


def release_active_session(agent: str, host: str) -> bool:
    lines = ACTIVE_FILE.read_text(encoding="utf-8").splitlines()
    header_info = active_table_header(lines)
    if not header_info:
        raise SystemExit(f"Could not find active-session table header in {ACTIVE_FILE}")
    header_index, header_line = header_info
    separator_index = active_table_separator_index(lines, header_index)
    if separator_index is None:
        raise SystemExit(f"Could not find active-session table separator in {ACTIVE_FILE}")
    column_count = active_table_column_count(header_line)

    start = separator_index + 1
    end = start
    while end < len(lines):
        stripped = lines[end].strip()
        if stripped.startswith("|"):
            end += 1
            continue
        break

    new_rows: list[str] = []
    removed = False
    for line in lines[start:end]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if parts and (parts[0].startswith("*(") or "no active sessions" in parts[0].lower()):
            continue
        if active_row_matches(parts, agent, host):
            removed = True
            continue
        new_rows.append(line)
    if not new_rows:
        new_rows.append(active_placeholder_row(column_count))
    lines = lines[:start] + new_rows + lines[end:]
    ACTIVE_FILE.write_text("\n".join(update_active_last_updated(lines)).rstrip() + "\n", encoding="utf-8")
    return removed


def parse_pending_approvals(limit: int) -> tuple[Counter[str], list[str]]:
    if not PENDING_APPROVALS_FILE.exists():
        return Counter(), []

    statuses: Counter[str] = Counter()
    rows: list[str] = []
    for line in PENDING_APPROVALS_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not TABLE_ROW_RE.match(stripped) or SEPARATOR_RE.match(stripped):
            continue
        if "Date" in stripped or "Action/Decision" in stripped:
            continue
        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if len(parts) != 6:
            continue
        if all(ALIGNMENT_CELL_RE.fullmatch(part) for part in parts):
            continue
        date, agent, project, action, status, notes = parts
        normalized = status.lower() or "unknown"
        if normalized not in OPEN_APPROVAL_STATUSES:
            continue
        statuses[normalized] += 1
        rows.append(f"{date} {project}: {action} [{status}]")
    return statuses, rows[-limit:]


def git_state() -> dict[str, object]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "status", "--short", "--branch"],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    branch = lines[0] if lines else "## unknown"
    changed = lines[1:]
    return {
        "branch": branch,
        "changed_count": len(changed),
        "clean": len(changed) == 0,
        "changed_lines": changed,
    }


def git_context_for_path(path: Path) -> dict[str, str]:
    resolved = path.resolve()
    repo_root = ""
    branch = ""
    try:
        repo_root = subprocess.run(
            ["git", "-C", str(resolved), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        branch = subprocess.run(
            ["git", "-C", str(resolved), "branch", "--show-current"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return {"cwd": str(resolved), "repo_root": "", "branch": ""}

    display_cwd = str(resolved)
    if repo_root and display_cwd.startswith(repo_root):
        suffix = display_cwd[len(repo_root):].lstrip("/")
        display_cwd = f"{Path(repo_root).name}/{suffix}" if suffix else Path(repo_root).name

    return {"cwd": display_cwd, "repo_root": repo_root, "branch": branch}


def relative_age_text(path: Path | None) -> str:
    if not path or not path.exists():
        return "none"
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    delta = datetime.now(timezone.utc) - modified
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 48:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


def relative_age_from_dt(value: datetime | None) -> str:
    if value is None:
        return "unknown"
    delta = datetime.now(timezone.utc) - value
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    if hours < 48:
        return f"{hours}h"
    days = hours // 24
    return f"{days}d"


def parse_last_write(value: str) -> datetime | None:
    raw = value.strip()
    if not raw:
        return None
    local_tz = datetime.now().astimezone().tzinfo
    for candidate in (raw, re.sub(r"\s+[A-Z]{2,4}$", "", raw)):
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(candidate, fmt).replace(tzinfo=local_tz)
            except ValueError:
                continue
    match = LAST_WRITE_RE.match(raw)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M").replace(tzinfo=local_tz)
    except ValueError:
        return None


def normalize_repo_claim(value: str) -> str:
    return value.strip().rstrip("/").lower()


def parse_git_status_paths(lines: list[str]) -> tuple[list[str], int]:
    paths: list[str] = []
    untracked = 0
    for line in lines:
        if len(line) < 4:
            continue
        status = line[:2]
        path_part = line[3:]
        if status == "??":
            untracked += 1
        if " -> " in path_part:
            path_part = path_part.split(" -> ", 1)[1]
        cleaned = path_part.strip()
        if cleaned:
            paths.append(cleaned)
    return paths, untracked


def latest_repo_change_time(repo_root: Path, rel_paths: list[str]) -> datetime | None:
    latest: datetime | None = None
    for rel_path in rel_paths:
        abs_path = repo_root / rel_path
        if not abs_path.exists():
            continue
        candidate = datetime.fromtimestamp(abs_path.stat().st_mtime, tz=timezone.utc)
        if latest is None or candidate > latest:
            latest = candidate
    return latest


def rows_matching_repo(repo_root: Path, sessions: list[dict[str, str]]) -> list[dict[str, str]]:
    repo_name = normalize_repo_claim(repo_root.name)
    repo_path = normalize_repo_claim(str(repo_root))
    matches: list[dict[str, str]] = []
    for row in sessions:
        claimed = normalize_repo_claim(row.get("repo", ""))
        if not claimed or claimed == "—":
            continue
        if claimed == repo_name or claimed == repo_path or repo_path.endswith("/" + claimed):
            matches.append(row)
    return matches


def current_memory_source(latest_events: Path | None, latest_candidates: Path | None) -> str:
    if latest_events:
        return f"runtime events ({latest_events.name}, {relative_age_text(latest_events)})"
    if latest_candidates:
        return f"candidate bundle ({latest_candidates.name}, {relative_age_text(latest_candidates)})"
    return "canonical docs only"


def load_event_rows(path: Path | None) -> list[dict]:
    if not path or not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def summarize_event_breakdown(rows: list[dict]) -> tuple[str, str]:
    if not rows:
        return ("none", "none")
    by_type = Counter(str(row.get("type", "unknown")) for row in rows)
    by_agent = Counter(str(row.get("agent", "unknown")) for row in rows)
    type_summary = ", ".join(f"{key}={value}" for key, value in sorted(by_type.items()))
    agent_summary = ", ".join(f"{key}={value}" for key, value in sorted(by_agent.items()))
    return (type_summary, agent_summary)


def progress_bar(filled: int, total: int, width: int = 10) -> str:
    total = max(total, 1)
    filled = max(0, min(filled, total))
    ticks = round((filled / total) * width)
    return "[" + ("#" * ticks) + ("-" * (width - ticks)) + f"] {filled}/{total}"


def truncate(text: str, max_len: int) -> str:
    value = text.strip()
    if max_len < 4 or len(value) <= max_len:
        return value
    return value[: max_len - 3] + "..."


def default_session_id(agent: str) -> str:
    return f"{agent}-{socket.gethostname()}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"


def parse_utc_timestamp(value: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
        return datetime.fromisoformat(text).astimezone(timezone.utc)
    except ValueError:
        return None


def short_sha(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    return text[:12]


def collect_template_sync_status() -> dict[str, object]:
    status: dict[str, object] = {
        "available": TEMPLATE_SYNC_SCRIPT.exists() and TEMPLATE_SYNC_STATE_FILE.exists(),
        "script_exists": TEMPLATE_SYNC_SCRIPT.exists(),
        "state_exists": TEMPLATE_SYNC_STATE_FILE.exists(),
        "stale": False,
        "updates_pending": False,
        "last_checked_utc": "",
        "last_checked_age": "",
        "last_checked_days": None,
        "check_interval_days": None,
        "last_seen_upstream_sha": "",
        "last_applied_upstream_sha": "",
        "summary": "template sync not configured",
        "suggested_command": "python3 _tools/memory-pipeline/runtime_cli.py template-sync --auto-check",
    }

    if not status["script_exists"]:
        status["summary"] = "sync.sh not present"
        return status
    if not status["state_exists"]:
        status["summary"] = "template sync state missing; run install.sh first"
        return status

    try:
        raw = json.loads(TEMPLATE_SYNC_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        status["summary"] = "template sync state unreadable"
        return status
    if not isinstance(raw, dict):
        status["summary"] = "template sync state unreadable"
        return status

    last_checked = str(raw.get("last_checked_utc", "") or "").strip()
    last_seen = str(raw.get("last_seen_upstream_sha", "") or "").strip()
    last_applied = str(raw.get("last_applied_upstream_sha", "") or "").strip()

    try:
        interval_days = int(raw.get("check_interval_days", 7) or 7)
    except (TypeError, ValueError):
        interval_days = 7

    checked_dt = parse_utc_timestamp(last_checked)
    now = datetime.now(timezone.utc)
    stale = checked_dt is None or checked_dt <= (now - timedelta(days=interval_days))
    pending = bool(last_seen and last_applied and last_seen != last_applied)

    if checked_dt is None:
        checked_age = "never"
        checked_days: int | None = None
    else:
        delta = now - checked_dt
        checked_days = max(0, delta.days)
        checked_age = relative_age_from_dt(checked_dt)

    if pending:
        summary = f"updates available from last check ({short_sha(last_seen)} vs applied {short_sha(last_applied)})"
    elif stale:
        summary = f"check due ({checked_age}, every {interval_days}d)"
    else:
        summary = f"current ({checked_age}, every {interval_days}d)"

    status.update(
        {
            "available": True,
            "stale": stale,
            "updates_pending": pending,
            "last_checked_utc": last_checked,
            "last_checked_age": checked_age,
            "last_checked_days": checked_days,
            "check_interval_days": interval_days,
            "last_seen_upstream_sha": last_seen,
            "last_applied_upstream_sha": last_applied,
            "summary": summary,
        }
    )
    return status


def collect_hud_state() -> dict[str, object]:
    latest_events = latest_matching(EVENTS_DIR, "[0-9][0-9][0-9][0-9]-*.ndjson")
    latest_candidates = latest_matching(CANDIDATES_DIR, "[0-9][0-9][0-9][0-9]-*.yaml")
    latest_event_rows = load_event_rows(latest_events)
    queue_counts, queue_rows = parse_queue()
    approval_counts, approval_rows = parse_pending_approvals(3)
    sessions = parse_active_session_rows()
    git = git_state()
    hostname = socket.gethostname()
    focus = load_hud_state()
    cwd_context = git_context_for_path(Path.cwd())
    event_types, event_agents = summarize_event_breakdown(latest_event_rows)
    template_sync = collect_template_sync_status()

    current = next((row for row in reversed(sessions) if row["host"] == hostname), None)
    others = [row for row in sessions if row is not current]
    current_age = relative_age_from_dt(parse_last_write(current["last_write"])) if current else "unknown"

    context_points = 1
    if current:
        context_points += 1
    if focus.get("task"):
        context_points += 1
    if latest_events:
        context_points += 1
    if latest_candidates:
        context_points += 1

    return {
        "latest_events": latest_events,
        "latest_candidates": latest_candidates,
        "latest_event_rows": latest_event_rows,
        "queue_counts": queue_counts,
        "queue_rows": queue_rows,
        "approval_counts": approval_counts,
        "approval_rows": approval_rows,
        "sessions": sessions,
        "current": current,
        "others": others,
        "git": git,
        "hostname": hostname,
        "focus": focus,
        "cwd_context": cwd_context,
        "event_types": event_types,
        "event_agents": event_agents,
        "current_age": current_age,
        "context_points": context_points,
        "template_sync": template_sync,
    }


def session_key(explicit: str = "") -> str:
    key = explicit.strip() or socket.gethostname()
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", key)


def hud_state_path(explicit: str = "") -> Path:
    return HUD_STATE_DIR / f"{session_key(explicit)}.json"


def load_hud_state(explicit: str = "") -> dict[str, str]:
    path = hud_state_path(explicit)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def save_hud_state(task: str, verify: str, note: str, explicit: str = "") -> Path:
    path = hud_state_path(explicit)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "task": task.strip(),
        "verify": verify.strip(),
        "note": note.strip(),
        "updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "host": socket.gethostname(),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def clear_hud_state(explicit: str = "") -> Path | None:
    path = hud_state_path(explicit)
    if not path.exists():
        return None
    path.unlink()
    return path


def print_status(limit: int) -> int:
    latest_events = latest_matching(EVENTS_DIR, "[0-9][0-9][0-9][0-9]-*.ndjson")
    latest_candidates = latest_matching(CANDIDATES_DIR, "[0-9][0-9][0-9][0-9]-*.yaml")
    queue_counts, queue_rows = parse_queue()
    active_rows = parse_active_sessions(limit)

    print("[runtime] Active Sessions")
    if active_rows:
        for row in active_rows:
            print(f"  - {row}")
    else:
        print("  - none")

    print("[runtime] Event Capture")
    if latest_events:
        print(f"  - latest_file: {latest_events.relative_to(ROOT)}")
        print(f"  - event_count: {count_events(latest_events)}")
        for row in recent_event_summaries(latest_events, limit):
            print(f"  - recent: {row}")
    else:
        print("  - no runtime events captured yet")

    print("[runtime] Candidate Bundles")
    if latest_candidates:
        print(f"  - latest_file: {latest_candidates.relative_to(ROOT)}")
        print(f"  - candidate_count: {count_candidates(latest_candidates)}")
    else:
        print("  - no candidate bundles yet")

    print("[runtime] Promotion Queue")
    if queue_counts:
        summary = ", ".join(f"{status}={count}" for status, count in sorted(queue_counts.items()))
        print(f"  - statuses: {summary}")
        for row in queue_rows[-limit:]:
            print(f"  - recent: {row}")
    else:
        print("  - no queue entries found")
    return 0


def print_hud(limit: int) -> int:
    state = collect_hud_state()
    latest_events = state["latest_events"]
    latest_candidates = state["latest_candidates"]
    latest_event_rows = state["latest_event_rows"]
    queue_counts = state["queue_counts"]
    queue_rows = state["queue_rows"]
    approval_counts = state["approval_counts"]
    approval_rows = state["approval_rows"]
    current = state["current"]
    others = state["others"]
    git = state["git"]
    focus = state["focus"]
    cwd_context = state["cwd_context"]
    event_types = state["event_types"]
    event_agents = state["event_agents"]
    current_age = state["current_age"]
    context_points = state["context_points"]
    template_sync = state["template_sync"]

    print("[hud] Session")
    if focus.get("task"):
        print(f"  - task: {focus['task']}")
    elif current:
        print(f"  - task: {current['task']}")
    else:
        print("  - task: no active session registered")
    if focus.get("verify"):
        print(f"  - next_verify: {focus['verify']}")
    if focus.get("note"):
        print(f"  - note: {focus['note']}")
    if focus.get("updated_utc"):
        print(f"  - focus_updated: {focus['updated_utc']}")
    if current:
        print(f"  - active_agent: {current['agent']} on {current['host']} [{current['mode']}]")
        print(f"  - last_write: {current['last_write']}")
        print(f"  - session_age_est: {current_age}")
    print(f"  - cwd: {cwd_context['cwd']}")
    print(f"  - pwd_branch: {cwd_context['branch'] or '(no git branch)'}")
    print(f"  - collaborators: {len(others)} other active session(s)")
    for row in others[:limit]:
        print(f"  - collaborator: {row['agent']} on {row['host']} :: {row['task']}")

    print("[hud] Memory")
    print(f"  - context_meter: {progress_bar(context_points, 5)}")
    print(f"  - source: {current_memory_source(latest_events, latest_candidates)}")
    print(
        f"  - memory_breakdown: events={len(latest_event_rows)}, "
        f"candidates={count_candidates(latest_candidates)}, approvals={sum(approval_counts.values())}"
    )
    if latest_events:
        print(f"  - event_count: {count_events(latest_events)}")
        print(f"  - event_types: {event_types}")
        print(f"  - agent_activity: {event_agents}")
    if latest_candidates:
        print(f"  - candidate_count: {count_candidates(latest_candidates)}")
    else:
        print("  - candidate_count: 0")
    if queue_counts:
        summary = ", ".join(f"{status}={count}" for status, count in sorted(queue_counts.items()))
        print(f"  - promotion_queue: {summary}")
        for row in queue_rows[-limit:]:
            print(f"  - queue_recent: {row}")
    else:
        print("  - promotion_queue: empty")

    print("[hud] Verify")
    print(f"  - git: {git['branch']}")
    print(f"  - repo_clean_bar: {progress_bar(1 if git['clean'] else 0, 1, width=8)}")
    if git["clean"]:
        print("  - verification_state: repo clean")
    else:
        print(f"  - verification_state: repo dirty ({git['changed_count']} file(s))")
        for line in git["changed_lines"][:limit]:
            print(f"  - changed: {line}")
    if approval_counts:
        summary = ", ".join(f"{status}={count}" for status, count in sorted(approval_counts.items()))
        print(f"  - approvals: {summary}")
        for row in approval_rows:
            print(f"  - approval_recent: {row}")
    else:
        print("  - approvals: none logged")
    if template_sync["available"]:
        print(f"  - template_sync: {template_sync['summary']}")
        print(
            f"  - template_last_checked: {template_sync['last_checked_utc'] or 'never'}"
        )
        if template_sync["updates_pending"]:
            print(
                "  - template_action: review update check and apply with operator approval"
            )
        elif template_sync["stale"]:
            print(
                f"  - template_action: run {template_sync['suggested_command']}"
            )
    return 0


def run_check_repo(args: argparse.Namespace) -> int:
    context = git_context_for_path(Path(args.path))
    repo_root_value = context.get("repo_root", "")
    if not repo_root_value:
        print(f"[runtime] not a git repo: {Path(args.path).resolve()}")
        return 1

    repo_root = Path(repo_root_value)
    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    )
    status_lines = [line for line in result.stdout.splitlines() if line.strip()]
    changed_paths, untracked_count = parse_git_status_paths(status_lines)
    latest_change = latest_repo_change_time(repo_root, changed_paths)
    sessions = parse_active_session_rows()
    matching = rows_matching_repo(repo_root, sessions)

    print(f"[runtime] Repo Check: {repo_root.name}")
    print(f"  - path: {repo_root}")
    print(f"  - branch: {context.get('branch') or 'unknown'}")
    print(f"  - changed_files: {len(changed_paths)}")
    print(f"  - untracked_files: {untracked_count}")
    if latest_change:
        print(f"  - latest_change_utc: {latest_change.strftime('%Y-%m-%d %H:%M:%SZ')}")

    if matching:
        print("  - matching_claims:")
        for row in matching:
            claim_age = parse_last_write(row.get("last_write", ""))
            newer = latest_change and claim_age and latest_change > claim_age.astimezone(timezone.utc)
            status = "possible recovery/in-flight work" if newer else "claimed"
            print(
                "    - "
                f"{row.get('agent')} on {row.get('host')} @ {row.get('last_write')} "
                f"[scope={row.get('scope') or 'n/a'}] :: {row.get('task')} ({status})"
            )
    else:
        print("  - matching_claims: none")

    if changed_paths and not matching:
        print("  - heuristic: dirty repo without active claim; re-check _agents/active.md and treat as possible crash-recovery work before editing.")
    elif changed_paths and matching:
        print("  - heuristic: dirty repo with active claim(s); coordinate before editing files in the claimed scope.")
    else:
        print("  - heuristic: no local repo dirt detected.")
    return 0


def run_claim_session(args: argparse.Namespace) -> int:
    upsert_active_session(
        agent=args.agent.strip(),
        host=args.host.strip(),
        mode=args.mode.strip(),
        timestamp=args.timestamp.strip() or current_timestamp_text(),
        repo=args.repo.strip(),
        scope=args.scope.strip(),
        task=args.task.strip(),
    )
    print(f"[runtime] claimed session: {args.agent} -> {args.repo} :: {args.scope}")
    return 0


def run_release_session(args: argparse.Namespace) -> int:
    removed = release_active_session(args.agent.strip(), args.host.strip())
    status = "released" if removed else "no matching row"
    print(f"[runtime] release-session: {status}")
    return 0


def print_prompt(max_task: int) -> int:
    state = collect_hud_state()
    git = state["git"]
    focus = state["focus"]
    current = state["current"]
    queue_counts = state["queue_counts"]
    approval_counts = state["approval_counts"]
    latest_event_rows = state["latest_event_rows"]
    cwd_context = state["cwd_context"]
    current_age = state["current_age"]
    context_points = int(state["context_points"])

    task = focus.get("task") or (current["task"] if current else "idle")
    dirty = "dirty" if not git["clean"] else "clean"
    branch = cwd_context["branch"] or "-"
    approvals_total = sum(approval_counts.values())
    queue_total = sum(queue_counts.values())
    event_total = len(latest_event_rows)
    meter = f"{context_points}/5"
    age = current_age
    template_sync = state["template_sync"]
    template_state = "n/a"
    if template_sync["available"]:
        if template_sync["updates_pending"]:
            template_state = "pending"
        elif template_sync["stale"]:
            template_state = "stale"
        else:
            template_state = "current"

    segments = [
        f"task={truncate(task, max_task)}",
        f"ctx={meter}",
        f"events={event_total}",
        f"queue={queue_total}",
        f"approvals={approvals_total}",
        f"tpl={template_state}",
        f"branch={branch}",
        f"state={dirty}",
        f"age={age}",
        f"cwd={cwd_context['cwd']}",
    ]
    print(" | ".join(segments))
    return 0


def default_closeout_project(state: dict[str, object]) -> str:
    cwd_context = state["cwd_context"]
    current = state["current"]
    focus = state["focus"]
    cwd_value = str(cwd_context.get("cwd", "")).strip()
    if cwd_value:
        return cwd_value
    if focus.get("task"):
        return str(focus["task"]).strip()
    if current:
        return str(current.get("task", "")).strip()
    return "session-closeout"


def build_closeout_event(args: argparse.Namespace) -> dict:
    state = collect_hud_state()
    git = state["git"]
    focus = state["focus"]
    current = state["current"]
    queue_counts = state["queue_counts"]
    approval_counts = state["approval_counts"]
    latest_event_rows = state["latest_event_rows"]
    latest_candidates = state["latest_candidates"]
    cwd_context = state["cwd_context"]
    current_age = state["current_age"]
    queue_total = sum(queue_counts.values())
    approvals_total = sum(approval_counts.values())
    candidate_total = count_candidates(latest_candidates)
    event_total = len(latest_event_rows)

    default_task = f"work in {cwd_context.get('cwd') or 'current repo'}"
    task = str(focus.get("task") or (current["task"] if current else default_task)).strip()
    verify = str(focus.get("verify", "")).strip()
    note = args.note.strip()
    trigger = args.phrase.strip()
    repo_state = "clean" if git["clean"] else f"dirty:{git['changed_count']}"
    project = args.project.strip() or default_closeout_project(state)

    summary_parts = [
        f"Closeout captured for task '{task}'",
        f"repo={repo_state}",
        f"branch={cwd_context.get('branch') or '-'}",
        f"cwd={cwd_context.get('cwd') or '-'}",
        f"events={event_total}",
        f"candidates={candidate_total}",
        f"queue={queue_total}",
        f"approvals={approvals_total}",
        f"session_age={current_age}",
    ]
    if verify:
        summary_parts.append(f"next_verify={verify}")
    if trigger:
        summary_parts.append(f"trigger='{trigger}'")
    if note:
        summary_parts.append(f"note='{note}'")
    summary = "; ".join(summary_parts)

    promote_hint = "candidate" if (note or trigger or not git["clean"] or queue_total or approvals_total) else "ignore"
    evidence = [
        f"git:{cwd_context.get('branch') or git['branch']}",
        f"cwd:{cwd_context.get('cwd') or '-'}",
    ]
    if trigger:
        evidence.append(f"trigger:{trigger}")
    if verify:
        evidence.append(f"verify:{verify}")
    if current:
        evidence.append(f"active-task:{current.get('task', '')}")

    closeout_args = argparse.Namespace(
        agent=args.agent,
        session_id=args.session_id.strip() or default_session_id(args.agent),
        type="observation",
        project=project,
        summary=summary,
        evidence=evidence,
        sensitivity="normal",
        promote_hint=promote_hint,
    )
    return ingest_runtime.build_event(closeout_args)


def run_closeout(args: argparse.Namespace) -> int:
    event = build_closeout_event(args)
    if args.dry_run:
        print(json.dumps(event, indent=2, ensure_ascii=True))
        return 0

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_file = EVENTS_DIR / f"{date_str}.ndjson"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=True) + "\n")

    print(f"[closeout] captured {event['id']} -> {out_file.relative_to(ROOT)}")
    print(f"[closeout] summary: {event['summary']}")
    return 0


def run_focus_set(args: argparse.Namespace) -> int:
    path = save_hud_state(args.task, args.verify, args.note, args.session_key)
    print(f"[focus] saved -> {path.relative_to(ROOT)}")
    return 0


def run_focus_show(args: argparse.Namespace) -> int:
    state = load_hud_state(args.session_key)
    if not state:
        print("[focus] no focus state set")
        return 0
    print(f"[focus] task: {state.get('task', '')}")
    if state.get("verify"):
        print(f"[focus] next_verify: {state['verify']}")
    if state.get("note"):
        print(f"[focus] note: {state['note']}")
    if state.get("updated_utc"):
        print(f"[focus] updated_utc: {state['updated_utc']}")
    return 0


def run_focus_clear(args: argparse.Namespace) -> int:
    path = clear_hud_state(args.session_key)
    if path is None:
        print("[focus] no focus state to clear")
        return 0
    print(f"[focus] cleared -> {path.relative_to(ROOT)}")
    return 0


def run_template_sync(args: argparse.Namespace) -> int:
    status = collect_template_sync_status()
    print("[template-sync] Status")
    print(f"  - summary: {status['summary']}")
    if not status["script_exists"]:
        print("  - detail: sync.sh is not present in this repo")
        return 1
    if not status["state_exists"]:
        print("  - detail: .aikb-config.d/template-sync-state.json is missing")
        print("  - next: run install.sh to initialize personalization and sync state")
        return 1

    print(f"  - last_checked_utc: {status['last_checked_utc'] or 'never'}")
    print(f"  - check_interval_days: {status['check_interval_days']}")
    print(
        f"  - last_applied_upstream_sha: {short_sha(str(status['last_applied_upstream_sha'])) or 'unknown'}"
    )
    print(
        f"  - last_seen_upstream_sha: {short_sha(str(status['last_seen_upstream_sha'])) or 'unknown'}"
    )

    should_run = args.force_check or (args.auto_check and bool(status["stale"]))
    if args.auto_check and not should_run:
        print("  - action: skipped check; saved window is still fresh")
        return 0
    if not args.auto_check and not args.force_check:
        print(f"  - next: {status['suggested_command']}")
        return 0

    cmd = [str(TEMPLATE_SYNC_SCRIPT), "--check"]
    print("[template-sync] Running: ./sync.sh --check")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode == 0:
        refreshed = collect_template_sync_status()
        print(f"[template-sync] Updated status: {refreshed['summary']}")
    return result.returncode


def run_capture(args: argparse.Namespace) -> int:
    if ingest_runtime.looks_sensitive(args.summary):
        raise SystemExit(
            "Refusing to log potential secret in summary. Use Vaultwarden reference instead."
        )

    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_file = EVENTS_DIR / f"{date_str}.ndjson"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    event = ingest_runtime.build_event(args)
    with out_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=True) + "\n")

    print(f"[runtime] captured {event['id']} -> {out_file.relative_to(ROOT)}")
    return 0


def main() -> int:
    args = parse_args()
    if args.command == "capture":
        return run_capture(args)
    if args.command == "check-repo":
        return run_check_repo(args)
    if args.command == "claim-session":
        return run_claim_session(args)
    if args.command == "closeout":
        return run_closeout(args)
    if args.command == "focus":
        if args.focus_command == "set":
            return run_focus_set(args)
        if args.focus_command == "show":
            return run_focus_show(args)
        if args.focus_command == "clear":
            return run_focus_clear(args)
        raise SystemExit(f"Unknown focus command: {args.focus_command}")
    if args.command == "hud":
        return print_hud(args.limit)
    if args.command == "template-sync":
        return run_template_sync(args)
    if args.command == "prompt":
        return print_prompt(args.max_task)
    if args.command == "release-session":
        return run_release_session(args)
    if args.command == "status":
        return print_status(args.limit)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
