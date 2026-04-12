#!/usr/bin/env python3
"""Interactive review loop for queued runtime memory candidates."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANDIDATES_DIR = ROOT / "_runtime" / "candidates"
EVENTS_DIR = ROOT / "_runtime" / "events"
REVIEW_SCRIPT = Path(__file__).resolve().with_name("review_candidates.py")
PROPOSE_PATCHES_SCRIPT = Path(__file__).resolve().with_name("propose_patches.py")


@dataclass
class Candidate:
    id: str
    date: str
    file_path: Path
    target_file: str = ""
    proposed_change: str = ""
    confidence: float = 0.0
    class_name: str = ""
    status: str = ""
    source_events: list[str] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewer", default="human", help="Reviewer name passed into review_candidates.py")
    parser.add_argument("--date", default="", help="Restrict review to one candidate bundle date (YYYY-MM-DD)")
    return parser.parse_args()


def candidate_files(date_filter: str) -> list[Path]:
    if date_filter:
        path = CANDIDATES_DIR / f"{date_filter}.yaml"
        return [path] if path.exists() else []
    return sorted(path for path in CANDIDATES_DIR.glob("*.yaml") if path.name != "README.md")


def parse_candidate_file(path: Path) -> list[Candidate]:
    candidates: list[Candidate] = []
    current: Candidate | None = None
    in_source_events = False
    date = path.stem

    def flush() -> None:
        nonlocal current
        if current is not None:
            candidates.append(current)
        current = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if raw_line.startswith("  - id: "):
            flush()
            current = Candidate(
                id=raw_line.split(":", 1)[1].strip(),
                date=date,
                file_path=path,
            )
            in_source_events = False
            continue

        if current is None:
            continue

        stripped = raw_line.strip()
        if raw_line.startswith("    source_events:"):
            in_source_events = True
            continue
        if in_source_events and raw_line.startswith("      - "):
            current.source_events.append(raw_line.split("-", 1)[1].strip())
            continue
        in_source_events = False

        if stripped.startswith("target_file:"):
            current.target_file = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("proposed_change:"):
            current.proposed_change = stripped.split(":", 1)[1].strip().strip('"')
        elif stripped.startswith("confidence:"):
            try:
                current.confidence = float(stripped.split(":", 1)[1].strip())
            except ValueError:
                current.confidence = 0.0
        elif stripped.startswith("class:"):
            current.class_name = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("status:"):
            current.status = stripped.split(":", 1)[1].strip()

    flush()
    return candidates


def load_candidates(date_filter: str) -> list[Candidate]:
    queued: list[Candidate] = []
    for path in candidate_files(date_filter):
        for candidate in parse_candidate_file(path):
            if candidate.status == "queued":
                queued.append(candidate)
    return queued


def load_event_index() -> dict[str, dict]:
    events: dict[str, dict] = {}
    for path in sorted(EVENTS_DIR.glob("*.ndjson")):
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            event_id = str(event.get("id", "")).strip()
            if event_id:
                events[event_id] = event
    return events


def run_review_update(candidate: Candidate, status: str, reviewer: str, notes: str) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(REVIEW_SCRIPT),
        "--id",
        candidate.id,
        "--status",
        status,
        "--reviewer",
        reviewer,
        "--notes",
        notes,
        "--date",
        candidate.date,
    ]
    return subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)


def show_source_events(candidate: Candidate, event_index: dict[str, dict]) -> None:
    print()
    print("Source Events")
    print("-------------")
    if not candidate.source_events:
        print("No source events attached.")
        print()
        return

    for idx, event_id in enumerate(candidate.source_events, 1):
        event = event_index.get(event_id)
        if not event:
            print(f"{idx}. {event_id} (not found in _runtime/events)")
            continue
        print(
            f"{idx}. {event_id} [{event.get('type', 'event')}] "
            f"{event.get('ts_utc', '-')} {event.get('agent', '-')}"
        )
        print(f"   project: {event.get('project', '-')}")
        print(f"   summary: {event.get('summary', '').strip()}")
    print()


def maybe_run_propose_patches(approved_dates: set[str]) -> None:
    if not approved_dates:
        return
    answer = input("Run propose_patches.py for approved dates? [y/N]: ").strip().lower()
    if answer not in {"y", "yes"}:
        return

    for date_str in sorted(approved_dates):
        cmd = [sys.executable, str(PROPOSE_PATCHES_SCRIPT), "--date", date_str]
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        if proc.stdout.strip():
            print(proc.stdout.strip())
        if proc.returncode != 0 and proc.stderr.strip():
            print(proc.stderr.strip(), file=sys.stderr)


def main() -> int:
    args = parse_args()
    candidates = load_candidates(args.date)
    if not candidates:
        target = f" for {args.date}" if args.date else ""
        print(f"No queued candidates found{target}.")
        return 0

    event_index = load_event_index()
    total = len(candidates)
    approved = 0
    rejected = 0
    skipped = 0
    approved_dates: set[str] = set()

    idx = 0
    while idx < total:
        candidate = candidates[idx]
        print()
        print(f"[{idx + 1}/{total} queued — {approved} approved, {rejected} rejected]")
        print(f"Candidate: {candidate.id}")
        print(f"  Target: {candidate.target_file or '-'}")
        print(f"  Change: {candidate.proposed_change or '-'}")
        print(
            f"  Confidence: {candidate.confidence:.2f}  "
            f"Class: {candidate.class_name or '-'}  "
            f"Source: {len(candidate.source_events)} event(s)"
        )

        while True:
            action = input("  [a]pprove / [r]eject / [s]kip / [?]events / [q]uit: ").strip().lower()
            if action in {"?", "events"}:
                show_source_events(candidate, event_index)
                continue
            if action in {"s", "skip"}:
                skipped += 1
                idx += 1
                break
            if action in {"q", "quit"}:
                idx = total
                break
            if action in {"a", "approve", "r", "reject"}:
                status = "approved" if action.startswith("a") else "rejected"
                notes = input("  Notes (optional): ").strip()
                proc = run_review_update(candidate, status, args.reviewer, notes)
                if proc.stdout.strip():
                    print(proc.stdout.strip())
                if proc.returncode != 0:
                    if proc.stderr.strip():
                        print(proc.stderr.strip(), file=sys.stderr)
                    return proc.returncode
                if status == "approved":
                    approved += 1
                    approved_dates.add(candidate.date)
                else:
                    rejected += 1
                idx += 1
                break
            print("  Enter a, r, s, ?, or q.")

    print()
    print("Review Summary")
    print("--------------")
    print(f"Queued total: {total}")
    print(f"Approved: {approved}")
    print(f"Rejected: {rejected}")
    print(f"Skipped: {skipped}")
    print(f"Reviewed this pass: {approved + rejected}")
    maybe_run_propose_patches(approved_dates)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
