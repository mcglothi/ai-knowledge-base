#!/usr/bin/env python3
"""Generate autonomous memory reorganization suggestions for AIKB runtime + canonical memory."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

TOKEN_RE = re.compile(r"[a-zA-Z0-9_\-]{3,}")


@dataclass
class Item:
    id: str
    source: str
    path: str
    text: str
    date: str


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--min-similarity", type=float, default=0.62)
    p.add_argument("--stale-days", type=int, default=180)
    p.add_argument("--limit", type=int, default=30)
    p.add_argument("--out", default="", help="Optional output path. Default: _runtime/reorg-suggestions/YYYY-MM-DD.json")
    return p.parse_args()


def parse_date(value: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def extract_last_updated(text: str) -> str:
    patterns = [
        r"\*\*Last Updated:\*\*\s*(\d{4}-\d{2}-\d{2})",
        r"(?im)^last_updated:\s*(\d{4}-\d{2}-\d{2})\b",
        r"(?im)^#\s*Last Updated:\s*(\d{4}-\d{2}-\d{2})\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return m.group(1)
    return ""


def tokenize(text: str) -> set[str]:
    return {t.lower() for t in TOKEN_RE.findall(text)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load_candidates(root: Path) -> list[Item]:
    out: list[Item] = []
    for f in sorted((root / "_runtime" / "candidates").glob("*.yaml")):
        lines = f.read_text(encoding="utf-8").splitlines()
        cur: dict[str, str] = {}

        def flush() -> None:
            if not cur.get("id"):
                return
            out.append(
                Item(
                    id=cur.get("id", ""),
                    source="candidate",
                    path=str(f.relative_to(root)),
                    text=cur.get("proposed_change", ""),
                    date=f.stem,
                )
            )

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("- id:"):
                flush()
                cur = {"id": stripped.split(":", 1)[1].strip()}
            elif stripped.startswith("proposed_change:"):
                cur["proposed_change"] = stripped.split(":", 1)[1].strip().strip('"')
        flush()
    return out


def load_canonical(root: Path) -> list[Item]:
    out: list[Item] = []
    for f in sorted(root.rglob("*.md")):
        parts = set(f.parts)
        if ".git" in parts or "_runtime" in parts or "_tools" in parts:
            continue
        rel = str(f.relative_to(root))
        text = f.read_text(encoding="utf-8", errors="ignore")
        date = extract_last_updated(text)
        out.append(Item(id=f"canon:{rel}", source="canonical", path=rel, text=text[:1800], date=date))
    return out


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    now = datetime.now(timezone.utc)

    candidates = load_candidates(root)
    canonical = load_canonical(root)
    items = candidates + canonical

    token_cache = {item.id: tokenize(item.text) for item in items}
    suggestions: list[dict] = []

    # 1) Merge suggestions from high-similarity items (candidate<->candidate, candidate<->canonical)
    for i, left in enumerate(items):
        if left.source == "canonical":
            continue
        for right in items[i + 1 :]:
            if left.path == right.path:
                continue
            sim = jaccard(token_cache[left.id], token_cache[right.id])
            if sim < args.min_similarity:
                continue
            suggestions.append(
                {
                    "type": "merge",
                    "reason": "High semantic/token overlap indicates potential duplicate memory.",
                    "confidence": round(sim, 3),
                    "left": {"id": left.id, "source": left.source, "path": left.path},
                    "right": {"id": right.id, "source": right.source, "path": right.path},
                    "action": "Consolidate into one canonical memory statement and mark duplicate as merged.",
                }
            )

    # 2) Archive suggestions for stale canonical documents.
    for doc in canonical:
        dt = parse_date(doc.date)
        if not dt:
            continue
        age_days = (now - dt).days
        if age_days < args.stale_days:
            continue
        suggestions.append(
            {
                "type": "archive-review",
                "reason": "Canonical memory appears stale and may need restructure or archive.",
                "confidence": round(min(0.99, age_days / 365.0), 3),
                "target": {"id": doc.id, "source": doc.source, "path": doc.path},
                "age_days": age_days,
                "action": "Review for decomposition into smaller topical files or archive if no longer active.",
            }
        )

    suggestions.sort(key=lambda s: s.get("confidence", 0.0), reverse=True)
    suggestions = suggestions[: max(1, args.limit)]

    out_dir = root / "_runtime" / "reorg-suggestions"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out) if args.out else out_dir / f"{now.strftime('%Y-%m-%d')}.json"

    payload = {
        "generated_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "candidate_count": len(candidates),
            "canonical_count": len(canonical),
            "suggestion_count": len(suggestions),
            "min_similarity": args.min_similarity,
            "stale_days": args.stale_days,
        },
        "suggestions": suggestions,
    }

    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(suggestions)} suggestion(s) -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
