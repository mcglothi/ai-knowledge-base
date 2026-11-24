#!/usr/bin/env python3
# Last Updated: 2026-09-08
"""
Optional local-LLM entity enrichment for the AIKB search index.

The deterministic extraction in indexer.py is the always-on baseline; this
pass adds LLM-extracted entities ONLY where a local OpenAI-compatible
endpoint (LM Studio / Ollama / a dedicated inference host — see llm_enrich.yaml) is reachable.
No endpoint → exit 0, index untouched, nightly stays green.

LLM-derived rows use kind 'term-llm' so they are distinguishable and fully
reversible: --reset deletes them all.

Usage:
    python3 llm_enrich.py [--max-chunks N] [--dry-run] [--reset]
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import re
import sqlite3
import sys
import urllib.error
import urllib.request
import time
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
    """Return (endpoint_url, model_id) for the first reachable endpoint, else None.

    The probe budget is deliberately generous. A 2s timeout looks fine against an
    idle host -- a dedicated inference host answers /models in ~20ms -- but a nightly runs exactly
    when that host is loaded, and a probe that times out falls silently through
    to the next endpoint. That turns "the batch runs on the sidecar" into "the
    batch quietly ran on the laptop" with nothing in the log to say so.
    """
    forced_url = os.environ.get("AIKB_LOCAL_LLM_URL")
    forced_model = os.environ.get("AIKB_LOCAL_LLM_MODEL")
    if forced_url and forced_model:
        config = {**config, "endpoints": [{"url": forced_url}], "model_preference": [forced_model]}
    preference = config.get("model_preference") or []
    probe_timeout = float(config.get("probe_timeout_seconds", 8))
    for ep in config.get("endpoints") or []:
        url = ep.get("url", "").rstrip("/")
        if not url:
            continue
        try:
            with urllib.request.urlopen(f"{url}/models", timeout=probe_timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            continue
        models = [m.get("id", "") for m in data.get("data", [])]
        if not models:
            continue
        if forced_model and forced_model not in models:
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
        msg = data["choices"][0]["message"]
        # Thinking models (Qwen3.x under LM Studio) return an EMPTY content and
        # put the answer in reasoning_content. Reading only content silently
        # yields zero entities on every call.
        content = (msg.get("content") or "").strip() or (msg.get("reasoning_content") or "").strip()
    except Exception:
        if os.environ.get("AIKB_REQUIRE_MODEL") == "1":
            raise
        return []
    if not content:
        if os.environ.get("AIKB_REQUIRE_MODEL") == "1":
            raise RuntimeError("Entity model returned empty content")
        return []

    m = re.search(r"\[.*?\]", content, re.S)
    if not m:
        if os.environ.get("AIKB_REQUIRE_MODEL") == "1":
            raise RuntimeError("Entity model returned no JSON array")
        return []
    try:
        raw = json.loads(m.group(0))
    except json.JSONDecodeError:
        if os.environ.get("AIKB_REQUIRE_MODEL") == "1":
            raise
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

    # indexer pulls fastembed; import lazily so this stays cheap when there is
    # no endpoint to talk to.
    from indexer import connect_db

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
            return 1 if os.environ.get("AIKB_REQUIRE_MODEL") == "1" else 0
        endpoint, model = found
        print(f"llm_enrich: using {endpoint} ({model})")

        limit = args.max_chunks or int(config.get("max_chunks_per_run", 200))
        chunks = select_chunks(conn, limit)
        if not chunks:
            print("llm_enrich: no chunks need enrichment.")
            return 0

        # Import lazily so indexer's fastembed dependency isn't touched.
        from indexer import insert_entity_links, prune_high_degree_entities

        # Serial extraction at ~4-15s per chunk means a 200-chunk budget can run
        # for the better part of an hour. Fan out, and stop at a wall-clock
        # budget so one slow night cannot stall the rest of the nightly.
        workers = max(1, int(config.get("workers", 4)))
        budget = float(config.get("max_seconds", 600))
        started = time.time()
        enriched = 0
        processed = 0
        with cf.ThreadPoolExecutor(workers) as pool:
            futures = {
                pool.submit(llm_extract, endpoint, model, content): chunk_id
                for chunk_id, content in chunks
            }
            for future in cf.as_completed(futures):
                chunk_id = futures[future]
                processed += 1
                if time.time() - started > budget:
                    for pending in futures:
                        pending.cancel()
                    print(f"llm_enrich: hit {budget:.0f}s budget after {processed} chunk(s); stopping early.")
                    break
                names = future.result()
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
