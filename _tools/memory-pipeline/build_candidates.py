#!/usr/bin/env python3
"""Generate daily candidate YAML from runtime events and update promotion queue."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PREF_PATTERNS = [
    re.compile(r"\b(prefer|preferred|preference)\b", re.IGNORECASE),
    re.compile(r"\b(default to|defaults to)\b", re.IGNORECASE),
    re.compile(r"\b(always|never)\b", re.IGNORECASE),
    re.compile(r"\b(wants?|likes?|dislikes?)\b", re.IGNORECASE),
    re.compile(r"\b(avoid|use)\b", re.IGNORECASE),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", help="Date to process (YYYY-MM-DD). Defaults to today UTC.")
    parser.add_argument("--no-fact-extraction", action="store_true", help="Disable user preference fact extraction")
    return parser.parse_args()


def score_candidate(event: dict) -> tuple[str, float]:
    if event.get("sensitivity") == "restricted":
        return ("needs-review", 0.5)
    if event.get("type") == "change":
        return ("auto-promote-safe", 0.9)
    if event.get("type") in {"decision", "blocker"}:
        return ("needs-review", 0.85)
    return ("needs-review", 0.7)


def has_preference_signal(summary: str) -> bool:
    s = summary.strip()
    if len(s) < 12:
        return False
    return any(p.search(s) for p in PREF_PATTERNS)


def preference_confidence(summary: str) -> float:
    score = 0.62
    for pat in PREF_PATTERNS:
        if pat.search(summary):
            score += 0.07
    return min(0.93, score)


def to_yaml(candidates: list[dict]) -> str:
    lines = ["candidates:"]
    for c in candidates:
        lines.append(f"  - id: {c['id']}")
        lines.append("    source_events:")
        for evt_id in c["source_events"]:
            lines.append(f"      - {evt_id}")
        lines.append(f"    target_file: {c['target_file']}")
        lines.append(f"    proposed_change: \"{c['proposed_change'].replace('"', '\\"')}\"")
        lines.append(f"    confidence: {c['confidence']:.2f}")
        lines.append(f"    class: {c['class']}")
        lines.append(f"    status: {c['status']}")
    return "\n".join(lines) + "\n"


def add_queue_rows(queue_text: str, candidates: list[dict]) -> str:
    rows = "\n".join(
        f"| {c['id']} | {c['target_file']} | {c['class']} | {c['confidence']:.2f} | queued |  |  |"
        for c in candidates
    )
    insertion = f"\n{rows}\n"
    marker = "|--------------|-------------|-------|------------|--------|----------|-------|"
    if marker in queue_text:
        return queue_text.replace(marker, marker + insertion, 1)
    return queue_text


def main() -> int:
    args = parse_args()
    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    root = Path(__file__).resolve().parents[2]
    events_file = root / "_runtime" / "events" / f"{date_str}.ndjson"
    if not events_file.exists():
        print(f"No events file found: {events_file}")
        return 0

    events = []
    with events_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))

    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for evt in events:
        if evt.get("promote_hint") != "candidate":
            continue
        key = (evt.get("project", "unknown"), evt.get("type", "observation"))
        grouped[key].append(evt)

    candidates = []
    counter = 1
    seen_changes: set[str] = set()

    for (target_file, evt_type), bucket in grouped.items():
        class_name, confidence = score_candidate(bucket[-1])
        summary = bucket[-1].get("summary", "")
        proposed_change = f"[{evt_type}] {summary}".strip()
        key = f"{target_file}|{proposed_change}".lower()
        if key in seen_changes:
            continue

        candidates.append(
            {
                "id": f"cand_{date_str.replace('-', '')}_{counter:03d}",
                "source_events": [e["id"] for e in bucket],
                "target_file": target_file,
                "proposed_change": proposed_change,
                "confidence": confidence,
                "class": class_name,
                "status": "queued",
            }
        )
        seen_changes.add(key)
        counter += 1

    # Automated fact extraction: preference capture from runtime summaries.
    if not args.no_fact_extraction:
        for evt in events:
            summary = (evt.get("summary", "") or "").strip()
            if not has_preference_signal(summary):
                continue

            proposed_change = f"[preference] User preference observed: {summary}"
            key = f"personal/profile.md|{proposed_change}".lower()
            if key in seen_changes:
                continue

            evt_id = evt.get("id", "")
            candidates.append(
                {
                    "id": f"cand_{date_str.replace('-', '')}_{counter:03d}",
                    "source_events": [evt_id] if evt_id else [],
                    "target_file": "personal/profile.md",
                    "proposed_change": proposed_change,
                    "confidence": preference_confidence(summary),
                    "class": "needs-review",
                    "status": "queued",
                }
            )
            seen_changes.add(key)
            counter += 1

    out_yaml = root / "_runtime" / "candidates" / f"{date_str}.yaml"
    out_yaml.parent.mkdir(parents=True, exist_ok=True)
    out_yaml.write_text(to_yaml(candidates), encoding="utf-8")

    queue = root / "_runtime" / "promotion-queue.md"
    if queue.exists() and candidates:
        queue_text = queue.read_text(encoding="utf-8")
        queue.write_text(add_queue_rows(queue_text, candidates), encoding="utf-8")

    print(f"Wrote {len(candidates)} candidates to {out_yaml}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
