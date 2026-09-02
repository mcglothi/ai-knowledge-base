"""
Shared definition of what is not a memory.

Every stage of the pipeline consumes the same runtime event stream, and each one
independently learned that most of it is not knowledge. Keeping these in one
module is deliberate: when the definitions lived in two places, the stages drifted
and dream_cycle spent months filing telemetry as durable facts while
build_candidates had already been taught to skip it.

All three filters are structural, not semantic. They ask "is this the shape of a
memory at all", never "is this memory any good" — that judgement needs a model
and a benchmark to score it against (see promotion_gate.py).
"""

from __future__ import annotations

import re

# Event types that carry no promotable knowledge. quota_snapshot alone was 3016
# of 3086 events in a representative month, and 12,898 of 15,344 chunks in the
# search index before the indexer learned to skip it.
TELEMETRY_TYPES = {"quota_snapshot", "heartbeat", "context_meter"}

# Proposals arrive labelled ("Fact candidate: ", "Runbook update candidate: ").
# The label must be stripped before testing the shape of what follows, or a
# serialized blob passes the check simply because it starts with a word.
_PROPOSAL_LABEL = re.compile(r"^[A-Za-z][A-Za-z ]{0,30}candidate:\s*", re.IGNORECASE)

# Markers of serialized machine state that reached the memory stream verbatim.
STRUCTURED_PAYLOAD_MARKERS = (
    "tool_use_id", "toolu_", "messageId", "file-history-snapshot",
    "trackedFileBackups", "backupFileName", '"role":', "'role':",
    "stop_reason", "tool_result",
)


def unwrap_summary(summary: str) -> str:
    """Strip the closeout envelope, keeping only the operator's note.

    `closeout` wraps its payload in session bookkeeping:

        Closeout captured for task '...'; repo=dirty:7; branch=main; cwd=AIKB;
        events=221; candidates=2; queue=528; approvals=0; session_age=11m;
        note='<the part that is actually knowledge>'

    Closeouts are 54% of all candidate-hinted events. Left wrapped, the counters
    dominate the text: a reviewer reads past them, and a classifier reads the
    note's substance while the row still looks like bookkeeping. Returns "" for a
    closeout carrying no note, which is bookkeeping and nothing else.
    """
    summary = summary or ""
    if not summary.startswith("Closeout captured"):
        return summary
    note = re.search(r"note='(.*)'\s*$", summary, re.S)
    return note.group(1).strip() if note else ""


def looks_like_structured_payload(text: str) -> bool:
    """True when the text is serialized state rather than a sentence.

    Tool-result envelopes, file-history snapshots, chat-transcript fragments and
    dict/list reprs were being filed as "Procedures To Keep" and "Durable Facts".
    A memory is prose; these are rejected structurally rather than by hoping a
    classifier notices.
    """
    stripped = _PROPOSAL_LABEL.sub("", (text or "").strip()).strip()
    if not stripped:
        return False
    if stripped[:1] in "{[":
        return True
    if any(marker in stripped for marker in STRUCTURED_PAYLOAD_MARKERS):
        return True
    # Prose has spaces between words; a serialized blob is mostly punctuation.
    letters = sum(c.isalpha() or c.isspace() for c in stripped[:400])
    return len(stripped) > 80 and letters / min(len(stripped), 400) < 0.72
