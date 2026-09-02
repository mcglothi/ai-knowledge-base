#!/usr/bin/env python3
"""Build nightly dream artifacts from runtime memory surfaces."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
# Single source of truth for "what is not knowledge". Shared with
# build_candidates so the two stages cannot drift on what counts as noise --
# they did drift once, and dream_cycle spent months filing telemetry as facts.
from noise_filters import (  # noqa: E402
    TELEMETRY_TYPES,
    looks_like_structured_payload,
    unwrap_summary,
)
from urllib import parse, request

PREFERENCE_PATTERNS = (
    re.compile(r"\b(prefer|preferred|preference|default to|defaults to|always|never|avoid|likes?|dislikes?)\b", re.IGNORECASE),
)
PROCEDURE_PATTERNS = (
    re.compile(r"\b(runbook|workflow|steps?|procedure|install|configure|deploy|restart|verify|check)\b", re.IGNORECASE),
)
PROCEDURE_TARGET_HINTS = ("runbook", "runbooks/", "operator-intents", "checklist", "automation/")
IMPERATIVE_VERBS = {
    "add",
    "apply",
    "build",
    "capture",
    "check",
    "configure",
    "create",
    "deploy",
    "document",
    "enable",
    "fix",
    "install",
    "move",
    "record",
    "refresh",
    "restart",
    "run",
    "set",
    "sync",
    "update",
    "use",
    "verify",
    "wire",
}
NOISE_PATTERNS = (
    re.compile(r"\b(your prompt was already strong|yes, please write that|i'll |i will |task candidate:|fact candidate:)\b", re.IGNORECASE),
)
CONTRADICTION_PAIRS = (
    ("enable", "disable"),
    ("enabled", "disabled"),
    ("use", "avoid"),
    ("prefer", "avoid"),
    ("always", "never"),
    ("healthy", "unhealthy"),
    ("approved", "rejected"),
    ("required", "optional"),
)
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "with",
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
    "personal-projects/",
    "home-lab/",
    "projects/",
    "side-gigs/",
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
    parser.add_argument(
        "--proposal-statuses",
        default="approved,applied,rejected",
        help="Comma-separated Memory Core proposal statuses to ingest.",
    )
    parser.add_argument("--proposal-limit", type=int, default=50, help="Per-status Memory Core proposal fetch limit.")
    parser.add_argument("--api-key", default="", help="Optional Memory Core API key override.")
    parser.add_argument("--memory-core-url", default="", help="Optional Memory Core base URL override.")
    parser.add_argument("--no-memory-core", action="store_true", help="Disable live Memory Core proposal fetches.")
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
        import yaml  # type: ignore

        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if isinstance(payload, dict) and "candidates" in payload and isinstance(payload["candidates"], list):
            return [dict(item) for item in payload["candidates"] if isinstance(item, dict)]
        if isinstance(payload, dict):
            return [dict(payload)]
        if isinstance(payload, list):
            return [dict(item) for item in payload if isinstance(item, dict)]
    except Exception:
        pass

    lines = path.read_text(encoding="utf-8").splitlines()
    if any(line.strip() == "candidates:" for line in lines):
        records: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        in_source_events = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped == "candidates:":
                continue
            if stripped.startswith("- id:"):
                if current:
                    records.append(current)
                current = {"id": stripped.split(":", 1)[1].strip(), "source_events": []}
                in_source_events = False
                continue
            if current is None:
                continue
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
        if current:
            records.append(current)
        return records

    record: dict[str, Any] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        record[key.strip()] = parse_simple_yaml_value(value)
    return [record] if record else []


def load_events(root: Path, date_str: str) -> list[dict[str, Any]]:
    path = root / "_runtime" / "events" / f"{date_str}.ndjson"
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            events.append(item)
    return events


def load_compacted_summary(root: Path, date_str: str) -> dict[str, Any]:
    path = root / "_runtime" / "events" / "compacted" / f"{date_str}.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_candidates(root: Path, date_str: str) -> list[dict[str, Any]]:
    candidates_dir = root / "_runtime" / "candidates"
    paths = []
    exact = candidates_dir / f"{date_str}.yaml"
    if exact.exists():
        paths.append(exact)
    for path in sorted(candidates_dir.glob(f"*{date_str}*.yaml")):
        if path not in paths:
            paths.append(path)

    records: list[dict[str, Any]] = []
    for path in paths:
        records.extend(parse_candidate_yaml(path))
    return records


def resolve_memory_core_url(arg_url: str) -> str:
    """--memory-core-url, then $MEMORY_CORE_URL, then .aikb-config.d, then none.

    Memory Core is an optional private service, so there is deliberately no
    built-in default: a template must not ship someone else's hostname, and
    hard-coding one is what made this file diverge from its published copy.
    Unset means "no API" and the caller falls back to local fixtures, so a fresh
    clone works with no configuration at all.
    """
    if arg_url:
        return arg_url.rstrip("/")
    env_url = os.environ.get("MEMORY_CORE_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")
    config = Path(__file__).resolve().parents[2] / ".aikb-config.d" / "MEMORY_CORE_URL"
    try:
        return config.read_text(encoding="utf-8").strip().rstrip("/")
    except OSError:
        return ""


def resolve_api_key(arg_api_key: str) -> str:
    if arg_api_key:
        return arg_api_key
    env_key = os.environ.get("MMC_API_KEY", "")
    if env_key:
        return env_key

    bw_session_path = Path.home() / ".bw_session"
    if not bw_session_path.exists():
        return ""
    bw_session = bw_session_path.read_text(encoding="utf-8").strip()
    if not bw_session:
        return ""

    item_name = os.environ.get("MMC_API_KEY_ITEM", "PAT/AIKB Memory Core/API Key")
    res = subprocess.run(
        ["bw", "get", "password", item_name, "--session", bw_session],
        check=False,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        return ""
    return res.stdout.strip()


def memory_core_api_call(
    *,
    base_url: str,
    api_key: str,
    path: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    qs = ""
    if params:
        qs = "?" + parse.urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{base_url}{path}{qs}"
    req = request.Request(url, method="GET", headers={"X-API-Key": api_key})
    with request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def load_memory_core_proposals(
    *,
    root: Path,
    date_str: str,
    statuses: list[str],
    limit: int,
    base_url: str,
    api_key: str,
    disabled: bool,
) -> tuple[list[dict[str, Any]], str]:
    if disabled:
        return load_local_proposal_fixtures(root, date_str), "fixtures_disabled"
    if not api_key:
        return load_local_proposal_fixtures(root, date_str), "fixtures_no_api_key"
    # With no endpoint configured there is nothing to call. Without this the run
    # attempts a request against an empty URL and reports "fixtures_api_error",
    # which reads like a failure rather than the normal unconfigured case.
    if not base_url:
        return load_local_proposal_fixtures(root, date_str), "fixtures_not_configured"

    proposals: list[dict[str, Any]] = []
    try:
        for status in statuses:
            payload = memory_core_api_call(
                base_url=base_url,
                api_key=api_key,
                path="/api/v1/proposals",
                params={"status": status, "limit": limit},
            )
            items = payload.get("proposals", payload if isinstance(payload, list) else [])
            if isinstance(items, list):
                proposals.extend(item for item in items if isinstance(item, dict))
        return proposals, "memory_core"
    except Exception:
        return load_local_proposal_fixtures(root, date_str), "fixtures_api_error"


def load_local_proposal_fixtures(root: Path, date_str: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted((root / "_runtime").glob(f"proposal-fixture-*{date_str}*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def load_canonical_changes(root: Path, start: datetime, end: datetime) -> list[dict[str, Any]]:
    cmd = [
        "git",
        "-C",
        str(root),
        "log",
        "--since",
        start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "--until",
        end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "--name-only",
        "--pretty=format:__COMMIT__%n%H%n%aI%n%s",
        "--",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return []

    commits: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in proc.stdout.splitlines():
        line = raw.strip()
        if line == "__COMMIT__":
            if current:
                commits.append(current)
            current = {"files": []}
            continue
        if current is None:
            continue
        if "commit" not in current:
            current["commit"] = line
        elif "date" not in current:
            current["date"] = line
        elif "summary" not in current:
            current["summary"] = line
        elif line:
            current["files"].append(line)
    if current:
        commits.append(current)
    filtered = []
    for commit in commits:
        summary = str(commit.get("summary", ""))
        files = [str(path) for path in commit.get("files", []) if str(path)]
        if is_noisy_canonical_change(summary, files):
            continue
        score, durable_files, reasons = canonical_signal_score(summary, files)
        if score < 2:
            continue
        commit["signal_score"] = score
        commit["durable_files"] = durable_files
        commit["signal_reasons"] = reasons
        filtered.append(commit)
    return filtered


def is_noisy_canonical_change(summary: str, files: list[str]) -> bool:
    if not files:
        return True
    if all(path in CANONICAL_NOISE_FILES for path in files):
        return True
    lowered = summary.lower()
    return lowered.startswith("ai session end:") or lowered.startswith("ai update: _agents/active.md")


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
    if any(token in lowered for token in ("benchmark", "eval", "maintenance automation", "temporal graph")):
        score -= 2
        reasons.append("summary:maintenance-ish")
    if any(token in lowered for token in ("roadmap", "memory core", "jarvis", "metadata contract", "runbook")):
        score += 2
        reasons.append("summary:durable-domain")

    return score, durable_files, reasons


def normalize_summary(text: str, anchor_date: str) -> str:
    summary = " ".join((text or "").strip().split())
    if not summary:
        return ""

    anchor = datetime.strptime(anchor_date, "%Y-%m-%d").date()
    replacements = {
        r"\btoday\b": anchor.strftime("%Y-%m-%d"),
        r"\byesterday\b": (anchor - timedelta(days=1)).strftime("%Y-%m-%d"),
        r"\btomorrow\b": (anchor + timedelta(days=1)).strftime("%Y-%m-%d"),
        r"\btonight\b": f"evening of {anchor.strftime('%Y-%m-%d')}",
        r"\bthis morning\b": f"morning of {anchor.strftime('%Y-%m-%d')}",
        r"\bthis afternoon\b": f"afternoon of {anchor.strftime('%Y-%m-%d')}",
    }
    for pattern, repl in replacements.items():
        summary = re.sub(pattern, repl, summary, flags=re.IGNORECASE)
    return summary


def choose_category(summary: str, target_file: str, source_status: str) -> str:
    if source_status == "rejected" or any(p.search(summary) for p in NOISE_PATTERNS):
        return "rejection"
    if has_preference_signal(summary, target_file):
        return "preference"
    if has_procedure_signal(summary, target_file):
        return "procedure"
    return "fact"


def has_preference_signal(summary: str, target_file: str) -> bool:
    if any(p.search(summary) for p in PREFERENCE_PATTERNS):
        return True
    lowered = summary.lower()
    if target_file.endswith("personal/profile.md") and any(token in lowered for token in ("prefer", "default", "avoid", "always", "never")):
        return True
    return False


def has_procedure_signal(summary: str, target_file: str) -> bool:
    if any(p.search(summary) for p in PROCEDURE_PATTERNS):
        return True
    lowered_target = target_file.lower()
    if any(hint in lowered_target for hint in PROCEDURE_TARGET_HINTS):
        return True
    words = re.findall(r"[a-z]+", summary.lower())
    if words and words[0] in IMPERATIVE_VERBS and target_file.startswith(("home-lab/", "personal-projects/", "_tools/")):
        return True
    return False



def proposal_is_noise(proposal: dict[str, Any]) -> bool:
    summary = str(proposal.get("summary", "")).lower()
    payload = proposal.get("payload", {}) if isinstance(proposal.get("payload"), dict) else {}
    target_file = str(payload.get("suggested_file") or payload.get("target_file") or "")
    if any(p.search(summary) for p in NOISE_PATTERNS):
        return True
    if target_file.startswith("_runtime/"):
        return True
    if "fallback rendering" in summary or "payload quality" in summary:
        return True
    if payload.get("raw_payload"):
        return True
    if looks_like_structured_payload(str(proposal.get("summary", ""))):
        return True
    return False


def choose_trainability(
    *,
    category: str,
    source_type: str,
    source_status: str,
    sensitivity: str = "normal",
    promote_hint: str = "candidate",
) -> str:
    if category == "rejection" or source_status == "rejected":
        return "reject"
    if sensitivity == "restricted":
        return "retrieve_only"
    if source_type in {"canonical_change", "compacted"}:
        return "retrieve_only"
    if source_status in {"approved", "merged", "applied"}:
        return "trainable"
    if source_type == "event" and promote_hint == "candidate":
        return "trainable"
    return "retrieve_only"


def proposal_trainability(proposal: dict[str, Any], category: str, status: str) -> str:
    payload = proposal.get("payload", {}) if isinstance(proposal.get("payload"), dict) else {}
    target_file = str(payload.get("suggested_file") or payload.get("target_file") or "")
    if category == "rejection":
        return "reject"
    if not target_file:
        return "retrieve_only"
    return choose_trainability(category=category, source_type="proposal", source_status=status)


def choose_category_with_hints(
    *,
    summary: str,
    target_file: str,
    source_status: str,
    kind: str = "",
) -> str:
    kind_l = kind.lower().strip()
    if source_status == "rejected" or any(p.search(summary) for p in NOISE_PATTERNS):
        return "rejection"
    if kind_l == "preference":
        return "preference"
    if kind_l in {"runbook_update", "task"}:
        return "procedure"
    return choose_category(summary, target_file, source_status)


def tokenize_subject(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9]{3,}", text.lower()))
    return {token for token in tokens if token not in STOPWORDS}


def bundle_keywords(text: str, *, limit: int = 5) -> list[str]:
    ranked = sorted(tokenize_subject(text))
    return ranked[:limit]


def detect_conflict_reason(left: str, right: str) -> str:
    left_norm = left.lower()
    right_norm = right.lower()
    for a, b in CONTRADICTION_PAIRS:
        if a in left_norm and b in right_norm:
            return f"{a}<->{b}"
        if b in left_norm and a in right_norm:
            return f"{b}<->{a}"
    if " not " in f" {left_norm} " and " not " not in f" {right_norm} ":
        return "negation"
    if " not " in f" {right_norm} " and " not " not in f" {left_norm} ":
        return "negation"
    return ""


def detect_contradictions(records: list[DreamRecord]) -> list[dict[str, Any]]:
    contradictions: list[dict[str, Any]] = []
    candidates = [record for record in records if record.category != "rejection"]
    for idx, left in enumerate(candidates):
        left_tokens = tokenize_subject(left.normalized_summary)
        if len(left_tokens) < 3:
            continue
        for right in candidates[idx + 1 :]:
            if left.target_file and right.target_file and left.target_file != right.target_file:
                continue
            overlap = left_tokens & tokenize_subject(right.normalized_summary)
            if len(overlap) < 3:
                continue
            reason = detect_conflict_reason(left.summary, right.summary)
            if not reason:
                continue
            contradictions.append(
                {
                    "left_id": left.id,
                    "right_id": right.id,
                    "target_file": left.target_file or right.target_file,
                    "reason": reason,
                    "shared_tokens": sorted(overlap),
                    "left_summary": left.summary,
                    "right_summary": right.summary,
                }
            )
    return contradictions


def dedupe_records(records: list[DreamRecord]) -> list[DreamRecord]:
    order = {"trainable": 3, "retrieve_only": 2, "reject": 1}
    merged: dict[tuple[str, str, str], DreamRecord] = {}

    for record in records:
        key = (record.category, record.target_file, record.normalized_summary.lower())
        existing = merged.get(key)
        if existing is None:
            merged[key] = record
            continue

        keep_current = (
            order[record.trainability] > order[existing.trainability]
            or (record.trainability == existing.trainability and record.confidence > existing.confidence)
        )
        target = record if keep_current else existing
        other = existing if keep_current else record

        target.evidence = sorted(set(target.evidence + other.evidence))
        target.notes = sorted(set(target.notes + other.notes))
        target.duplicate_count += other.duplicate_count + 1
        merged[key] = target

    return sorted(merged.values(), key=lambda item: (item.category, item.target_file, item.id))


def resolve_bundle_trainability(records: list[DreamRecord]) -> str:
    if any(record.trainability == "trainable" for record in records):
        return "trainable"
    if any(record.trainability == "retrieve_only" for record in records):
        return "retrieve_only"
    return "reject"


def bundle_similarity(left: DreamRecord, right: DreamRecord) -> float:
    left_tokens = tokenize_subject(left.normalized_summary)
    right_tokens = tokenize_subject(right.normalized_summary)
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = left_tokens & right_tokens
    union = left_tokens | right_tokens
    return len(overlap) / max(1, len(union))


def build_bundles(records: list[DreamRecord], *, date_str: str) -> list[DreamBundle]:
    grouped: dict[tuple[str, str], list[list[DreamRecord]]] = defaultdict(list)

    for record in records:
        key = (record.category, record.target_file)
        placed = False
        for cluster in grouped[key]:
            if any(bundle_similarity(record, existing) >= 0.35 for existing in cluster):
                cluster.append(record)
                placed = True
                break
        if not placed:
            grouped[key].append([record])

    bundles: list[DreamBundle] = []
    counter = 1
    for (category, target_file), clusters in sorted(grouped.items()):
        for cluster in clusters:
            summaries = [record.summary for record in cluster]
            keyword_counter = Counter()
            for summary in summaries:
                keyword_counter.update(bundle_keywords(summary, limit=8))
            keywords = [token for token, _ in keyword_counter.most_common(6)]
            bundles.append(
                DreamBundle(
                    id=f"bundle_{date_str.replace('-', '')}_{counter:03d}",
                    date=date_str,
                    category=category,
                    target_file=target_file,
                    trainability=resolve_bundle_trainability(cluster),
                    record_ids=[record.id for record in cluster],
                    source_types=sorted({record.source_type for record in cluster}),
                    summaries=summaries[:5],
                    keywords=keywords,
                    avg_confidence=sum(record.confidence for record in cluster) / max(1, len(cluster)),
                )
            )
            counter += 1
    return consolidate_bundles(bundles, date_str=date_str)


def bundle_merge_score(left: DreamBundle, right: DreamBundle) -> float:
    if left.category != right.category or left.trainability != right.trainability:
        return 0.0
    if left.target_file != right.target_file:
        return 0.0
    left_keywords = set(left.keywords)
    right_keywords = set(right.keywords)
    if not left_keywords or not right_keywords:
        return 0.0
    overlap = left_keywords & right_keywords
    union = left_keywords | right_keywords
    return len(overlap) / max(1, len(union))


def should_merge_bundles(left: DreamBundle, right: DreamBundle) -> bool:
    score = bundle_merge_score(left, right)
    if score >= 0.30:
        return True
    shared = set(left.keywords) & set(right.keywords)
    if left.target_file == right.target_file and left.category == right.category and shared:
        return True
    return False


def merge_bundle_group(group: list[DreamBundle], *, bundle_id: str, date_str: str) -> DreamBundle:
    keyword_counter = Counter()
    source_types: set[str] = set()
    record_ids: list[str] = []
    summaries: list[str] = []

    for bundle in group:
        keyword_counter.update(bundle.keywords)
        source_types.update(bundle.source_types)
        record_ids.extend(bundle.record_ids)
        summaries.extend(bundle.summaries)

    keywords = [token for token, _ in keyword_counter.most_common(8)]
    unique_summaries = []
    seen = set()
    for summary in summaries:
        if summary in seen:
            continue
        seen.add(summary)
        unique_summaries.append(summary)

    return DreamBundle(
        id=bundle_id,
        date=date_str,
        category=group[0].category,
        target_file=group[0].target_file,
        trainability=group[0].trainability,
        record_ids=sorted(set(record_ids)),
        source_types=sorted(source_types),
        summaries=unique_summaries[:6],
        keywords=keywords,
        avg_confidence=sum(bundle.avg_confidence for bundle in group) / max(1, len(group)),
    )


def consolidate_bundles(bundles: list[DreamBundle], *, date_str: str) -> list[DreamBundle]:
    grouped: dict[tuple[str, str, str], list[list[DreamBundle]]] = defaultdict(list)

    for bundle in bundles:
        key = (bundle.category, bundle.target_file, bundle.trainability)
        placed = False
        for cluster in grouped[key]:
            if any(should_merge_bundles(bundle, existing) for existing in cluster):
                cluster.append(bundle)
                placed = True
                break
        if not placed:
            grouped[key].append([bundle])

    consolidated: list[DreamBundle] = []
    counter = 1
    for _, clusters in sorted(grouped.items()):
        for cluster in clusters:
            consolidated.append(
                merge_bundle_group(
                    cluster,
                    bundle_id=f"bundle_{date_str.replace('-', '')}_{counter:03d}",
                    date_str=date_str,
                )
            )
            counter += 1
    return consolidated


def canonical_signal_values(records: list[DreamRecord]) -> list[int]:
    values: list[int] = []
    for record in records:
        if record.source_type != "canonical_change":
            continue
        for note in record.notes:
            if note.startswith("signal_score:"):
                try:
                    values.append(int(note.split(":", 1)[1]))
                except ValueError:
                    pass
    return values


def build_quality_report(
    *,
    date_str: str,
    records: list[DreamRecord],
    bundles: list[DreamBundle],
    contradictions: list[dict[str, Any]],
    proposal_source: str,
) -> dict[str, Any]:
    by_category = Counter(record.category for record in records)
    by_trainability = Counter(record.trainability for record in records)
    by_source = Counter(record.source_type for record in records)
    signal_values = canonical_signal_values(records)
    bundle_sizes = [len(bundle.record_ids) for bundle in bundles]

    return {
        "date": date_str,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "proposal_source": proposal_source,
        "record_count": len(records),
        "bundle_count": len(bundles),
        "avg_bundle_size": round(sum(bundle_sizes) / max(1, len(bundle_sizes)), 2),
        "category_counts": dict(by_category),
        "trainability_counts": dict(by_trainability),
        "source_counts": dict(by_source),
        "trainable_ratio": round(by_trainability.get("trainable", 0) / max(1, len(records)), 3),
        "rejection_rate": round(by_trainability.get("reject", 0) / max(1, len(records)), 3),
        "contradiction_count": len(contradictions),
        "canonical_signal_avg": round(sum(signal_values) / max(1, len(signal_values)), 2) if signal_values else 0.0,
        "public_template_portable": True,
    }


def render_distilled_memory(
    *,
    date_str: str,
    bundles: list[DreamBundle],
    quality: dict[str, Any],
    contradictions: list[dict[str, Any]],
    proposal_source: str,
) -> str:
    top_trainable = [bundle for bundle in bundles if bundle.trainability == "trainable"][:5]
    top_procedures = [bundle for bundle in bundles if bundle.category == "procedure"][:4]
    top_preferences = [bundle for bundle in bundles if bundle.category == "preference"][:4]
    top_facts = [bundle for bundle in bundles if bundle.category == "fact" and bundle.trainability != "reject"][:4]
    top_rejections = [bundle for bundle in bundles if bundle.trainability == "reject"][:4]

    lines = [
        f"# Dream Distillation ({date_str})",
        "",
        "## Snapshot",
        "",
        f"- Proposal source: `{proposal_source}`",
        f"- Records: `{quality.get('record_count', 0)}`",
        f"- Bundles: `{quality.get('bundle_count', 0)}`",
        f"- Trainable ratio: `{quality.get('trainable_ratio', 0)}`",
        f"- Rejection rate: `{quality.get('rejection_rate', 0)}`",
        f"- Contradictions: `{quality.get('contradiction_count', 0)}`",
        "",
        "## What The System Learned",
        "",
    ]

    if top_trainable:
        for bundle in top_trainable:
            lines.append(
                f"- `{bundle.category}` `{bundle.target_file or '-'}`: {bundle.summaries[0]}"
            )
    else:
        lines.append("- No trainable memories were strong enough to highlight.")

    lines.extend(["", "## Procedures To Keep", ""])
    if top_procedures:
        for bundle in top_procedures:
            lines.append(f"- `{bundle.target_file or '-'}`: {bundle.summaries[0]}")
    else:
        lines.append("- No procedure-oriented memories stood out.")

    lines.extend(["", "## Preferences To Preserve", ""])
    if top_preferences:
        for bundle in top_preferences:
            lines.append(f"- `{bundle.target_file or '-'}`: {bundle.summaries[0]}")
    else:
        lines.append("- No preference-oriented memories stood out.")

    lines.extend(["", "## Durable Facts Worth Keeping In Retrieval", ""])
    if top_facts:
        for bundle in top_facts:
            lines.append(f"- `{bundle.target_file or '-'}`: {bundle.summaries[0]}")
    else:
        lines.append("- No durable fact bundles stood out.")

    lines.extend(["", "## Noise The Dream Rejected", ""])
    if top_rejections:
        for bundle in top_rejections:
            lines.append(f"- `{bundle.target_file or '-'}`: {bundle.summaries[0]}")
    else:
        lines.append("- No noisy bundles were rejected.")

    lines.extend(["", "## Contradictions To Review", ""])
    if contradictions:
        for contradiction in contradictions[:6]:
            lines.append(
                f"- `{contradiction['target_file'] or '-'}` `{contradiction['reason']}`: {contradiction['left_summary']} || {contradiction['right_summary']}"
            )
    else:
        lines.append("- None detected.")

    return "\n".join(lines) + "\n"


def build_records(
    *,
    date_str: str,
    events: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    proposals: list[dict[str, Any]],
    compacted: dict[str, Any],
    canonical_changes: list[dict[str, Any]],
) -> list[DreamRecord]:
    records: list[DreamRecord] = []

    for event in events:
        # quota_snapshot alone was 12,898 of the 15,344 chunks in the search
        # index and 98% of the event stream. Unfiltered, it was the ENTIRE
        # content of a nightly dream: four telemetry rows filed as durable
        # facts, plus six "contradictions" between near-identical lines.
        if event.get("type") in TELEMETRY_TYPES:
            continue
        # Closeouts wrap their payload in session counters (repo=, branch=,
        # events=, queue=). Keep the operator's note; a closeout without one
        # is bookkeeping and never a memory.
        raw = unwrap_summary(str(event.get("summary", "")) or "")
        if looks_like_structured_payload(raw):
            continue
        summary = normalize_summary(raw, date_str)
        if not summary:
            continue
        category = choose_category(summary, str(event.get("project", "")), "")
        records.append(
            DreamRecord(
                id=f"dream_evt_{event.get('id', len(records) + 1)}",
                date=date_str,
                category=category,
                trainability=choose_trainability(
                    category=category,
                    source_type="event",
                    source_status="",
                    sensitivity=str(event.get("sensitivity", "normal")),
                    promote_hint=str(event.get("promote_hint", "candidate")),
                ),
                summary=summary,
                normalized_summary=summary,
                source_type="event",
                source_id=str(event.get("id", "")),
                source_status="",
                target_file=str(event.get("project", "")),
                confidence=0.8 if event.get("type") in {"decision", "change"} else 0.65,
                evidence=[str(item) for item in event.get("evidence", []) if item],
            )
        )

    for candidate in candidates:
        summary = normalize_summary(
            str(candidate.get("proposed_change") or candidate.get("summary") or ""),
            date_str,
        )
        if not summary:
            continue
        status = str(candidate.get("status", "")).strip()
        target_file = str(candidate.get("target_file") or candidate.get("project") or "")
        category = choose_category_with_hints(
            summary=summary,
            target_file=target_file,
            source_status=status,
            kind=str(candidate.get("type", "")),
        )
        records.append(
            DreamRecord(
                id=f"dream_cand_{candidate.get('id', len(records) + 1)}",
                date=date_str,
                category=category,
                trainability=choose_trainability(
                    category=category,
                    source_type="candidate",
                    source_status=status,
                ),
                summary=summary,
                normalized_summary=summary,
                source_type="candidate",
                source_id=str(candidate.get("id", "")),
                source_status=status,
                target_file=target_file,
                confidence=float(candidate.get("confidence", 0.7) or 0.7),
                evidence=[str(item) for item in candidate.get("source_events", []) if item],
            )
        )

    for proposal in proposals:
        summary = normalize_summary(str(proposal.get("summary", "")), date_str)
        if not summary:
            continue
        status = str(proposal.get("status", "")).strip()
        kind = str(proposal.get("kind", "")).strip()
        payload = proposal.get("payload", {}) if isinstance(proposal.get("payload"), dict) else {}
        target_file = str(payload.get("suggested_file") or payload.get("target_file") or "")
        category = (
            "rejection"
            if proposal_is_noise(proposal)
            else choose_category_with_hints(
                summary=summary,
                target_file=target_file,
                source_status=status,
                kind=kind,
            )
        )
        evidence = []
        proposal_evidence = proposal.get("evidence", {})
        if isinstance(proposal_evidence, dict):
            for key, value in proposal_evidence.items():
                if value:
                    evidence.append(f"{key}:{value}")
        records.append(
            DreamRecord(
                id=f"dream_prop_{proposal.get('proposal_id', len(records) + 1)}",
                date=date_str,
                category=category,
                trainability=proposal_trainability(proposal, category, status),
                summary=summary,
                normalized_summary=summary,
                source_type="proposal",
                source_id=str(proposal.get("proposal_id", "")),
                source_status=status,
                target_file=target_file,
                confidence=float(proposal.get("confidence", 0.7) or 0.7),
                evidence=evidence,
                notes=[kind] if kind else [],
            )
        )

    for project, highlights in sorted(compacted.get("highlights", {}).items()):
        if not isinstance(highlights, list):
            continue
        for idx, raw_summary in enumerate(highlights, start=1):
            summary = normalize_summary(str(raw_summary), date_str)
            if not summary:
                continue
            category = choose_category(summary, str(project), "")
            records.append(
                DreamRecord(
                    id=f"dream_compacted_{date_str}_{idx}",
                    date=date_str,
                    category=category,
                    trainability="retrieve_only",
                    summary=summary,
                    normalized_summary=summary,
                    source_type="compacted",
                    source_id=str(compacted.get("source_file", "")),
                    source_status="",
                    target_file=str(project),
                    confidence=0.55,
                    evidence=[str(compacted.get("source_file", ""))] if compacted.get("source_file") else [],
                    notes=["compacted_highlight"],
                )
            )

    for commit in canonical_changes:
        summary = normalize_summary(str(commit.get("summary", "")), date_str)
        if not summary:
            continue
        files = [str(path) for path in commit.get("files", []) if str(path)]
        durable_files = [str(path) for path in commit.get("durable_files", []) if str(path)]
        target_file = durable_files[0] if durable_files else next(
            (path for path in files if path not in CANONICAL_NOISE_FILES),
            files[0] if files else "",
        )
        category = choose_category_with_hints(
            summary=summary,
            target_file=target_file,
            source_status="",
        )
        records.append(
            DreamRecord(
                id=f"dream_git_{str(commit.get('commit', ''))[:8]}",
                date=date_str,
                category=category,
                trainability="retrieve_only",
                summary=summary,
                normalized_summary=summary,
                source_type="canonical_change",
                source_id=str(commit.get("commit", "")),
                source_status="merged",
                target_file=target_file,
                confidence=min(0.95, 0.55 + 0.04 * int(commit.get("signal_score", 0))),
                evidence=files,
                notes=[
                    item
                    for item in [
                        str(commit.get("date", "")),
                        f"signal_score:{commit.get('signal_score', 0)}",
                        *[str(reason) for reason in commit.get("signal_reasons", [])],
                    ]
                    if item
                ],
            )
        )

    return dedupe_records(records)


def write_jsonl(path: Path, records: list[DreamRecord]) -> None:
    lines = [json.dumps(asdict(record), sort_keys=True) for record in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_summary(
    *,
    date_str: str,
    records: list[DreamRecord],
    bundles: list[DreamBundle],
    contradictions: list[dict[str, Any]],
    canonical_changes: list[dict[str, Any]],
    compacted: dict[str, Any],
    output_dir: Path,
    proposal_source: str,
    quality: dict[str, Any],
) -> str:
    by_category = Counter(record.category for record in records)
    by_trainability = Counter(record.trainability for record in records)
    by_source = Counter(record.source_type for record in records)

    top_trainable = [record for record in records if record.trainability == "trainable"][:8]
    lines = [
        f"# Dream Cycle Summary ({date_str})",
        "",
        f"- Generated at: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Output dir: `{output_dir}`",
        f"- Proposal source: `{proposal_source}`",
        f"- Records: `{len(records)}`",
        f"- Bundles: `{len(bundles)}`",
        f"- Trainable: `{by_trainability.get('trainable', 0)}`",
        f"- Retrieve-only: `{by_trainability.get('retrieve_only', 0)}`",
        f"- Rejected: `{by_trainability.get('reject', 0)}`",
        f"- Contradictions: `{len(contradictions)}`",
        "",
        "## Quality",
        "",
        f"- `trainable_ratio`: `{quality.get('trainable_ratio', 0)}`",
        f"- `rejection_rate`: `{quality.get('rejection_rate', 0)}`",
        f"- `avg_bundle_size`: `{quality.get('avg_bundle_size', 0)}`",
        f"- `canonical_signal_avg`: `{quality.get('canonical_signal_avg', 0)}`",
        f"- `public_template_portable`: `{quality.get('public_template_portable', False)}`",
        "",
        "## Category Counts",
        "",
    ]

    for category in ("fact", "procedure", "preference", "rejection"):
        lines.append(f"- `{category}`: {by_category.get(category, 0)}")

    lines.extend(["", "## Source Counts", ""])
    for source_type, count in sorted(by_source.items()):
        lines.append(f"- `{source_type}`: {count}")

    lines.extend(["", "## Top Trainable Memories", ""])
    if top_trainable:
        for record in top_trainable:
            lines.append(f"- `{record.category}` `{record.target_file or '-'}`: {record.summary}")
    else:
        lines.append("- None.")

    lines.extend(["", "## Dream Bundles", ""])
    if bundles:
        for bundle in bundles[:10]:
            keyword_text = ", ".join(bundle.keywords[:4]) or "-"
            lines.append(
                f"- `{bundle.category}` `{bundle.target_file or '-'}` `{bundle.trainability}` "
                f"(records={len(bundle.record_ids)}, avg_confidence={bundle.avg_confidence:.2f}, keywords={keyword_text})"
            )
    else:
        lines.append("- None.")

    lines.extend(["", "## Contradictions", ""])
    if contradictions:
        for conflict in contradictions[:10]:
            lines.append(
                f"- `{conflict['reason']}` `{conflict['target_file'] or '-'}`: {conflict['left_summary']} || {conflict['right_summary']}"
            )
    else:
        lines.append("- None detected.")

    lines.extend(["", "## Canonical Changes In Window", ""])
    if canonical_changes:
        for change in canonical_changes[:10]:
            files = ", ".join(change.get("files", [])[:3]) or "-"
            lines.append(f"- `{str(change.get('commit', ''))[:8]}`: {change.get('summary', '')} [{files}]")
    else:
        lines.append("- None detected.")

    if compacted:
        lines.extend(
            [
                "",
                "## Compacted Event Context",
                "",
                f"- Source file: `{compacted.get('source_file', '-')}`",
                f"- Event count: `{compacted.get('event_count', 0)}`",
            ]
        )

    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- `dream-summary-{date_str}.md`",
            f"- `dream-distilled-{date_str}.md`",
            f"- `dream-bundles-{date_str}.json`",
            f"- `dream-quality-{date_str}.json`",
            f"- `dream-facts-{date_str}.jsonl`",
            f"- `dream-procedures-{date_str}.jsonl`",
            f"- `dream-preferences-{date_str}.jsonl`",
            f"- `dream-rejections-{date_str}.jsonl`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_contradictions(path: Path, contradictions: list[dict[str, Any]], *, date_str: str) -> None:
    payload = {
        "date": date_str,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(contradictions),
        "contradictions": contradictions,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    date_str = resolve_runtime_date(args.date, allow_future=args.allow_future_date)
    here = Path(__file__).resolve().parent
    root = here.parents[1]
    output_dir = Path(args.output_dir).expanduser() if args.output_dir else root / "_runtime" / "dreams"
    output_dir.mkdir(parents=True, exist_ok=True)
    conflict_dir = root / "_runtime" / "conflicts"
    conflict_dir.mkdir(parents=True, exist_ok=True)

    start, end = dream_window(date_str, args.lookback_hours)
    events = load_events(root, date_str)
    candidates = load_candidates(root, date_str)
    compacted = load_compacted_summary(root, date_str)
    canonical_changes = load_canonical_changes(root, start, end)
    statuses = [item.strip() for item in args.proposal_statuses.split(",") if item.strip()]
    proposals, proposal_source = load_memory_core_proposals(
        root=root,
        date_str=date_str,
        statuses=statuses,
        limit=args.proposal_limit,
        base_url=resolve_memory_core_url(args.memory_core_url),
        api_key=resolve_api_key(args.api_key),
        disabled=args.no_memory_core,
    )

    records = build_records(
        date_str=date_str,
        events=events,
        candidates=candidates,
        proposals=proposals,
        compacted=compacted,
        canonical_changes=canonical_changes,
    )
    contradictions = detect_contradictions(records)
    bundles = build_bundles(records, date_str=date_str)
    quality = build_quality_report(
        date_str=date_str,
        records=records,
        bundles=bundles,
        contradictions=contradictions,
        proposal_source=proposal_source,
    )

    grouped: dict[str, list[DreamRecord]] = defaultdict(list)
    for record in records:
        grouped[record.category].append(record)

    write_json(output_dir / f"dream-bundles-{date_str}.json", [asdict(bundle) for bundle in bundles])
    write_json(output_dir / f"dream-quality-{date_str}.json", quality)
    write_jsonl(output_dir / f"dream-facts-{date_str}.jsonl", grouped["fact"])
    write_jsonl(output_dir / f"dream-procedures-{date_str}.jsonl", grouped["procedure"])
    write_jsonl(output_dir / f"dream-preferences-{date_str}.jsonl", grouped["preference"])
    write_jsonl(output_dir / f"dream-rejections-{date_str}.jsonl", grouped["rejection"])
    distilled = render_distilled_memory(
        date_str=date_str,
        bundles=bundles,
        quality=quality,
        contradictions=contradictions,
        proposal_source=proposal_source,
    )
    (output_dir / f"dream-distilled-{date_str}.md").write_text(distilled, encoding="utf-8")

    summary = render_summary(
        date_str=date_str,
        records=records,
        bundles=bundles,
        contradictions=contradictions,
        canonical_changes=canonical_changes,
        compacted=compacted,
        output_dir=output_dir,
        proposal_source=proposal_source,
        quality=quality,
    )
    summary_path = output_dir / f"dream-summary-{date_str}.md"
    summary_path.write_text(summary, encoding="utf-8")
    write_contradictions(conflict_dir / f"dream-{date_str}.json", contradictions, date_str=date_str)

    print(f"Wrote dream artifacts to {output_dir}")
    print(
        "records="
        f"{len(records)} contradictions={len(contradictions)} "
        f"trainable={sum(1 for record in records if record.trainability == 'trainable')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
