#!/usr/bin/env python3
"""
Optional local-LLM entity enrichment for the AIKB search index.

The deterministic extraction in indexer.py is the always-on baseline; this
pass adds LLM-extracted entities ONLY where a local OpenAI-compatible
endpoint (LM Studio / Ollama / Hopper — see llm_enrich.yaml) is reachable.
No endpoint → exit 0, index untouched, nightly stays green.

LLM-derived rows use kind 'term-llm' so they are distinguishable and fully
reversible: --reset deletes them all.

Usage:
    python3 llm_enrich.py [--max-chunks N] [--dry-run] [--reset]
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import yaml

TOOL_DIR = Path(__file__).parent
DB_PATH = TOOL_DIR / "aikb_index.db"
CONFIG_PATH = TOOL_DIR / "llm_enrich.yaml"

MAX_ENTITIES_PER_CHUNK = 8
_NAME_OK = re.compile(r"^[a-z0-9][a-z0-9./:-]{2,39}$")

PROMPT = (
    "Extract up to 8 named entities from the text below: tools, services, "
    "hostnames, projects, protocols, or product names. Output ONLY a JSON "
    "array of lowercase strings, no prose. Skip generic words (server, "
    "script, memory, config).\n\nText:\n{text}\n\nJSON array:"
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--max-chunks", type=int, default=0, help="Override config max_chunks_per_run")
    p.add_argument("--dry-run", action="store_true", help="Extract but do not write")
    p.add_argument("--reset", action="store_true", help="Delete all term-llm entities and exit")
    return p.parse_args()


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}


def detect_endpoint(config: dict) -> tuple[str, str] | None:
    """Return (endpoint_url, model_id) for the first reachable endpoint, else None."""
    preference = config.get("model_preference") or []
    for ep in config.get("endpoints") or []:
        url = ep.get("url", "").rstrip("/")
        if not url:
            continue
        try:
            with urllib.request.urlopen(f"{url}/models", timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            continue
        models = [m.get("id", "") for m in data.get("data", [])]
        if not models:
            continue
        model = next((m for m in preference if m in models), models[0])
        return url, model
    return None


def llm_extract(endpoint: str, model: str, text: str) -> list[str]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT.format(text=text[:1500])}],
        "temperature": 0.0,
        # Reasoning models spend tokens in reasoning_content before emitting
        # the JSON array; 200 starves them into empty content.
        "max_tokens": 900,
    }
    req = urllib.request.Request(
        f"{endpoint}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
    except Exception:
        return []

    m = re.search(r"\[.*?\]", content, re.S)
    if not m:
        return []
    try:
        raw = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []

    names = []
    for item in raw:
        if not isinstance(item, str):
            continue
        name = item.strip().lower().replace("_", "-").replace(" ", "-")
        if _NAME_OK.match(name) and not name.isdigit():
            names.append(name)
        if len(names) >= MAX_ENTITIES_PER_CHUNK:
            break
    return names


def select_chunks(conn: sqlite3.Connection, limit: int) -> list[tuple[int, str]]:
    """Chunks with no term/term-llm entity links yet — the ones deterministic
    extraction found nothing content-shaped in."""
    return conn.execute(
        """SELECT c.id, c.content FROM chunks c
           WHERE NOT EXISTS (
               SELECT 1 FROM entity_chunks ec
               JOIN entities e ON e.id = ec.entity_id
               WHERE ec.chunk_id = c.id AND e.kind IN ('term', 'term-llm')
           )
           AND length(c.content) > 120
           ORDER BY c.mtime DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()


def main() -> int:
    args = parse_args()
    if not DB_PATH.exists():
        print("llm_enrich: no index present; nothing to do.")
        return 0

    conn = connect_db()
    try:
        if args.reset:
            cur = conn.execute(
                "DELETE FROM entity_chunks WHERE entity_id IN (SELECT id FROM entities WHERE kind='term-llm')"
            )
            conn.execute("DELETE FROM entities WHERE kind='term-llm'")
            conn.commit()
            print(f"llm_enrich: removed {cur.rowcount} term-llm link(s).")
            return 0

        config = load_config()
        found = detect_endpoint(config)
        if not found:
            print("llm_enrich: no local LLM endpoint reachable; skipping (baseline stands alone).")
            return 0
        endpoint, model = found
        print(f"llm_enrich: using {endpoint} ({model})")

        limit = args.max_chunks or int(config.get("max_chunks_per_run", 200))
        chunks = select_chunks(conn, limit)
        if not chunks:
            print("llm_enrich: no chunks need enrichment.")
            return 0

        # Import lazily so indexer's fastembed dependency isn't touched.
        from indexer import insert_entity_links, prune_high_degree_entities

        enriched = 0
        for chunk_id, content in chunks:
            names = llm_extract(endpoint, model, content)
            if not names:
                continue
            if args.dry_run:
                print(f"  [dry-run] chunk {chunk_id}: {names}")
                continue
            insert_entity_links(conn, chunk_id, [(n, "term-llm") for n in names])
            enriched += 1

        if not args.dry_run:
            prune_high_degree_entities(conn)
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            conn.execute(
                "INSERT OR REPLACE INTO usage_meta (key, value) VALUES ('llm_enriched_at', ?)", (now,)
            )
            conn.commit()
        print(f"llm_enrich: enriched {enriched}/{len(chunks)} chunk(s).")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
