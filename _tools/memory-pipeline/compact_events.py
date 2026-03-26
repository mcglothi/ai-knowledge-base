#!/usr/bin/env python3
"""Compact historical runtime event logs into monthly summaries and optional gzip archives."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--older-than-days", type=int, default=21)
    p.add_argument("--max-files", type=int, default=20)
    p.add_argument("--archive-raw", action="store_true", help="Move compacted ndjson files to _runtime/events/archive/*.ndjson.gz")
    return p.parse_args()


def parse_event_date(path: Path) -> datetime | None:
    try:
        return datetime.strptime(path.stem, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    events_dir = root / "_runtime" / "events"
    compact_dir = events_dir / "compacted"
    archive_dir = events_dir / "archive"

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max(1, args.older_than_days))

    targets: list[Path] = []
    for f in sorted(events_dir.glob("*.ndjson")):
        dt = parse_event_date(f)
        if not dt:
            continue
        if dt <= cutoff:
            targets.append(f)

    if args.max_files > 0:
        targets = targets[: args.max_files]

    if not targets:
        print("No event files eligible for compaction.")
        return 0

    compact_dir.mkdir(parents=True, exist_ok=True)
    if args.archive_raw:
        archive_dir.mkdir(parents=True, exist_ok=True)

    for f in targets:
        events = []
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        by_project = Counter(e.get("project", "unknown") for e in events)
        by_type = Counter(e.get("type", "unknown") for e in events)
        highlights = defaultdict(list)

        for e in events:
            project = e.get("project", "unknown")
            summary = (e.get("summary", "") or "").strip()
            if summary and len(highlights[project]) < 3:
                highlights[project].append(summary)

        payload = {
            "source_file": str(f.relative_to(root)),
            "compacted_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event_count": len(events),
            "projects": dict(by_project),
            "types": dict(by_type),
            "highlights": dict(highlights),
        }

        compact_path = compact_dir / f"{f.stem}.json"
        compact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        if args.archive_raw:
            gz_path = archive_dir / f"{f.stem}.ndjson.gz"
            with gzip.open(gz_path, "wt", encoding="utf-8") as gz:
                gz.write(f.read_text(encoding="utf-8"))
            f.unlink()

        print(f"Compacted {f.name} -> {compact_path.relative_to(root)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
