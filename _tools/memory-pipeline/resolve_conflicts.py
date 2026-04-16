#!/usr/bin/env python3
"""Resolve runtime conflict records by id and sync status/notes in-place."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path

VALID_STATUS = {"open", "resolved", "ignored"}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--id", required=True, help="Conflict id (e.g. conf_20260304_001)")
    p.add_argument("--status", required=True, choices=sorted(VALID_STATUS))
    p.add_argument("--reviewer", default="", help="Reviewer handle/name")
    p.add_argument("--notes", default="", help="Resolution notes")
    p.add_argument("--date", help="Conflict file date (YYYY-MM-DD). Inferred from id if omitted.")
    return p.parse_args()


def infer_date(conflict_id: str) -> str:
    m = re.match(r"^conf_(\d{4})(\d{2})(\d{2})_", conflict_id)
    if not m:
        raise SystemExit("Could not infer date from conflict id; pass --date YYYY-MM-DD.")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


def upsert_field(block_lines: list[str], field: str, value: str, indent: str = "    ") -> list[str]:
    key = f"{indent}{field}:"
    for i, line in enumerate(block_lines):
        if line.startswith(key):
            block_lines[i] = f'{key} "{value}"'
            return block_lines

    # Insert after status when possible, else append
    insert_at = len(block_lines)
    for i, line in enumerate(block_lines):
        if line.startswith(f"{indent}status:"):
            insert_at = i + 1
            break
    block_lines.insert(insert_at, f'{key} "{value}"')
    return block_lines


def update_conflict_file(path: Path, conflict_id: str, status: str, reviewer: str, notes: str) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines()
    start = None
    end = None

    for i, line in enumerate(lines):
        if line.strip() == f"- id: {conflict_id}" or line.strip() == f"id: {conflict_id}":
            start = i
            break
    if start is None:
        return False

    for j in range(start + 1, len(lines)):
        if lines[j].startswith("  - id:"):
            end = j
            break
    if end is None:
        end = len(lines)

    block = lines[start:end]
    status_updated = False
    for i, line in enumerate(block):
        if line.startswith("    status:"):
            block[i] = f"    status: {status}"
            status_updated = True
            break
    if not status_updated:
        block = upsert_field(block, "status", status, indent="    ")

    if reviewer:
        block = upsert_field(block, "reviewer", reviewer, indent="    ")
    if notes:
        block = upsert_field(block, "resolution_note", notes, indent="    ")
        block = upsert_field(
            block,
            "resolved_at",
            dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            indent="    ",
        )

    lines = lines[:start] + block + lines[end:]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def main() -> int:
    args = parse_args()
    date_str = args.date or infer_date(args.id)
    root = Path(__file__).resolve().parents[2]
    conflicts_file = root / "_runtime" / "conflicts" / f"{date_str}.yaml"

    if not conflicts_file.exists():
        raise SystemExit(f"Conflict file not found: {conflicts_file}")

    ok = update_conflict_file(conflicts_file, args.id, args.status, args.reviewer, args.notes)
    if not ok:
        raise SystemExit(f"Conflict id not found: {args.id}")

    print(
        f"Updated {args.id}: status={args.status}, reviewer={args.reviewer or '-'}, notes={args.notes or '-'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
