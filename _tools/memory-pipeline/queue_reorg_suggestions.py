#!/usr/bin/env python3
"""Sync latest autonomous reorg suggestions into _runtime/promotion-queue.md."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

SECTION_START = "## Autonomous Reorg Queue"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", default="", help="Path to reorg suggestions JSON. Defaults to latest in _runtime/reorg-suggestions/")
    p.add_argument("--queue", default="", help="Override promotion queue path")
    return p.parse_args()


def latest_reorg_file(root: Path) -> Path:
    folder = root / "_runtime" / "reorg-suggestions"
    files = sorted(folder.glob("*.json"))
    if not files:
        raise SystemExit(f"No reorg suggestions found in {folder}")
    return files[-1]


def build_rows(suggestions: list[dict]) -> list[str]:
    rows = [
        "| Reorg ID | Type | Confidence | Target | Status | Notes |",
        "|----------|------|------------|--------|--------|-------|",
    ]

    for i, s in enumerate(suggestions, 1):
        sid = f"reorg_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{i:03d}"
        stype = s.get("type", "unknown")
        conf = f"{float(s.get('confidence', 0.0)):.2f}"
        target = "-"
        if s.get("target"):
            target = s["target"].get("path", "-")
        elif s.get("left") and s.get("right"):
            target = f"{s['left'].get('path', '-') } <-> {s['right'].get('path', '-') }"
        notes = s.get("reason", "")[:120].replace("|", "/")
        rows.append(f"| {sid} | {stype} | {conf} | {target} | queued | {notes} |")

    return rows


def upsert_section(queue_path: Path, section_body: str) -> None:
    if queue_path.exists():
        text = queue_path.read_text(encoding="utf-8")
    else:
        text = (
            "# Runtime Promotion Queue\n\n"
            f"**Last Updated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n"
            "**Summary:** Manual approval and merge tracking for promoting runtime memory candidates into canonical AIKB files.\n\n"
        )

    if SECTION_START in text:
        before, rest = text.split(SECTION_START, 1)
        marker = "\n## "
        idx = rest.find(marker)
        if idx == -1:
            after = ""
        else:
            after = rest[idx:]
        text = before.rstrip() + "\n\n" + SECTION_START + "\n\n" + section_body + "\n" + after
    else:
        text = text.rstrip() + "\n\n" + SECTION_START + "\n\n" + section_body + "\n"

    queue_path.write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]

    reorg_file = Path(args.input) if args.input else latest_reorg_file(root)
    queue_path = Path(args.queue) if args.queue else (root / "_runtime" / "promotion-queue.md")

    payload = json.loads(reorg_file.read_text(encoding="utf-8"))
    suggestions = payload.get("suggestions", [])

    rows = build_rows(suggestions)
    section_body = "\n".join(
        [
            f"- Source: `{reorg_file.relative_to(root)}`",
            f"- Generated: {payload.get('generated_at_utc', '-')}",
            "",
            *rows,
        ]
    )

    upsert_section(queue_path, section_body)
    print(f"Queued {len(suggestions)} reorg suggestion(s) into {queue_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
