#!/usr/bin/env python3
# Last Updated: 2026-10-29
"""Generate daily candidate YAML from runtime events and update promotion queue."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from promotion_gate import judge_batch  # noqa: E402
from event_inputs import load_events

# One definition of "not a memory", shared with dream_cycle. Re-exported here so
# existing callers and tests keep working.
from noise_filters import TELEMETRY_TYPES, unwrap_summary  # noqa: E402,F401


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", help="Date to process (YYYY-MM-DD). Defaults to today UTC.")
    parser.add_argument(
        "--no-gate",
        action="store_true",
        help="Skip local-LLM scoring; candidates are written ungated.",
    )
    parser.add_argument(
        "--no-fact-extraction",
        action="store_true",
        help=argparse.SUPPRESS,  # deprecated no-op, see note below
    )
    return parser.parse_args()


def score_candidate(event: dict) -> tuple[str, float]:
    if event.get("sensitivity") == "restricted":
        return ("needs-review", 0.5)
    if event.get("type") == "change":
        return ("auto-promote-safe", 0.9)
    if event.get("type") in {"decision", "blocker"}:
        return ("needs-review", 0.85)
    return ("needs-review", 0.7)



def resolve_target(root: Path, raw: str) -> tuple[str, bool]:
    """Map an event's free-text `project` onto a real AIKB file.

    Events carry whatever string the emitting agent felt like using -- "AIKB",
    "runway", "/home/user/code", "merge". 53% of historical candidates named
    a target that does not exist, so the reviewer could not act on them without
    first working out where they belonged. Unroutable candidates are kept but
    flagged, never silently pointed at a fabricated path.
    """
    raw = (raw or "").strip()
    if not raw:
        return "", False
    if (root / raw).is_file():
        return raw, True
    # A bare doc name ("runway", "unmanic") is routable when exactly one
    # canonical file matches it; anything ambiguous stays unrouted.
    stem = Path(raw).stem.lower()
    if stem:
        matches = [
            p.relative_to(root).as_posix()
            for p in root.rglob(f"{stem}.md")
            if "_runtime" not in p.parts and ".git" not in p.parts
        ]
        if len(matches) == 1:
            return matches[0], True
    return raw, False


def to_yaml(candidates: list[dict]) -> str:
    import yaml
    return yaml.safe_dump({"candidates": candidates}, sort_keys=False, allow_unicode=True)


def load_existing_candidates(path: Path) -> list[dict]:
    """Candidates already written for this date, including operator edits."""
    if not path.exists():
        return []
    import yaml
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = data.get("candidates") if isinstance(data, dict) else data
    return [c for c in (items or []) if isinstance(c, dict) and c.get("id")]


def merge_candidates(existing: list[dict], generated: list[dict]) -> tuple[list[dict], list[dict]]:
    """Append-only merge of a regenerated day into what is already on disk.

    Re-running a date (a nightly host job reprocesses any date whose event inputs changed,
    e.g. a late session-stop upload) used to rewrite the whole YAML with every
    status reset to "queued", silently undoing operator reviews. Existing
    entries are now kept verbatim -- status, gate verdict and any manual fields
    -- and only their source_events list may grow. Returns (merged, fresh).
    """
    by_id = {c["id"]: c for c in existing}
    fresh = []
    for cand in generated:
        old = by_id.get(cand["id"])
        if old is None:
            fresh.append(cand)
            continue
        events = list(old.get("source_events") or [])
        events += [e for e in cand.get("source_events", []) if e not in events]
        old["source_events"] = events
    return existing + fresh, fresh


def existing_candidate_ids(queue_text: str) -> set[str]:
    """Candidate IDs already present in the queue, in any status."""
    ids = set()
    for line in queue_text.splitlines():
        if not line.startswith("| cand_"):
            continue
        ids.add(line.split("|")[1].strip())
    return ids


def add_queue_rows(queue_text: str, candidates: list[dict]) -> tuple[str, int]:
    """Insert queue rows, skipping candidates already tracked.

    Re-running for a date used to append a fresh row every time regardless of
    what was already there. 443 of the queue's 521 rejections were duplicate
    insertions the operator then had to close out by hand -- a bookkeeping
    artefact, not a judgement about any candidate.
    """
    known = existing_candidate_ids(queue_text)
    fresh = [c for c in candidates if c["id"] not in known]
    if not fresh:
        return queue_text, 0

    rows = "\n".join(
        f"| {c['id']} | {c['target_file']} | {c['class']} | {c['confidence']:.2f} | queued |  | "
        f"{c.get('gate_verdict', 'ungated')}: {(c.get('gate_reason') or '').replace('|', '/')[:110]} |"
        for c in fresh
    )
    marker = "|--------------|-------------|-------|------------|--------|----------|-------|"
    if marker in queue_text:
        return queue_text.replace(marker, marker + f"\n{rows}\n", 1), len(fresh)
    return queue_text, 0


def main() -> int:
    args = parse_args()
    if args.no_fact_extraction:
        # Kept so existing callers do not break. The preference extractor it
        # used to disable has been removed: it matched any summary containing
        # "always", "never", "use" or "avoid" and copied the whole operational
        # change into personal/profile.md as a "user preference". Across the
        # entire queue history it produced zero merges and a steady stream of
        # rows the operator closed as "False preference copy".
        print("build_candidates: --no-fact-extraction is a no-op (extractor removed).")

    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    root = Path(__file__).resolve().parents[2]
    events = load_events(root, date_str)

    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    telemetry_skipped = 0
    for evt in events:
        if evt.get("type") in TELEMETRY_TYPES:
            telemetry_skipped += 1
            continue
        if evt.get("promote_hint") != "candidate":
            continue
        key = (evt.get("project", "unknown"), evt.get("type", "observation"),
               unwrap_summary(evt.get("summary", "") or ""))
        grouped[key].append(evt)

    candidates = []
    counter = 1
    seen_changes: set[str] = set()
    unrouted = 0
    bookkeeping_skipped = 0

    for (raw_target, evt_type, _summary), bucket in grouped.items():
        class_name, confidence = score_candidate(bucket[-1])
        summary = unwrap_summary(bucket[-1].get("summary", "") or "")
        if not summary:
            bookkeeping_skipped += 1
            continue
        proposed_change = f"[{evt_type}] {summary}".strip()
        target_file, routed = resolve_target(root, raw_target)
        if not routed:
            class_name = "needs-routing"
            unrouted += 1

        key = f"{target_file}|{proposed_change}".lower()
        if key in seen_changes:
            continue

        candidates.append(
            {
                "id": f"cand_{date_str.replace('-', '')}_{hashlib.sha256(key.encode()).hexdigest()[:12]}",
                "source_events": [e["id"] for e in bucket if e.get("id")],
                "target_file": target_file,
                "proposed_change": proposed_change,
                "confidence": confidence,
                "class": class_name,
                "status": "queued",
            }
        )
        seen_changes.add(key)
        counter += 1

    # Local-LLM gate. Advisory only: it annotates every candidate with a verdict
    # and a reason so the queue arrives sorted, and drops nothing. Measured
    # drop-precision is ~98%, which still loses roughly 1 keeper in 50 -- not a
    # trade worth making automatically while the eval set is n=85.
    out_yaml = root / "_runtime" / "candidates" / f"{date_str}.yaml"
    candidates, fresh = merge_candidates(load_existing_candidates(out_yaml), candidates)

    gate_model = None
    if fresh and not args.no_gate:
        verdicts, gate_model = judge_batch(
            [(c["target_file"], c["proposed_change"]) for c in fresh]
        )
        for cand, (verdict, reason) in zip(fresh, verdicts):
            cand["gate_verdict"] = verdict
            cand["gate_reason"] = reason
        if os.environ.get("AIKB_REQUIRE_MODEL") == "1" and (
            len(verdicts) != len(fresh) or any(v not in ("merge", "reject") for v, _ in verdicts)
        ):
            raise RuntimeError("Required local promotion gate did not score every candidate")
        fresh.sort(key=lambda c: {"merge": 0, "ungated": 1, "reject": 2}.get(c["gate_verdict"], 1))
        candidates = candidates[: len(candidates) - len(fresh)] + fresh

    out_yaml.parent.mkdir(parents=True, exist_ok=True)
    out_yaml.write_text(to_yaml(candidates), encoding="utf-8")

    added = 0
    queue = root / "_runtime" / "promotion-queue.md"
    if queue.exists() and candidates:
        queue_text = queue.read_text(encoding="utf-8")
        queue_text, added = add_queue_rows(queue_text, candidates)
        queue.write_text(queue_text, encoding="utf-8")

    print(f"Wrote {len(candidates)} candidates to {out_yaml} ({len(fresh)} new, existing statuses preserved)")
    print(f"  telemetry events skipped: {telemetry_skipped}")
    if bookkeeping_skipped:
        print(f"  note-less closeouts:      {bookkeeping_skipped} (pure bookkeeping)")
    if unrouted:
        print(f"  unroutable target_file:   {unrouted} (class=needs-routing)")
    if gate_model:
        kept = sum(1 for c in fresh if c.get("gate_verdict") == "merge")
        print(f"  gate ({gate_model}): {kept} merge / {len(fresh) - kept} reject-or-ungated")
    print(f"  queue rows added:         {added} ({len(candidates) - added} already tracked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
