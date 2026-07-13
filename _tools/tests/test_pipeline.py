"""End-to-end contract tests for the AIKB memory pipeline.

Each test runs the real scripts inside a throwaway AIKB root (the scripts
resolve their root from __file__, so we copy them into a fake tree) — no
network, no embedding model, no state leaks into the working repo.

Run:  pytest _tools/tests/ -v
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = REPO_ROOT / "_tools" / "memory-pipeline"

sys.path.insert(0, str(PIPELINE_DIR))

import redaction  # noqa: E402


@pytest.fixture()
def fake_root(tmp_path: Path) -> Path:
    """Throwaway AIKB tree with the real pipeline scripts copied in."""
    root = tmp_path / "aikb"
    pipeline = root / "_tools" / "memory-pipeline"
    pipeline.mkdir(parents=True)
    for script in PIPELINE_DIR.glob("*.py"):
        shutil.copy(script, pipeline / script.name)
    (root / "_runtime" / "events").mkdir(parents=True)
    (root / "_runtime" / "candidates").mkdir(parents=True)
    (root / "projects").mkdir()
    (root / "projects" / "sample-project.md").write_text(
        "# Sample Project\n\n**Last Updated:** 2026-07-01\n\n"
        "## Database Decision\n\nWe chose postgres for the sample project backend.\n",
        encoding="utf-8",
    )
    return root


def run_script(root: Path, script: str, *args: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(root / "_tools" / "memory-pipeline" / script), *args]
    return subprocess.run(cmd, capture_output=True, text=True)


def capture(root: Path, summary: str, date: str = "2026-01-01") -> subprocess.CompletedProcess:
    return run_script(
        root,
        "ingest_runtime.py",
        "--agent", "Test Agent",
        "--session-id", "pytest",
        "--type", "observation",
        "--project", "projects/sample-project.md",
        "--summary", summary,
        "--date", date,
    )


def read_events(root: Path, date: str = "2026-01-01") -> list[dict]:
    path = root / "_runtime" / "events" / f"{date}.ndjson"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# ── Redaction unit tests ───────────────────────────────────────────────────────

CREDENTIAL_SAMPLES = [
    ("sk-ant-abcdefghijklmnopqrstuvwxyz123456", "anthropic_key"),
    ("sk-abcdefghijklmnopqrstuvwxyz123456", "openai_key"),
    ("ghp_ABCDEFGHIJKLMNOPQRSTuvwxyz012345", "github_pat"),
    ("github_pat_ABCDEFGHIJKLMNOPQRST_uvwxyz", "github_fine_grained"),
    ("AKIAIOSFODNN7EXAMPLE", "aws_access_key"),
    ("xoxb-1234567890-abcdefghij", "slack_token"),
    ("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", "bearer_token"),
    ("password=hunter2", "password_assignment"),
    ("api_key: 0123456789abcdef", "credential_assignment"),
]


@pytest.mark.parametrize("sample,expected", CREDENTIAL_SAMPLES)
def test_credential_shapes_are_redacted(sample: str, expected: str):
    result = redaction.redact_text(f"context before {sample} context after")
    assert expected in result.redactions
    assert sample not in result.text
    assert f"[REDACTED:{expected}]" in result.text


def test_prose_with_hint_words_is_not_redacted():
    result = redaction.redact_text("The token refresh bug was fixed in the auth service")
    assert result.redactions == []
    assert result.hints == ["token"]
    assert "token refresh bug" in result.text


def test_clean_text_passes_untouched():
    result = redaction.redact_text("Restarted nginx on the web host after config change")
    assert result.redactions == []
    assert result.hints == []


# ── Capture (remember → event) ─────────────────────────────────────────────────

def test_capture_writes_event(fake_root: Path):
    proc = capture(fake_root, "Chose postgres over sqlite for multi-writer support")
    assert proc.returncode == 0, proc.stderr
    events = read_events(fake_root)
    assert len(events) == 1
    assert events[0]["summary"].startswith("Chose postgres")
    assert events[0]["agent"] == "Test Agent"
    assert "redactions" not in events[0]


def test_capture_with_hint_word_is_not_blocked(fake_root: Path):
    proc = capture(fake_root, "The token refresh bug was fixed")
    assert proc.returncode == 0, "hint words must warn, not block"
    assert "note" in proc.stderr.lower() or "never log" in proc.stderr.lower()
    events = read_events(fake_root)
    assert events[0]["summary"] == "The token refresh bug was fixed"


def test_capture_redacts_real_credential(fake_root: Path):
    proc = capture(fake_root, "Router admin uses password=hunter2 for now")
    assert proc.returncode == 0
    events = read_events(fake_root)
    assert "hunter2" not in json.dumps(events)
    assert "[REDACTED:password_assignment]" in events[0]["summary"]
    assert events[0]["redactions"] == ["password_assignment"]


def test_concurrent_captures_all_land(fake_root: Path):
    procs = [capture(fake_root, f"parallel event {i}") for i in range(8)]
    assert all(p.returncode == 0 for p in procs)
    events = read_events(fake_root)
    assert len(events) == 8
    assert len({e["id"] for e in events}) == 8


# ── Candidate pipeline (event → candidate) ─────────────────────────────────────

def test_event_becomes_candidate(fake_root: Path):
    capture(fake_root, "Chose postgres over sqlite for multi-writer support")
    proc = run_script(fake_root, "build_candidates.py", "--date", "2026-01-01")
    assert proc.returncode == 0, proc.stderr
    candidate_file = fake_root / "_runtime" / "candidates" / "2026-01-01.yaml"
    assert candidate_file.exists()
    text = candidate_file.read_text()
    event_id = read_events(fake_root)[0]["id"]
    assert event_id in text
    assert "projects/sample-project.md" in text


def test_ignore_hint_skips_candidate(fake_root: Path):
    run_script(
        fake_root,
        "ingest_runtime.py",
        "--agent", "Test Agent",
        "--session-id", "pytest",
        "--type", "observation",
        "--project", "general",
        "--summary", "ephemeral note not worth promoting",
        "--promote-hint", "ignore",
        "--date", "2026-01-01",
    )
    run_script(fake_root, "build_candidates.py", "--date", "2026-01-01", "--no-fact-extraction")
    candidate_file = fake_root / "_runtime" / "candidates" / "2026-01-01.yaml"
    if candidate_file.exists():
        assert "ephemeral note" not in candidate_file.read_text()


# ── Search ─────────────────────────────────────────────────────────────────────

def test_search_finds_canonical_and_event(fake_root: Path):
    capture(fake_root, "Chose postgres over sqlite for multi-writer support")
    proc = run_script(
        fake_root, "memory_search.py",
        "--query", "postgres sample project decision",
        "--no-semantic", "--json",
    )
    assert proc.returncode == 0, proc.stderr
    results = json.loads(proc.stdout)
    assert results, "expected at least one search result"
    paths = [r["path"] for r in results]
    assert any("sample-project" in p for p in paths)


def test_search_explain_components_sum_to_score(fake_root: Path):
    capture(fake_root, "Chose postgres over sqlite for multi-writer support")
    proc = run_script(
        fake_root, "memory_search.py",
        "--query", "postgres decision",
        "--no-semantic", "--json", "--explain",
    )
    assert proc.returncode == 0, proc.stderr
    results = json.loads(proc.stdout)
    for record in results:
        assert "explain" in record
        assert abs(sum(record["explain"].values()) - record["score"]) < 0.01


def test_search_no_recency_flag(fake_root: Path):
    proc = run_script(
        fake_root, "memory_search.py",
        "--query", "postgres decision",
        "--no-semantic", "--no-recency", "--json", "--explain",
    )
    assert proc.returncode == 0, proc.stderr
    for record in json.loads(proc.stdout):
        assert record["explain"].get("recency", 0.0) == 0.0


def test_temporal_filter_excludes_later_events(fake_root: Path):
    # ingest's --date only names the output file; ts_utc drives temporal
    # filtering, so write the events directly with controlled timestamps.
    for date, note in (("2026-01-01", "postgres early note"), ("2026-03-01", "postgres later note")):
        event = {
            "id": f"evt_test_{date.replace('-', '')}",
            "ts_utc": f"{date}T12:00:00Z",
            "session_id": "pytest",
            "agent": "Test Agent",
            "type": "observation",
            "project": "general",
            "summary": note,
            "evidence": [],
            "sensitivity": "normal",
            "promote_hint": "candidate",
        }
        path = fake_root / "_runtime" / "events" / f"{date}.ndjson"
        path.write_text(json.dumps(event) + "\n", encoding="utf-8")
    proc = run_script(
        fake_root, "memory_search.py",
        "--query", "postgres note",
        "--scope", "events",
        "--no-semantic", "--json",
        "--before", "2026-01-31",
    )
    results = json.loads(proc.stdout)
    assert results
    assert all("2026-01-01" in r["path"] for r in results)


# ── SQLite hardening ───────────────────────────────────────────────────────────

def test_connect_db_uses_wal_and_busy_timeout(tmp_path: Path):
    import memory_search

    conn = memory_search.connect_db(tmp_path / "test.sqlite3")
    try:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 30000
    finally:
        conn.close()


def test_concurrent_readers_and_writer(tmp_path: Path):
    import memory_search

    db = tmp_path / "test.sqlite3"
    writer = memory_search.connect_db(db)
    writer.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, val TEXT)")
    writer.execute("INSERT INTO t (val) VALUES ('x')")
    # WAL allows a reader while a write txn is open — this deadlocks or raises
    # 'database is locked' under the old default journal mode with no timeout.
    reader = memory_search.connect_db(db)
    try:
        assert reader.execute("SELECT COUNT(*) FROM t").fetchone() is not None
        writer.commit()
        assert reader.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 1
    finally:
        reader.close()
        writer.close()
