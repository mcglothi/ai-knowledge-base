#!/usr/bin/env python3
"""Build a temporal knowledge graph from AIKB markdown links + runtime events."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
UPDATED_RE = re.compile(r"\*\*Last Updated:\*\*\s*(\d{4}-\d{2}-\d{2})")
FRONTMATTER_UPDATED_RE = re.compile(r"(?im)^last_updated:\s*(\d{4}-\d{2}-\d{2})\b")
TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
# Directories excluded from the graph. These are either machine-local tooling
# (.claude, .venv, node_modules) or our own source, none of which is knowledge.
# Including them made the graph depend on which host ran the build.
SKIP_DIRS = {".git", "_tools", ".claude", ".codex", ".venv", "node_modules", ".pytest_cache"}

IP_RE = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")

def extract_entities(text: str) -> list[str]:
    """Extract IPs and simple capitalized entities (heuristics for local tools/hosts)."""
    entities = set(IP_RE.findall(text))
    # Simple heuristic for tools/hosts (e.g., TrueNAS, Ghostty, Docker)
    caps = re.findall(r"\b[A-Z][a-z0-9]+\b", text)
    for c in caps:
        if len(c) > 3 and c not in {"This", "The", "When", "What", "How", "If"}:
            entities.add(c)
    # Sorted, not list(set): set iteration order varies per process (hash
    # randomization), which made every rebuild reorder the whole file and
    # produce enormous meaningless diffs even when nothing had changed.
    return sorted(entities)

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
        if parts & SKIP_DIRS:
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

        # Extract entities from document
        doc_entities = extract_entities(text)
        for ent in doc_entities:
            if ent not in nodes:
                nodes[ent] = {"id": ent, "kind": "entity", "title": ent, "last_updated": last_updated}
            edges.append({
                "source": rel,
                "target": ent,
                "relation": "mentions_entity",
                "ts": last_updated,
            })

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

    # Runtime event -> project edges.
    #
    # Read the TRACKED compacted summaries, not the raw _runtime/events/*.ndjson.
    # Those raw files are gitignored (.gitignore: _runtime/events/*.ndjson), so a
    # machine with 138 of them produced a ~107k-edge graph while a fresh clone with
    # 5 produced ~18k. Same code, same commit, different answer. Building from
    # tracked inputs makes the graph reproducible on any host.
    compacted_dir = root / "_runtime" / "events" / "compacted"
    if compacted_dir.exists():
        for ev_file in sorted(compacted_dir.glob("*.json")):
            try:
                payload = json.loads(ev_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue
            day = ev_file.stem
            event_node = f"event:{day}"
            types = payload.get("types") or {}
            nodes[event_node] = {
                "id": event_node,
                "kind": "event",
                "title": f"{payload.get('event_count', 0)} events on {day}",
                "last_updated": day,
                "event_type": (max(types, key=types.get) if types else "unknown"),
            }

            for project in (payload.get("projects") or {}):
                project = str(project).strip()
                if not project or project == "unknown":
                    continue
                # A project label is whatever the event recorded — sometimes an
                # absolute path from another host. It is not a document, so do not
                # label it "doc" and let it masquerade as one in the graph.
                if project not in nodes:
                    nodes[project] = {
                        "id": project,
                        "kind": "project",
                        "title": Path(project).name or project,
                        "last_updated": day,
                    }
                edges.append({
                    "source": event_node,
                    "target": project,
                    "relation": "mentions_project",
                    "ts": day,
                })

            highlights = payload.get("highlights") or {}
            summaries: list[str] = []
            if isinstance(highlights, dict):
                for group in highlights.values():
                    if isinstance(group, list):
                        summaries.extend(str(x) for x in group)
            elif isinstance(highlights, list):
                summaries.extend(str(x) for x in highlights)

            seen_ents: set[str] = set()
            for summary in summaries:
                for ent in extract_entities(summary):
                    if ent in seen_ents:
                        continue
                    seen_ents.add(ent)
                    if ent not in nodes:
                        nodes[ent] = {"id": ent, "kind": "entity", "title": ent, "last_updated": day}
                    edges.append({
                        "source": event_node,
                        "target": ent,
                        "relation": "mentions_entity",
                        "ts": day,
                    })

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
