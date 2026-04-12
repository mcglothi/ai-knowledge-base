#!/usr/bin/env python3
"""Flag stale AIKB memory artifacts and optional runtime cleanup candidates."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STALE_DOC_DAYS = 90
STALE_COMPLETE_DAYS = 180
EXCLUDED_STALE_PREFIXES = ("personal/dev-environment/", "_templates/")
LAST_UPDATED_PATTERNS = (
    re.compile(r"\*\*Last Updated:\*\*\s*(\d{4}-\d{2}-\d{2})"),
    re.compile(r"(?im)^last_updated:\s*(\d{4}-\d{2}-\d{2})\b"),
)
INDEX_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


@dataclass
class StaleDoc:
    path: str
    last_updated: str
    age_days: int


@dataclass
class IndexEntry:
    topic: str
    status: str
    link_path: str
    linked_last_updated: str
    age_days: int


@dataclass
class PendingWithoutPriority:
    item: str
    file: str


@dataclass
class TerminalCandidateFile:
    path: str
    statuses: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit structured JSON instead of markdown.")
    parser.add_argument(
        "--delete-terminal-candidates",
        action="store_true",
        help="Delete candidate bundles where every candidate is already terminal.",
    )
    return parser.parse_args()


def parse_last_updated(text: str) -> str | None:
    for pattern in LAST_UPDATED_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1)
    return None


def age_days(last_updated: str) -> int | None:
    try:
        updated = date.fromisoformat(last_updated)
    except ValueError:
        return None
    return (datetime.now(timezone.utc).date() - updated).days


def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for path in sorted(ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT).as_posix()
        if any(rel.startswith(prefix) for prefix in EXCLUDED_STALE_PREFIXES):
            continue
        if ".git/" in rel:
            continue
        files.append(path)
    return files


def find_stale_docs() -> list[StaleDoc]:
    stale: list[StaleDoc] = []
    for path in iter_markdown_files():
        rel = path.relative_to(ROOT).as_posix()
        last_updated = parse_last_updated(path.read_text(encoding="utf-8", errors="ignore"))
        if not last_updated:
            continue
        age = age_days(last_updated)
        if age is None or age <= STALE_DOC_DAYS:
            continue
        stale.append(StaleDoc(path=rel, last_updated=last_updated, age_days=age))
    return stale


def parse_index_rows() -> list[IndexEntry]:
    index_path = ROOT / "_index.md"
    if not index_path.exists():
        return []

    findings: list[IndexEntry] = []
    for raw_line in index_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        if "Topic" in line or "System" in line or "Item" in line:
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 4:
            continue
        topic = parts[0]
        status = parts[1]
        details = parts[-1]
        normalized_status = status.lower()
        if "complete" not in normalized_status and "decommissioned" not in normalized_status:
            continue
        link_match = INDEX_LINK_RE.search(details)
        if not link_match:
            continue
        target = link_match.group(1)
        target_path = (ROOT / target).resolve()
        if not target_path.exists() or not target_path.is_file():
            continue
        linked_last_updated = parse_last_updated(target_path.read_text(encoding="utf-8", errors="ignore"))
        if not linked_last_updated:
            continue
        linked_age = age_days(linked_last_updated)
        if linked_age is None or linked_age <= STALE_COMPLETE_DAYS:
            continue
        findings.append(
            IndexEntry(
                topic=topic,
                status=status,
                link_path=Path(target).as_posix(),
                linked_last_updated=linked_last_updated,
                age_days=linked_age,
            )
        )
    return findings


def parse_state_pending_without_priority() -> list[PendingWithoutPriority]:
    state_path = ROOT / "_state.yaml"
    if not state_path.exists():
        return []

    try:
        import yaml  # type: ignore

        payload = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
        pending = payload.get("pending", []) or []
        findings = []
        for item in pending:
            if not isinstance(item, dict):
                continue
            if "priority" in item:
                continue
            findings.append(
                PendingWithoutPriority(
                    item=str(item.get("item", "")) or "(unnamed pending item)",
                    file=str(item.get("file", "_state.yaml")),
                )
            )
        return findings
    except Exception:
        pass

    findings: list[PendingWithoutPriority] = []
    in_pending = False
    current_item = ""
    current_file = "_state.yaml"
    has_priority = False
    for raw_line in state_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if line.startswith("pending:"):
            in_pending = True
            continue
        if in_pending and line and not line.startswith(" "):
            if current_item and not has_priority:
                findings.append(PendingWithoutPriority(item=current_item, file=current_file))
            in_pending = False
            current_item = ""
            current_file = "_state.yaml"
            has_priority = False
        if not in_pending:
            continue
        stripped = line.strip()
        if stripped.startswith("- item:"):
            if current_item and not has_priority:
                findings.append(PendingWithoutPriority(item=current_item, file=current_file))
            current_item = stripped.split(":", 1)[1].strip().strip('"')
            current_file = "_state.yaml"
            has_priority = False
        elif stripped.startswith("file:"):
            current_file = stripped.split(":", 1)[1].strip().strip('"')
        elif stripped.startswith("priority:"):
            has_priority = True
    if current_item and not has_priority:
        findings.append(PendingWithoutPriority(item=current_item, file=current_file))
    return findings


def parse_candidate_statuses(path: Path) -> list[str]:
    statuses: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("status:"):
            statuses.append(stripped.split(":", 1)[1].strip())
    return statuses


def find_terminal_candidate_files(delete_terminal: bool) -> list[TerminalCandidateFile]:
    findings: list[TerminalCandidateFile] = []
    for path in sorted((ROOT / "_runtime" / "candidates").glob("*.yaml")):
        statuses = parse_candidate_statuses(path)
        if not statuses:
            continue
        if any(status not in {"merged", "rejected"} for status in statuses):
            continue
        rel = path.relative_to(ROOT).as_posix()
        findings.append(TerminalCandidateFile(path=rel, statuses=statuses))
        if delete_terminal:
            path.unlink()
    return findings


def render_markdown(
    stale_docs: list[StaleDoc],
    stale_index_rows: list[IndexEntry],
    pending_without_priority: list[PendingWithoutPriority],
    terminal_candidates: list[TerminalCandidateFile],
    deleted_terminal: bool,
) -> str:
    lines = [
        "# Retention Check",
        "",
        f"- Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Stale markdown docs (> {STALE_DOC_DAYS} days): {len(stale_docs)}",
        f"- Complete/decommissioned index entries linked to docs > {STALE_COMPLETE_DAYS} days old: {len(stale_index_rows)}",
        f"- Pending items without priority: {len(pending_without_priority)}",
        f"- Terminal candidate bundles: {len(terminal_candidates)}",
        "",
        "## Stale Markdown Docs",
        "",
    ]

    if stale_docs:
        for item in stale_docs:
            lines.append(f"- `{item.path}` — last updated {item.last_updated} ({item.age_days} days old)")
    else:
        lines.append("- None")

    lines.extend(["", "## Complete / Decommissioned Index Rows", ""])
    if stale_index_rows:
        for item in stale_index_rows:
            lines.append(
                f"- `{item.topic}` [{item.status}] -> `{item.link_path}` "
                f"(last updated {item.linked_last_updated}, {item.age_days} days old)"
            )
    else:
        lines.append("- None")

    lines.extend(["", "## Pending Without Priority", ""])
    if pending_without_priority:
        for item in pending_without_priority:
            lines.append(f"- `{item.item}` -> `{item.file}`")
    else:
        lines.append("- None")

    lines.extend(["", "## Terminal Candidate Bundles", ""])
    if terminal_candidates:
        suffix = " (deleted)" if deleted_terminal else ""
        for item in terminal_candidates:
            unique_statuses = ", ".join(sorted(set(item.statuses)))
            lines.append(f"- `{item.path}` — statuses: {unique_statuses}{suffix}")
    else:
        lines.append("- None")

    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    stale_docs = find_stale_docs()
    stale_index_rows = parse_index_rows()
    pending_without_priority = parse_state_pending_without_priority()
    terminal_candidates = find_terminal_candidate_files(args.delete_terminal_candidates)

    if args.json:
        payload = {
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "stale_docs": [asdict(item) for item in stale_docs],
            "stale_complete_index_rows": [asdict(item) for item in stale_index_rows],
            "pending_without_priority": [asdict(item) for item in pending_without_priority],
            "terminal_candidate_files": [asdict(item) for item in terminal_candidates],
            "deleted_terminal_candidates": args.delete_terminal_candidates,
        }
        print(json.dumps(payload, indent=2))
        return 0

    print(
        render_markdown(
            stale_docs,
            stale_index_rows,
            pending_without_priority,
            terminal_candidates,
            args.delete_terminal_candidates,
        ),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
