#!/usr/bin/env python3
"""Scan runtime + canonical memory for potential contradictions."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

TOKEN_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_\-]{2,}")
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "your", "have",
    "about", "what", "when", "where", "which", "will", "been", "were", "their",
    "they", "them", "then", "than", "also", "only", "more", "most", "after",
    "before", "under", "over", "across", "using", "used", "use", "status", "file",
    "project", "memory", "runtime", "candidate", "canonical", "notes", "last", "updated",
    "summary", "purpose", "files", "readme", "index", "agents", "aikb", "2026-03-04",
    "2026-03-03", "2026-03-02", "2026-03-01", "----", "---",
}

MARKER_PATTERNS = {
    "activity": {
        "positive": re.compile(r"\b(active|enabled|healthy|running|live)\b"),
        "negative": re.compile(r"\b(inactive|disabled|decommissioned|stopped|offline)\b"),
    },
    "progress": {
        "positive": re.compile(r"\b(complete|completed|done|resolved|merged)\b"),
        "negative": re.compile(r"\b(pending|blocked|in\s+progress|in-progress|queued)\b"),
    },
    "access": {
        "positive": re.compile(r"\b(allow|allowed|permitted|authorized)\b"),
        "negative": re.compile(r"\b(deny|denied|forbidden|unauthorized)\b"),
    },
}


@dataclass
class MemoryItem:
    id: str
    source: str
    path: str
    text: str
    date: str
    anchor_path: str = ""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--date", help="Output date (YYYY-MM-DD). Defaults to today UTC.")
    p.add_argument("--scope", default="all", choices=["all", "runtime", "candidates", "canonical"])
    p.add_argument("--min-topic-overlap", type=int, default=2)
    p.add_argument("--include-rejected", action="store_true")
    p.add_argument("--limit", type=int, default=200)
    return p.parse_args()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def tokenize(text: str) -> set[str]:
    toks = {t.lower() for t in TOKEN_RE.findall(text.lower())}
    filtered: set[str] = set()
    for t in toks:
        if t in STOPWORDS:
            continue
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
            continue
        if re.fullmatch(r"-+", t):
            continue
        filtered.add(t)
    return filtered


def parse_candidate_file(f: Path, include_rejected: bool) -> list[MemoryItem]:
    lines = f.read_text(encoding="utf-8").splitlines()
    cur: dict[str, str] = {}
    out: list[MemoryItem] = []

    def flush() -> None:
        if not cur.get("id"):
            return
        if cur.get("status") == "rejected" and not include_rejected:
            return
        out.append(
            MemoryItem(
                id=cur.get("id", ""),
                source="candidate",
                path=str(f),
                text=cur.get("proposed_change", ""),
                date=f.stem,
                anchor_path=cur.get("target_file", ""),
            )
        )

    for raw in lines:
        s = raw.strip()
        if s.startswith("- id:"):
            flush()
            cur = {"id": s.split(":", 1)[1].strip()}
        elif s.startswith("proposed_change:"):
            cur["proposed_change"] = s.split(":", 1)[1].strip().strip('"')
        elif s.startswith("status:"):
            cur["status"] = s.split(":", 1)[1].strip()
        elif s.startswith("target_file:"):
            cur["target_file"] = s.split(":", 1)[1].strip()
    flush()
    return out


def iter_candidates(root: Path, include_rejected: bool) -> Iterable[MemoryItem]:
    for f in sorted((root / "_runtime" / "candidates").glob("*.yaml")):
        for item in parse_candidate_file(f, include_rejected):
            item.path = str(f.relative_to(root))
            yield item


def iter_events(root: Path) -> Iterable[MemoryItem]:
    for f in sorted((root / "_runtime" / "events").glob("*.ndjson")):
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            yield MemoryItem(
                id=obj.get("id", ""),
                source="event",
                path=str(f.relative_to(root)),
                text=obj.get("summary", ""),
                date=obj.get("ts_utc", f.stem),
                anchor_path=obj.get("project", ""),
            )


def iter_canonical(root: Path) -> Iterable[MemoryItem]:
    for f in sorted(root.rglob("*.md")):
        parts = set(f.parts)
        if ".git" in parts or "_runtime" in parts or "_tools" in parts:
            continue
        rel = str(f.relative_to(root))
        if rel in {"README.md", "_index.md"}:
            continue
        if rel.startswith("_agents/"):
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"\*\*Last Updated:\*\*\s*(\d{4}-\d{2}-\d{2})", text)
        date = m.group(1) if m else "1970-01-01"
        excerpt = " ".join(text.splitlines()[:50])
        yield MemoryItem(
            id=f"canon:{rel}",
            source="canonical",
            path=rel,
            text=excerpt,
            date=date,
            anchor_path=rel,
        )


def detect_markers(text: str) -> dict[str, str]:
    tl = text.lower()
    marks: dict[str, str] = {}
    for domain, groups in MARKER_PATTERNS.items():
        pos = bool(groups["positive"].search(tl))
        neg = bool(groups["negative"].search(tl))
        if pos and not neg:
            marks[domain] = "positive"
        elif neg and not pos:
            marks[domain] = "negative"
    return marks


def to_yaml(conflicts: list[dict]) -> str:
    lines = ["conflicts:"]
    for c in conflicts:
        lines.append(f"  - id: {c['id']}")
        lines.append(f"    topic: \"{c['topic']}\"")
        lines.append("    records:")
        for rid in c["records"]:
            lines.append(f"      - {rid}")
        lines.append(f"    reason: \"{c['reason']}\"")
        lines.append("    status: open")
        lines.append(f"    detected_at: {c['detected_at']}")
        lines.append("    details:")
        lines.append(f"      left_path: {c['left_path']}")
        lines.append(f"      right_path: {c['right_path']}")
        lines.append(f"      overlap_tokens: [{', '.join(c['overlap_tokens'])}]")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    out_date = args.date or now_utc().strftime("%Y-%m-%d")

    items: list[MemoryItem] = []
    if args.scope in ("all", "runtime"):
        items.extend(iter_events(root))
    if args.scope in ("all", "runtime", "candidates"):
        items.extend(iter_candidates(root, args.include_rejected))
    if args.scope in ("all", "canonical"):
        items.extend(iter_canonical(root))

    conflicts: list[dict] = []
    seen_pairs: set[tuple[str, str, str]] = set()
    counter = 1

    for i in range(len(items)):
        a = items[i]
        ta = tokenize(a.text)
        ma = detect_markers(a.text)
        if not ma:
            continue
        for j in range(i + 1, len(items)):
            b = items[j]
            if a.id == b.id:
                continue
            # Compare only anchored records for the same target file.
            if a.anchor_path and b.anchor_path and a.anchor_path != b.anchor_path:
                continue
            # Skip canonical-canonical pairwise checks (too broad/noisy for v1).
            if a.source == "canonical" and b.source == "canonical":
                continue
            tb = tokenize(b.text)
            overlap = sorted(ta.intersection(tb))
            if len(overlap) < args.min_topic_overlap:
                continue
            # Require at least one high-signal overlap token to reduce generic false positives.
            if not any(len(tok) >= 5 for tok in overlap):
                continue
            mb = detect_markers(b.text)
            if not mb:
                continue

            for domain in set(ma.keys()).intersection(mb.keys()):
                if ma[domain] == mb[domain]:
                    continue
                key = tuple(sorted((a.id, b.id)) + [domain])
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)
                conflicts.append(
                    {
                        "id": f"conf_{out_date.replace('-', '')}_{counter:03d}",
                        "topic": " ".join(overlap[:6]),
                        "records": [a.id, b.id],
                        "reason": f"{domain} contradiction ({ma[domain]} vs {mb[domain]})",
                        "detected_at": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "left_path": a.path,
                        "right_path": b.path,
                        "overlap_tokens": overlap[:8],
                    }
                )
                counter += 1
                if len(conflicts) >= args.limit:
                    break
            if len(conflicts) >= args.limit:
                break
        if len(conflicts) >= args.limit:
            break

    out_file = root / "_runtime" / "conflicts" / f"{out_date}.yaml"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(to_yaml(conflicts), encoding="utf-8")

    print(f"Wrote {len(conflicts)} conflicts to {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
