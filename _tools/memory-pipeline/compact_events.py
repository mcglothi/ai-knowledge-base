#!/usr/bin/env python3
"""Compact historical runtime event logs into monthly summaries and optional gzip archives."""

from __future__ import annotations

import argparse
import gzip
import json
import re
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


# Observation extraction (v2): dated fact lists per (project, type), inspired
# by Mastra's Observational Memory — structured dated facts survive compaction
# where prose highlights lose the specifics.

OBSERVATION_TYPES = ("decision", "blocker", "change", "observation")
MAX_FACTS_PER_GROUP = 8
MAX_EVIDENCE_PER_GROUP = 3

# Volatile substrings stripped before dedupe so "backup at 03:12:44 ok" and
# "backup at 03:12:45 ok" collapse into one fact.
_NORMALIZE_STRIP = re.compile(
    r"\d{4}-\d{2}-\d{2}[t ]?\d{2}:\d{2}(:\d{2})?(z|[+-]\d{2}:?\d{2})?"  # timestamps
    r"|\b[0-9a-f]{7,40}\b"                                              # hashes
    r"|\d{2}:\d{2}(:\d{2})?"                                            # times
    r"|\(\d+(\.\d+)?s\)"                                                # durations
    r"|\b\d+\b"                                                         # counters
)
_WS = re.compile(r"\s+")


def _normalize_summary(summary: str) -> str:
    text = _NORMALIZE_STRIP.sub("", summary.lower())
    return _WS.sub(" ", text).strip()


def build_observations(events: list[dict], date_str: str) -> tuple[list[dict], dict[str, int]]:
    """
    Group events into dated observation records:
        {date, project, type, facts[], evidence[], dropped}
    Deterministic: dedupe on normalized summary keeping first occurrence in
    timestamp order, cap facts per group. Non-observation types (quota
    snapshots, shell-hook floods) are counted in stats, not summarized.
    """
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    skipped: Counter = Counter()

    for e in sorted(events, key=lambda ev: ev.get("ts_utc", "")):
        etype = e.get("type", "unknown")
        if etype not in OBSERVATION_TYPES:
            skipped[etype] += 1
            continue
        project = e.get("project", "unknown") or "unknown"
        groups[(project, etype)].append(e)

    observations = []
    for (project, etype), group_events in sorted(groups.items()):
        facts: list[str] = []
        evidence: list[str] = []
        seen: set[str] = set()
        dropped = 0
        for e in group_events:
            summary = (e.get("summary", "") or "").strip()
            if not summary:
                continue
            norm = _normalize_summary(summary)
            if not norm or norm in seen:
                dropped += 1
                continue
            seen.add(norm)
            if len(facts) >= MAX_FACTS_PER_GROUP:
                dropped += 1
                continue
            facts.append(summary)
            if len(evidence) < MAX_EVIDENCE_PER_GROUP:
                refs = e.get("evidence") or []
                evidence.append(refs[0] if refs else e.get("id", ""))
        if not facts:
            continue
        observations.append({
            "date": date_str,
            "project": project,
            "type": etype,
            "facts": facts,
            "evidence": [ev for ev in evidence if ev],
            "dropped": dropped,
        })

    return observations, dict(skipped)


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

        observations, skipped_stats = build_observations(events, f.stem)

        payload = {
            "version": 2,
            "source_file": str(f.relative_to(root)),
            "compacted_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event_count": len(events),
            "projects": dict(by_project),
            "types": dict(by_type),
            "highlights": dict(highlights),
            "observations": observations,
            "skipped_types": skipped_stats,
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
