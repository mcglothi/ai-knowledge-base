#!/usr/bin/env python3
"""
Aggregate usage signals into aikb_index.db for ranking.

Two signal streams, both keyed on (file_path, section) — chunk rowids are
regenerated on reindex, so natural keys are the only stable join:

  access_stats   — from _runtime/telemetry/aikb-search/*.ndjson (written by
                   server.py on every search). Powers a bounded recency-of-use
                   boost: chunks that keep getting retrieved surface a little
                   easier; chunks nobody touches drift down. Full rebuild per
                   run over a sliding window, so decay needs no bookkeeping.

  feedback_stats — from _runtime/events/*.ndjson type:"feedback" records
                   (written by the aikb_feedback MCP tool). Powers bounded
                   penalties for chunks flagged stale/wrong/incomplete/duplicate.

Run standalone (nightly maintenance) or via build_index() after indexing:
    python3 usage_stats.py
"""

import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

TOOL_DIR = Path(__file__).parent
AIKB_ROOT = TOOL_DIR.parent.parent
DB_PATH = TOOL_DIR / "aikb_index.db"
TELEMETRY_DIR = AIKB_ROOT / "_runtime" / "telemetry" / "aikb-search"
EVENTS_DIR = AIKB_ROOT / "_runtime" / "events"

SCHEMA = """
    CREATE TABLE IF NOT EXISTS access_stats (
        file_path      TEXT NOT NULL,
        section        TEXT NOT NULL,
        hit_count      INTEGER NOT NULL DEFAULT 0,
        rank_weighted  REAL    NOT NULL DEFAULT 0.0,
        last_retrieved TEXT,
        PRIMARY KEY (file_path, section)
    );

    CREATE TABLE IF NOT EXISTS feedback_stats (
        file_path     TEXT NOT NULL,
        section       TEXT NOT NULL DEFAULT '',
        stale         INTEGER NOT NULL DEFAULT 0,
        wrong         INTEGER NOT NULL DEFAULT 0,
        incomplete    INTEGER NOT NULL DEFAULT 0,
        duplicate     INTEGER NOT NULL DEFAULT 0,
        last_feedback TEXT,
        PRIMARY KEY (file_path, section)
    );

    CREATE TABLE IF NOT EXISTS usage_meta (
        key   TEXT PRIMARY KEY,
        value TEXT
    );
"""

FEEDBACK_ISSUES = ("stale", "wrong", "incomplete", "duplicate")


def _iter_ndjson_in_window(directory: Path, window_days: int):
    """Yield parsed JSON lines from YYYY-MM-DD.ndjson files inside the window.
    Filters on filename date so old logs are never even opened."""
    if not directory.exists():
        return
    cutoff = datetime.now(timezone.utc).date() - timedelta(days=window_days)
    for f in sorted(directory.glob("*.ndjson")):
        try:
            file_date = datetime.strptime(f.stem, "%Y-%m-%d").date()
        except ValueError:
            continue
        if file_date < cutoff:
            continue
        try:
            with f.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue


def refresh_usage_stats(conn: sqlite3.Connection, window_days: int = 30):
    """Rebuild access_stats from search telemetry within the window."""
    conn.executescript(SCHEMA)
    stats: dict[tuple[str, str], dict] = {}
    for entry in _iter_ndjson_in_window(TELEMETRY_DIR, window_days):
        ts = entry.get("ts_utc", "")
        for result in entry.get("results", []):
            key = (result.get("file", ""), result.get("section", ""))
            if not key[0]:
                continue
            rank = result.get("rank") or 1
            s = stats.setdefault(key, {"hits": 0, "rw": 0.0, "last": ""})
            s["hits"] += 1
            s["rw"] += 1.0 / max(1, rank)
            if ts > s["last"]:
                s["last"] = ts

    conn.execute("DELETE FROM access_stats")
    conn.executemany(
        """INSERT INTO access_stats (file_path, section, hit_count, rank_weighted, last_retrieved)
           VALUES (?, ?, ?, ?, ?)""",
        [(fp, sec, s["hits"], s["rw"], s["last"]) for (fp, sec), s in stats.items()],
    )
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn.execute(
        "INSERT OR REPLACE INTO usage_meta (key, value) VALUES ('access_refreshed_at', ?)", (now,)
    )
    return len(stats)


def refresh_feedback_stats(conn: sqlite3.Connection, window_days: int = 180):
    """Rebuild feedback_stats from type:'feedback' runtime events."""
    conn.executescript(SCHEMA)
    stats: dict[tuple[str, str], dict] = {}
    for event in _iter_ndjson_in_window(EVENTS_DIR, window_days):
        if event.get("type") != "feedback":
            continue
        detail = event.get("detail") or {}
        file_path = detail.get("file", "")
        if not file_path:
            continue
        issue = detail.get("issue", "")
        if issue not in FEEDBACK_ISSUES:
            continue
        key = (file_path, detail.get("section", "") or "")
        s = stats.setdefault(key, {i: 0 for i in FEEDBACK_ISSUES} | {"last": ""})
        s[issue] += 1
        ts = event.get("ts_utc", "")
        if ts > s["last"]:
            s["last"] = ts

    conn.execute("DELETE FROM feedback_stats")
    conn.executemany(
        """INSERT INTO feedback_stats (file_path, section, stale, wrong, incomplete, duplicate, last_feedback)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [
            (fp, sec, s["stale"], s["wrong"], s["incomplete"], s["duplicate"], s["last"])
            for (fp, sec), s in stats.items()
        ],
    )
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn.execute(
        "INSERT OR REPLACE INTO usage_meta (key, value) VALUES ('feedback_refreshed_at', ?)", (now,)
    )
    return len(stats)


def main():
    if not DB_PATH.exists():
        print(f"Index not found at {DB_PATH}; run indexer.py first.")
        sys.exit(0)  # not an error: nightly runs on hosts without an index
    conn = sqlite3.connect(DB_PATH)
    try:
        n_access = refresh_usage_stats(conn)
        n_feedback = refresh_feedback_stats(conn)
        conn.commit()
    finally:
        conn.close()
    print(f"usage_stats: {n_access} access row(s), {n_feedback} feedback row(s).")


if __name__ == "__main__":
    main()
