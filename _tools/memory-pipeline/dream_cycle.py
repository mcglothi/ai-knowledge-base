#!/usr/bin/env python3
"""Build nightly dream artifacts from runtime memory surfaces."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

PREFERENCE_PATTERNS = (
    re.compile(r"\b(prefer|preferred|preference|default to|defaults to|always|never|avoid|likes?|dislikes?)\b", re.IGNORECASE),
)
PROCEDURE_PATTERNS = (
    re.compile(r"\b(runbook|workflow|steps?|procedure|install|configure|deploy|restart|verify|check)\b", re.IGNORECASE),
)
PROCEDURE_TARGET_HINTS = ("runbook", "runbooks/", "operator-intents", "checklist", "automation/")
IMPERATIVE_VERBS = {
    "add", "apply", "build", "capture", "check", "configure", "create", "deploy", "document",
    "enable", "fix", "install", "move", "record", "refresh", "restart", "run", "set", "sync",
    "update", "use", "verify", "wire",
}
NOISE_PATTERNS = (
    re.compile(r"\b(your prompt was already strong|yes, please write that|i'll |i will |task candidate:|fact candidate:)\b", re.IGNORECASE),
)
CONTRADICTION_PAIRS = (
    ("enable", "disable"), ("enabled", "disabled"), ("use", "avoid"), ("prefer", "avoid"),
    ("always", "never"), ("healthy", "unhealthy"), ("approved", "rejected"), ("required", "optional"),
)
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "in", "is", "it",
    "of", "on", "or", "that", "the", "this", "to", "was", "with",
}
CANONICAL_NOISE_FILES = {"_agents/active.md"}
CANONICAL_NOISE_PREFIXES = (
    "_runtime/benchmarks/",
    "_runtime/graphs/",
    "_runtime/reorg-suggestions/",
    "_runtime/conflicts/",
    "_tools/",
    "_templates/",
)
CANONICAL_DURABLE_PREFIXES = (
    "personal/",
    "projects/",
    "work/",
)

@dataclass
class DreamRecord:
    id: str
    date: str
    category: str
    trainability: str
    summary: str
    normalized_summary: str
    source_type: str
    source_id: str
    source_status: str
    target_file: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    duplicate_count: int = 0
    notes: list[str] = field(default_factory=list)

@dataclass
class DreamBundle:
    id: str
    date: str
    category: str
    target_file: str
    trainability: str
    record_ids: list[str]
    source_types: list[str]
    summaries: list[str]
    keywords: list[str]
    avg_confidence: float

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="", help="Dream date (YYYY-MM-DD). Defaults to today UTC.")
    parser.add_argument("--allow-future-date", action="store_true", help="Allow --date values after today UTC.")
    parser.add_argument("--lookback-hours", type=int, default=24, help="Git lookback window for canonical changes.")
    parser.add_argument("--output-dir", default="", help="Override output directory. Defaults to _runtime/dreams.")
    return parser.parse_args()

def resolve_runtime_date(raw: str, *, allow_future: bool) -> str:
    today = datetime.now(timezone.utc).date()
    if not raw:
        return today.strftime("%Y-%m-%d")
    try:
        requested = datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SystemExit("--date must be a valid YYYY-MM-DD value.") from exc
    if requested > today and not allow_future:
        raise SystemExit(f"--date {raw} is in the future relative to UTC today {today.isoformat()}.")
    return requested.strftime("%Y-%m-%d")

def dream_window(date_str: str, lookback_hours: int) -> tuple[datetime, datetime]:
    anchor = datetime.strptime(date_str, "%Y-%m-%d").date()
    end = datetime.combine(anchor, time(23, 59, 59), tzinfo=timezone.utc)
    start = end - timedelta(hours=max(1, lookback_hours))
    return start, end

def parse_simple_yaml_value(raw: str) -> Any:
    value = raw.strip()
    if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
        return value[1:-1]
    if value in {"true", "false"}:
        return value == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value

def parse_candidate_yaml(path: Path) -> list[dict[str, Any]]:
    try:
        import yaml
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if isinstance(payload, dict) and "candidates" in payload and isinstance(payload["candidates"], list):
            return [dict(item) for item in payload["candidates"] if isinstance(item, dict)]
    except Exception:
        pass

    lines = path.read_text(encoding="utf-8").splitlines()
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_source_events = False
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped == "candidates:":
            continue
        if stripped.startswith("- id:"):
            if current: records.append(current)
            current = {"id": stripped.split(":", 1)[1].strip(), "source_events": []}
            in_source_events = False
            continue
        if current is None: continue
        if stripped == "source_events:":
            in_source_events = True
            continue
        if in_source_events and stripped.startswith("- "):
            current.setdefault("source_events", []).append(stripped[2:].strip())
            continue
        in_source_events = False
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            current[key.strip()] = parse_simple_yaml_value(value)
    if current: records.append(current)
    return records

def load_events(root: Path, date_str: str) -> list[dict[str, Any]]:
    path = root / "_runtime" / "events" / f"{date_str}.ndjson"
    if not path.exists(): return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        try:
            item = json.loads(line)
            if isinstance(item, dict): events.append(item)
        except json.JSONDecodeError: continue
    return events

def load_candidates(root: Path, date_str: str) -> list[dict[str, Any]]:
    candidates_dir = root / "_runtime" / "candidates"
    paths = list(candidates_dir.glob(f"*{date_str}*.yaml"))
    records: list[dict[str, Any]] = []
    for path in paths:
        records.extend(parse_candidate_yaml(path))
    return records

def load_canonical_changes(root: Path, start: datetime, end: datetime) -> list[dict[str, Any]]:
    cmd = ["git", "-C", str(root), "log", "--since", start.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "--until", end.strftime("%Y-%m-%dT%H:%M:%SZ"), "--name-only", "--pretty=format:__COMMIT__%n%H%n%aI%n%s", "--"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0: return []

    commits: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in proc.stdout.splitlines():
        line = raw.strip()
        if line == "__COMMIT__":
            if current: commits.append(current)
            current = {"files": []}
            continue
        if current is None: continue
        if "commit" not in current: current["commit"] = line
        elif "date" not in current: current["date"] = line
        elif "summary" not in current: current["summary"] = line
        elif line: current["files"].append(line)
    if current: commits.append(current)
    
    filtered = []
    for commit in commits:
        summary = str(commit.get("summary", ""))
        files = [str(path) for path in commit.get("files", []) if str(path)]
        score, durable_files, reasons = canonical_signal_score(summary, files)
        if score < 2: continue
        commit["signal_score"] = score
        commit["durable_files"] = durable_files
        commit["signal_reasons"] = reasons
        filtered.append(commit)
    return filtered

def canonical_signal_score(summary: str, files: list[str]) -> tuple[int, list[str], list[str]]:
    score = 0
    durable_files: list[str] = []
    reasons: list[str] = []
    lowered = summary.lower()
    for path in files:
        if path in CANONICAL_NOISE_FILES:
            score -= 3
            reasons.append(f"noise-file:{path}")
            continue
        if any(path.startswith(prefix) for prefix in CANONICAL_DURABLE_PREFIXES):
            durable_files.append(path)
            score += 4
            reasons.append(f"durable:{path}")
            continue
        if any(path.startswith(prefix) for prefix in CANONICAL_NOISE_PREFIXES):
            score -= 2
            reasons.append(f"maintenance:{path}")
            continue
        if path in {"_index.md", "_state.yaml", "README.md"}:
            score += 1
            reasons.append(f"meta:{path}")
    if lowered.startswith("ai update:"):
        score += 1
        reasons.append("commit:ai-update")
    return score, durable_files, reasons

def normalize_summary(text: str, anchor_date: str) -> str:
    summary = " ".join((text or "").strip().split())
    if not summary: return ""
    anchor = datetime.strptime(anchor_date, "%Y-%m-%d").date()
    replacements = {
        r"\btoday\b": anchor.strftime("%Y-%m-%d"),
        r"\byesterday\b": (anchor - timedelta(days=1)).strftime("%Y-%m-%d"),
        r"\btomorrow\b": (anchor + timedelta(days=1)).strftime("%Y-%m-%d"),
    }
    for pattern, repl in replacements.items():
        summary = re.sub(pattern, repl, summary, flags=re.IGNORECASE)
    return summary

def choose_category(summary: str, target_file: str, source_status: str) -> str:
    if source_status == "rejected" or any(p.search(summary) for p in NOISE_PATTERNS):
        return "rejection"
    if any(p.search(summary) for p in PREFERENCE_PATTERNS):
        return "preference"
    if any(p.search(summary) for p in PROCEDURE_PATTERNS):
        return "procedure"
    return "fact"

def tokenize_subject(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9]{3,}", text.lower()))
    return {token for token in tokens if token not in STOPWORDS}

def detect_contradictions(records: list[DreamRecord]) -> list[dict[str, Any]]:
    contradictions: list[dict[str, Any]] = []
    candidates = [record for record in records if record.category != "rejection"]
    for idx, left in enumerate(candidates):
        left_tokens = tokenize_subject(left.normalized_summary)
        if len(left_tokens) < 3: continue
        for right in candidates[idx + 1 :]:
            if left.target_file and right.target_file and left.target_file != right.target_file:
                continue
            overlap = left_tokens & tokenize_subject(right.normalized_summary)
            if len(overlap) < 3: continue
            contradictions.append({
                "left_id": left.id, "right_id": right.id,
                "target_file": left.target_file or right.target_file,
                "left_summary": left.summary, "right_summary": right.summary,
            })
    return contradictions

def main() -> int:
    args = parse_args()
    date_str = resolve_runtime_date(args.date, allow_future=args.allow_future_date)
    root = Path(__file__).resolve().parents[2]
    output_dir = Path(args.output_dir).expanduser() if args.output_dir else root / "_runtime" / "dreams"
    output_dir.mkdir(parents=True, exist_ok=True)

    start, end = dream_window(date_str, args.lookback_hours)
    events = load_events(root, date_str)
    candidates = load_candidates(root, date_str)
    canonical_changes = load_canonical_changes(root, start, end)

    records: list[DreamRecord] = []
    for event in events:
        summary = normalize_summary(str(event.get("summary", "")), date_str)
        if not summary: continue
        records.append(DreamRecord(
            id=f"dream_evt_{event.get('id', len(records))}", date=date_str,
            category=choose_category(summary, str(event.get("project", "")), ""),
            trainability="trainable", summary=summary, normalized_summary=summary,
            source_type="event", source_id=str(event.get("id", "")),
            source_status="", target_file=str(event.get("project", "")), confidence=0.7,
        ))

    for cand in candidates:
        summary = normalize_summary(str(cand.get("proposed_change", "")), date_str)
        if not summary: continue
        records.append(DreamRecord(
            id=f"dream_cand_{cand.get('id', len(records))}", date=date_str,
            category=choose_category(summary, str(cand.get("target_file", "")), str(cand.get("status", ""))),
            trainability="trainable", summary=summary, normalized_summary=summary,
            source_type="candidate", source_id=str(cand.get("id", "")),
            source_status=str(cand.get("status", "")), target_file=str(cand.get("target_file", "")),
            confidence=float(cand.get("confidence", 0.7)),
        ))

    contradictions = detect_contradictions(records)
    
    # Simple markdown distillation
    lines = [f"# Dream Distillation ({date_str})", "", "## Summary", 
             f"- Records: {len(records)}", f"- Contradictions: {len(contradictions)}", ""]
    
    if records:
        lines.append("## What Was Learned")
        for r in records[:10]:
            lines.append(f"- [{r.category}] {r.summary}")
    
    (output_dir / f"dream-distilled-{date_str}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote dream artifacts to {output_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
