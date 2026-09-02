"""Contract tests for dream_cycle's intake filters and public surface.

These exist because of a specific failure. Commit 429924d7 ("feat: port dream
cycle...") cut dream_cycle.py from 1347 lines to 336, deleting 30 functions of
which only 7 were the private-service integration it was trying to strip. The
README was never updated, so this repo documented seven features it no longer
had, and nothing in CI noticed a 1123-line deletion.

The surface test below is the guard: if a future sanitisation pass flattens this
file again, CI fails instead of shipping docs that describe absent code.

Classification (fact/procedure/preference) is deliberately NOT asserted. It is
still regex-based and known-weak, but correcting it needs labelled ground truth
rather than an assertion of one contributor's taste.

Run:  pytest _tools/tests/ -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = REPO_ROOT / "_tools" / "memory-pipeline"

sys.path.insert(0, str(PIPELINE_DIR))

import dream_cycle  # noqa: E402
import noise_filters  # noqa: E402


# ── Structured payloads are not memories ──────────────────────────────────────

SERIALIZED_SAMPLES = [
    "Task candidate: [{'text': 'System: Potential loop detected",
    'Fact candidate: {"type":"file-history-snapshot","messageId":"c0c448aa"}',
    "Task candidate: {'role': 'user', 'content': [{'tool_use_id': 'toolu_016C'}]}",
    "the call returned tool_use_id toolu_016CTEFcWVU4",
]


@pytest.mark.parametrize("sample", SERIALIZED_SAMPLES)
def test_serialized_machine_state_is_rejected(sample: str):
    assert noise_filters.looks_like_structured_payload(sample)


PROSE_SAMPLES = [
    "Runbook update candidate: I fixed the vcmd script by using the hardware-native "
    "48,000 Hz sample rate for recording and resampling to 16,000 Hz for Whisper",
    "AdGuard aaaa_disabled enabled: set dns.aaaa_disabled=true on the secondary resolver",
    "Preference candidate: I dont have it yet, the adapter will be in next week",
]


@pytest.mark.parametrize("sample", PROSE_SAMPLES)
def test_prose_is_not_rejected(sample: str):
    assert not noise_filters.looks_like_structured_payload(sample)


def test_the_proposal_label_does_not_smuggle_a_payload_through():
    """"<Kind> candidate: " must not defeat the shape check."""
    payload = "[{'text': 'System: Potential loop detected'}]"
    assert noise_filters.looks_like_structured_payload(payload)
    assert noise_filters.looks_like_structured_payload("Task candidate: " + payload)


@pytest.mark.parametrize("empty", ["", "   ", None])
def test_empty_input_is_not_a_payload(empty):
    assert not noise_filters.looks_like_structured_payload(empty)


# ── Closeout envelopes ────────────────────────────────────────────────────────

def test_closeout_note_survives_and_counters_do_not():
    summary = (
        "Closeout captured for task 'Deploy guard'; repo=dirty:7; branch=main; "
        "events=221; queue=528; note='Deployed the guard; 275 evaluated, 0 mismatches.'"
    )
    out = noise_filters.unwrap_summary(summary)
    assert out == "Deployed the guard; 275 evaluated, 0 mismatches."
    for counter in ("repo=", "branch=", "events=", "queue="):
        assert counter not in out


def test_a_closeout_with_no_note_yields_nothing():
    assert noise_filters.unwrap_summary("Closeout captured for task 'X'; repo=clean") == ""


def test_a_note_containing_semicolons_is_not_truncated():
    assert noise_filters.unwrap_summary("Closeout captured for 'X'; note='a; b; c'") == "a; b; c"


def test_ordinary_summaries_pass_through_untouched():
    summary = "Secondary resolver migrated and aaaa_disabled set"
    assert noise_filters.unwrap_summary(summary) == summary


# ── Telemetry ─────────────────────────────────────────────────────────────────

def test_telemetry_types_are_filtered():
    assert "quota_snapshot" in noise_filters.TELEMETRY_TYPES
    assert "quota_snapshot" in dream_cycle.TELEMETRY_TYPES


@pytest.mark.parametrize("kind", ["change", "decision", "observation", "blocker", "feedback"])
def test_knowledge_types_are_not_filtered(kind: str):
    assert kind not in noise_filters.TELEMETRY_TYPES


# ── Regression guard ──────────────────────────────────────────────────────────

# Removed wholesale by 429924d7 and restored since. Each is generic pipeline
# functionality, not private-service integration.
RESTORED_FUNCTIONS = [
    "build_records", "build_bundles", "consolidate_bundles", "build_quality_report",
    "dedupe_records", "choose_category_with_hints", "choose_trainability",
    "bundle_similarity", "bundle_merge_score", "merge_bundle_group", "bundle_keywords",
    "write_jsonl", "write_json", "write_contradictions", "render_distilled_memory",
    "render_summary", "is_noisy_canonical_change", "canonical_signal_values",
    "detect_conflict_reason", "load_compacted_summary",
]


@pytest.mark.parametrize("name", RESTORED_FUNCTIONS)
def test_dream_cycle_surface_is_intact(name: str):
    assert hasattr(dream_cycle, name), (
        f"{name} is missing. If a sanitisation pass removed it, the README in "
        "_tools/memory-pipeline/ now documents features this code does not have."
    )


@pytest.mark.parametrize(
    "symbol", ["DreamBundle", "CONTRADICTION_PAIRS", "IMPERATIVE_VERBS", "PROCEDURE_TARGET_HINTS"]
)
def test_no_orphaned_constants(symbol: str):
    """A constant appearing exactly once is defined-but-unused.

    That is the fingerprint the last regression left: the functions were deleted
    and their constants were not, so the file still *looked* complete.
    """
    source = (PIPELINE_DIR / "dream_cycle.py").read_text(encoding="utf-8")
    assert source.count(symbol) > 1, f"{symbol} is defined but never used"


def test_no_private_hostname_is_hardcoded():
    """The default that made this file unpublishable in the first place."""
    source = (PIPELINE_DIR / "dream_cycle.py").read_text(encoding="utf-8")
    assert "memory.home." not in source
    assert 'MEMORY_CORE_URL", "http' not in source


def test_unconfigured_memory_core_resolves_to_nothing(monkeypatch):
    """A fresh clone must fall back to fixtures, not call an empty URL."""
    monkeypatch.delenv("MEMORY_CORE_URL", raising=False)
    monkeypatch.setattr(
        dream_cycle.Path, "read_text", lambda *a, **k: (_ for _ in ()).throw(OSError())
    )
    assert dream_cycle.resolve_memory_core_url("") == ""
