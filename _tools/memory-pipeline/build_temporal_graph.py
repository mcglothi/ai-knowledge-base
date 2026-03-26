#!/usr/bin/env python3
"""Build a temporal knowledge graph from AIKB markdown links + runtime events."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
UPDATED_RE = re.compile(r"\*\*Last Updated:\*\*\s*(\d{4}-\d{2}-\d{2})")
FRONTMATTER_UPDATED_RE = re.compile(r"(?im)^last_updated:\s*(\d{4}-\d{2}-\d{2})\b")
TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default="", help="Output JSON path")
    return p.parse_args()


def parse_date(text: str) -> str:
    m = UPDATED_RE.search(text)
    if m:
        return m.group(1)
    m = FRONTMATTER_UPDATED_RE.search(text)
    return m.group(1) if m else "1970-01-01"


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]

    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    for f in sorted(root.rglob("*.md")):
        parts = set(f.parts)
        if ".git" in parts or "_tools" in parts:
            continue
        rel = str(f.relative_to(root))
        text = f.read_text(encoding="utf-8", errors="ignore")
        title = (TITLE_RE.search(text).group(1).strip() if TITLE_RE.search(text) else rel)
        last_updated = parse_date(text)

        nodes[rel] = {
            "id": rel,
            "kind": "doc",
            "title": title,
            "last_updated": last_updated,
        }

        for link in LINK_RE.findall(text):
            target = link.split("#", 1)[0].strip()
            if not target or target.startswith("http://") or target.startswith("https://"):
                continue
            if target.startswith("./"):
                try:
                    target = str((f.parent / target).resolve().relative_to(root.resolve()))
                except ValueError:
                    target = target[2:]
            target = target.lstrip("/")
            edges.append(
                {
                    "source": rel,
                    "target": target,
                    "relation": "references",
                    "ts": last_updated,
                }
            )

    # Runtime event -> project edges
    for ev_file in sorted((root / "_runtime" / "events").glob("*.ndjson")):
        for line in ev_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                continue
            event_id = evt.get("id") or f"event:{ev_file.stem}"
            event_node = f"event:{event_id}"
            nodes[event_node] = {
                "id": event_node,
                "kind": "event",
                "title": evt.get("summary", "event"),
                "last_updated": (evt.get("ts_utc", "")[:10] or ev_file.stem),
                "event_type": evt.get("type", "unknown"),
            }
            project = evt.get("project", "").strip()
            if project:
                if project not in nodes:
                    nodes[project] = {
                        "id": project,
                        "kind": "doc",
                        "title": project,
                        "last_updated": ev_file.stem,
                    }
                edges.append(
                    {
                        "source": event_node,
                        "target": project,
                        "relation": "mentions_project",
                        "ts": (evt.get("ts_utc", "")[:10] or ev_file.stem),
                    }
                )

    out = Path(args.out) if args.out else (root / "_runtime" / "graphs" / "temporal-knowledge-graph.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": list(nodes.values()),
        "edges": edges,
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote graph with {len(nodes)} nodes / {len(edges)} edges -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
