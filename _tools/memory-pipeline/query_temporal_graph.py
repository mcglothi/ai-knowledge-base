#!/usr/bin/env python3
"""Query temporal knowledge graph neighbors with optional date bounds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--graph", default="", help="Graph JSON path")
    p.add_argument("--node", required=True, help="Node id or substring")
    p.add_argument("--before", default="")
    p.add_argument("--after", default="")
    p.add_argument("--limit", type=int, default=20)
    return p.parse_args()


def in_window(ts: str, before: str, after: str) -> bool:
    if before and ts > before:
        return False
    if after and ts < after:
        return False
    return True


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    graph_path = Path(args.graph) if args.graph else (root / "_runtime" / "graphs" / "temporal-knowledge-graph.json")

    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    edges = payload.get("edges", [])

    needle = args.node.lower()
    hits = []
    for e in edges:
        src = e.get("source", "")
        dst = e.get("target", "")
        ts = e.get("ts", "")
        if not in_window(ts, args.before, args.after):
            continue
        if needle in src.lower() or needle in dst.lower():
            hits.append(e)

    hits = hits[: max(1, args.limit)]
    if not hits:
        print("No graph edges matched.")
        return 0

    for i, h in enumerate(hits, 1):
        print(f"{i}. {h.get('source')} -[{h.get('relation')} @ {h.get('ts')}]-> {h.get('target')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
