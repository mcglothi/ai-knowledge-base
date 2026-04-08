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
from datetime import datetime, timezone
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

STATUS_RE = re.compile(r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|")
CANDIDATE_ID_RE = re.compile(r"^\s*-\s+id:\s+(\S+)\s*$")
TABLE_ROW_RE = re.compile(r"^\|")
SEPARATOR_RE = re.compile(r"^\|[-\s|]+\|$")
ALIGNMENT_CELL_RE = re.compile(r"^:?-{3,}:?$")
LAST_WRITE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s+[A-Z]{2,4}$")


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
    for line in ACTIVE_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "Agent" in stripped or SEPARATOR_RE.match(stripped):
            continue
        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if len(parts) != 5:
            continue
        agent, host, mode, last_write, task = parts
        rows.append(f"{agent} on {host} [{mode}] @ {last_write} :: {task}")
    return rows[-limit:]


def parse_active_session_rows() -> list[dict[str, str]]:
    if not ACTIVE_FILE.exists():
        return []
    rows: list[dict[str, str]] = []
    for line in ACTIVE_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "Agent" in stripped or SEPARATOR_RE.match(stripped):
            continue
        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if len(parts) != 5:
            continue
        agent, host, mode, last_write, task = parts
        rows.append(
            {
                "agent": agent,
                "host": host,
                "mode": mode,
                "last_write": last_write,
                "task": task,
            }
        )
    return rows


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
    match = LAST_WRITE_RE.match(value.strip())
    if not match:
        return None
    try:
        local_tz = datetime.now().astimezone().tzinfo
        return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M").replace(tzinfo=local_tz)
    except ValueError:
        return None


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

    segments = [
        f"task={truncate(task, max_task)}",
        f"ctx={meter}",
        f"events={event_total}",
        f"queue={queue_total}",
        f"approvals={approvals_total}",
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
    if args.command == "prompt":
        return print_prompt(args.max_task)
    if args.command == "status":
        return print_status(args.limit)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
