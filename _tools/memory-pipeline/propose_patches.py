#!/usr/bin/env python3
"""Create markdown patch proposal draft from queued candidates."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", help="Date to read candidate file (YYYY-MM-DD). Defaults to today UTC.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    root = Path(__file__).resolve().parents[2]
    candidates_file = root / "_runtime" / "candidates" / f"{date_str}.yaml"
    if not candidates_file.exists():
        raise SystemExit(f"No candidate file found: {candidates_file}")

    proposal_file = root / "_runtime" / f"patch-proposals-{date_str}.md"
    content = [
        "# Patch Proposals",
        "",
        f"**Last Updated:** {date_str}",
        "**Summary:** Draft patch proposals generated from queued runtime memory candidates.",
        "",
        "---",
        "",
        "## Source",
        "",
        f"- Candidate file: `{candidates_file.relative_to(root)}`",
        "",
        "## Proposed Changes",
        "",
        "Review candidate YAML and convert approved items into concrete edits against target files.",
        "",
    ]
    proposal_file.write_text("\n".join(content), encoding="utf-8")
    print(f"Wrote proposal scaffold to {proposal_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
