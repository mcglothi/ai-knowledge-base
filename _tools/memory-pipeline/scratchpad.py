#!/usr/bin/env python3
"""Session scratchpads for mid-session ephemera (virtual RAM blocks)."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--session-id", default="")
    p.add_argument("--action", required=True, choices=["create", "append", "show", "list", "close"])
    p.add_argument("--title", default="Session Scratchpad")
    p.add_argument("--text", default="")
    p.add_argument("--ttl-hours", type=int, default=12)
    return p.parse_args()


def path_for(root: Path, session_id: str) -> Path:
    return root / "_runtime" / "scratchpads" / f"{session_id}.md"


def ensure_session_id(args: argparse.Namespace) -> str:
    sid = args.session_id.strip()
    if not sid and args.action != "list":
        raise SystemExit("--session-id is required for this action")
    return sid


def create_pad(path: Path, title: str, ttl_hours: int) -> None:
    now = datetime.now(timezone.utc)
    body = "\n".join(
        [
            f"# {title}",
            "",
            f"- session_id: `{path.stem}`",
            f"- opened_utc: `{now.strftime('%Y-%m-%dT%H:%M:%SZ')}`",
            f"- expires_utc: `{(now.timestamp() + ttl_hours * 3600):.0f}`",
            "",
            "## Notes",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body + "\n", encoding="utf-8")


def append_note(path: Path, text: str) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with path.open("a", encoding="utf-8") as f:
        f.write(f"- [{now}] {text}\n")


def close_pad(path: Path) -> Path:
    archive = path.parent / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    dst = archive / path.name
    path.replace(dst)
    return dst


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    sid = ensure_session_id(args)

    if args.action == "list":
        folder = root / "_runtime" / "scratchpads"
        if not folder.exists():
            print("No scratchpads yet.")
            return 0
        for f in sorted(folder.glob("*.md")):
            print(f.name)
        return 0

    pad = path_for(root, sid)

    if args.action == "create":
        create_pad(pad, args.title, args.ttl_hours)
        print(f"Created scratchpad: {pad}")
        return 0

    if not pad.exists() and args.action in {"append", "show", "close"}:
        raise SystemExit(f"Scratchpad not found: {pad}")

    if args.action == "append":
        if not args.text.strip():
            raise SystemExit("--text is required for append")
        append_note(pad, args.text.strip())
        print(f"Updated scratchpad: {pad}")
        return 0

    if args.action == "show":
        print(pad.read_text(encoding="utf-8"))
        return 0

    if args.action == "close":
        dst = close_pad(pad)
        print(f"Archived scratchpad: {dst}")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
