#!/usr/bin/env python3
"""Review a runtime candidate and sync status into YAML + promotion queue."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


VALID_STATUS = {"queued", "approved", "rejected", "merged"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True, help="Candidate id (e.g. cand_20260304_001)")
    parser.add_argument("--status", required=True, choices=sorted(VALID_STATUS))
    parser.add_argument("--reviewer", default="", help="Reviewer handle/name")
    parser.add_argument("--notes", default="", help="Short decision notes")
    parser.add_argument(
        "--date",
        help="Candidate file date (YYYY-MM-DD). If omitted, inferred from candidate id.",
    )
    return parser.parse_args()


def infer_date(candidate_id: str) -> str:
    m = re.match(r"^cand_(\d{4})(\d{2})(\d{2})_", candidate_id)
    if not m:
        raise SystemExit("Could not infer date from candidate id; pass --date YYYY-MM-DD.")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


def update_candidate_yaml(path: Path, candidate_id: str, status: str) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines()
    found = False
    in_block = False

    for idx, line in enumerate(lines):
        if line.strip() == f"- id: {candidate_id}" or line.strip() == f"id: {candidate_id}":
            in_block = True
            found = True
            continue
        if in_block and line.startswith("  - id:"):
            in_block = False
        if in_block and line.strip().startswith("status:"):
            indent = line[: len(line) - len(line.lstrip())]
            lines[idx] = f"{indent}status: {status}"
            in_block = False
            break

    if not found:
        return False

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def update_queue_md(
    path: Path, candidate_id: str, status: str, reviewer: str, notes: str, updated_date: str
) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines()
    found = False

    for idx, line in enumerate(lines):
        if not line.startswith("| "):
            continue
        cols = [c.strip() for c in line.strip().split("|")[1:-1]]
        if len(cols) != 7:
            continue
        if cols[0] != candidate_id:
            continue
        cols[4] = status
        cols[5] = reviewer
        cols[6] = notes
        lines[idx] = "| " + " | ".join(cols) + " |"
        found = True
        break

    if not found:
        return False

    # Refresh Last Updated stamp.
    for idx, line in enumerate(lines):
        if line.startswith("**Last Updated:**"):
            lines[idx] = f"**Last Updated:** {updated_date}"
            break

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def main() -> int:
    args = parse_args()
    date_str = args.date or infer_date(args.id)
    root = Path(__file__).resolve().parents[2]
    candidates_file = root / "_runtime" / "candidates" / f"{date_str}.yaml"
    queue_file = root / "_runtime" / "promotion-queue.md"

    if not candidates_file.exists():
        raise SystemExit(f"Candidate file not found: {candidates_file}")
    if not queue_file.exists():
        raise SystemExit(f"Queue file not found: {queue_file}")

    ok_yaml = update_candidate_yaml(candidates_file, args.id, args.status)
    if not ok_yaml:
        raise SystemExit(f"Candidate id not found in YAML: {args.id}")

    ok_queue = update_queue_md(
        queue_file,
        args.id,
        args.status,
        args.reviewer,
        args.notes,
        date_str,
    )
    if not ok_queue:
        raise SystemExit(f"Candidate id not found in queue: {args.id}")

    print(
        f"Updated {args.id}: status={args.status}, reviewer={args.reviewer or '-'}, notes={args.notes or '-'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
