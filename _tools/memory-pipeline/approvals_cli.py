#!/usr/bin/env python3
"""Manage AIKB pending approvals stored in _pending_approvals.md."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APPROVALS_FILE = ROOT / "_pending_approvals.md"
HEADER_ROW = "| Date | Agent | Project | Action/Decision | Status | Notes |"
SEPARATOR_ROW = "| :--- | :--- | :--- | :--- | :--- | :--- |"


@dataclass
class ApprovalRow:
    date: str
    agent: str
    project: str
    action: str
    status: str
    notes: str

    def to_markdown(self) -> str:
        return (
            f"| {self.date} | {self.agent} | {self.project} | "
            f"{self.action} | {self.status} | {self.notes} |"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    add = subparsers.add_parser("add", help="Add a new approval row.")
    add.add_argument("--agent", required=True)
    add.add_argument("--project", required=True)
    add.add_argument("--action", required=True)
    add.add_argument("--notes", default="")
    add.add_argument("--status", default="Pending")
    add.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))

    list_cmd = subparsers.add_parser("list", help="List approvals.")
    list_cmd.add_argument("--status", default="", help="Filter by status (case-insensitive).")
    list_cmd.add_argument("--limit", type=int, default=20)

    resolve = subparsers.add_parser("resolve", help="Resolve an approval row by its table index.")
    resolve.add_argument("--index", type=int, required=True, help="1-based row index from `list`.")
    resolve.add_argument("--status", required=True, help="New status, e.g. Approved or Rejected.")
    resolve.add_argument("--notes", default="", help="Replacement notes or appended detail.")

    return parser.parse_args()


def load_lines() -> list[str]:
    if not APPROVALS_FILE.exists():
        raise SystemExit(f"Approvals file not found: {APPROVALS_FILE}")
    return APPROVALS_FILE.read_text(encoding="utf-8").splitlines()


def save_lines(lines: list[str]) -> None:
    APPROVALS_FILE.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def parse_rows(lines: list[str]) -> tuple[list[ApprovalRow], dict[int, int]]:
    rows: list[ApprovalRow] = []
    line_map: dict[int, int] = {}
    row_index = 0
    for lineno, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if stripped in {HEADER_ROW, SEPARATOR_ROW}:
            continue
        parts = [part.strip() for part in stripped.strip("|").split("|")]
        if len(parts) != 6:
            continue
        if all(set(part) <= {":", "-", " "} for part in parts):
            continue
        row_index += 1
        rows.append(
            ApprovalRow(
                date=parts[0],
                agent=parts[1],
                project=parts[2],
                action=parts[3],
                status=parts[4],
                notes=parts[5],
            )
        )
        line_map[row_index] = lineno
    return rows, line_map


def find_insert_index(lines: list[str]) -> int:
    for idx, line in enumerate(lines):
        if line.strip() == SEPARATOR_ROW:
            return idx + 1
    raise SystemExit("Could not find approvals table separator row.")


def update_last_updated(lines: list[str], date_str: str) -> list[str]:
    updated: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith("**Last Updated:**"):
            updated.append(f"**Last Updated:** {date_str}")
            replaced = True
        else:
            updated.append(line)
    if not replaced:
        updated.insert(1, f"**Last Updated:** {date_str}")
    return updated


def run_add(args: argparse.Namespace) -> int:
    lines = load_lines()
    insert_at = find_insert_index(lines)
    row = ApprovalRow(
        date=args.date,
        agent=args.agent.strip(),
        project=args.project.strip(),
        action=args.action.strip(),
        status=args.status.strip(),
        notes=args.notes.strip(),
    )
    lines.insert(insert_at, row.to_markdown())
    lines = update_last_updated(lines, args.date)
    save_lines(lines)
    print(f"[approvals] added: {row.action}")
    return 0


def matches_status(row: ApprovalRow, desired: str) -> bool:
    if not desired:
        return True
    return row.status.strip().lower() == desired.strip().lower()


def run_list(args: argparse.Namespace) -> int:
    rows, _ = parse_rows(load_lines())
    filtered = [row for row in rows if matches_status(row, args.status)]
    if not filtered:
        print("[approvals] no matching rows")
        return 0
    for idx, row in enumerate(filtered[: args.limit], 1):
        print(
            f"{idx}. [{row.status}] {row.date} | {row.project} | {row.agent} | "
            f"{row.action}" + (f" | {row.notes}" if row.notes else "")
        )
    return 0


def run_resolve(args: argparse.Namespace) -> int:
    lines = load_lines()
    rows, line_map = parse_rows(lines)
    if args.index < 1 or args.index > len(rows):
        raise SystemExit(f"Approval index out of range: {args.index}")
    row = rows[args.index - 1]
    notes = args.notes.strip()
    if notes:
        if row.notes and row.notes != notes:
            row.notes = f"{row.notes}; {notes}"
        else:
            row.notes = notes
    row.status = args.status.strip()
    lines[line_map[args.index]] = row.to_markdown()
    lines = update_last_updated(lines, datetime.now().strftime("%Y-%m-%d"))
    save_lines(lines)
    print(f"[approvals] resolved row {args.index} -> {row.status}")
    return 0


def main() -> int:
    args = parse_args()
    if args.command == "add":
        return run_add(args)
    if args.command == "list":
        return run_list(args)
    if args.command == "resolve":
        return run_resolve(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
