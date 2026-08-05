#!/usr/bin/env python3
"""Append one runtime_event record to _runtime/events/YYYY-MM-DD.ndjson."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))
from redaction import HINT_WORDS as SECRET_HINTS  # noqa: E402  (back-compat name)
from redaction import redact_text  # noqa: E402

EVENT_TYPES = {"decision", "blocker", "change", "observation"}
SENSITIVITY = {"normal", "restricted"}
PROMOTE_HINT = {"candidate", "ignore"}

# Free-text event fields that pass through redaction before being logged.
TEXT_FIELDS = ("summary", "rejected", "assumptions", "invariants", "next_step")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--type", required=True, choices=sorted(EVENT_TYPES))
    parser.add_argument("--project", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--rejected", help="What was tried or considered and ruled out, and why")
    parser.add_argument("--assumptions", help="Things true right now that won't be obvious from the code")
    parser.add_argument("--invariants", help="Temporary states: things intentionally broken/incomplete until X")
    parser.add_argument("--next-step", help="The exact next action when this work resumes")
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--sensitivity", default="normal", choices=sorted(SENSITIVITY))
    parser.add_argument("--promote-hint", default="candidate", choices=sorted(PROMOTE_HINT))
    parser.add_argument("--date", help="Override date for output file (YYYY-MM-DD)")
    return parser.parse_args()


def looks_sensitive(text: str) -> bool:
    """Deprecated: advisory only. Kept for callers that still import it."""
    lowered = text.lower()
    return any(hint in lowered for hint in SECRET_HINTS)


def apply_redaction(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    """Redact credential shapes in free-text fields, in place.

    Returns (redaction_names, hint_words). Redactions mean a credential shape
    was found and replaced — capture proceeds with the redacted text. Hints are
    advisory words that merit a warning but never block capture.
    """
    redactions: list[str] = []
    hints: list[str] = []
    for field_name in TEXT_FIELDS:
        value = getattr(args, field_name, None)
        if not value:
            continue
        result = redact_text(value)
        setattr(args, field_name, result.text)
        redactions.extend(r for r in result.redactions if r not in redactions)
        hints.extend(h for h in result.hints if h not in hints)
    if getattr(args, "evidence", None):
        cleaned = []
        for item in args.evidence:
            result = redact_text(item)
            cleaned.append(result.text)
            redactions.extend(r for r in result.redactions if r not in redactions)
        args.evidence = cleaned
    return redactions, hints


def build_event(args: argparse.Namespace) -> dict:
    now = datetime.now(timezone.utc)
    event_id = f"evt_{now.strftime('%Y%m%d_%H%M%S_%f')}_{uuid4().hex[:6]}"

    event = {
        "id": event_id,
        "ts_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_id": args.session_id,
        "agent": args.agent,
        "type": args.type,
        "project": args.project,
        "summary": args.summary.strip(),
        "evidence": args.evidence,
        "sensitivity": args.sensitivity,
        "promote_hint": args.promote_hint,
    }
    if getattr(args, "rejected", None):
        event["rejected"] = args.rejected.strip()
    if getattr(args, "assumptions", None):
        event["assumptions"] = args.assumptions.strip()
    if getattr(args, "invariants", None):
        event["invariants"] = args.invariants.strip()
    if getattr(args, "next_step", None):
        event["next_step"] = args.next_step.strip()
    return event


def main() -> int:
    args = parse_args()
    redactions, hints = apply_redaction(args)
    if redactions:
        print(
            f"Warning: redacted credential-shaped content ({', '.join(redactions)}). "
            "Store the secret in the password manager and reference it by name.",
            file=sys.stderr,
        )
    elif hints:
        print(
            f"Note: summary mentions {', '.join(hints)} — fine if it's just prose, "
            "but never log actual credential values.",
            file=sys.stderr,
        )

    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_file = Path(__file__).resolve().parents[2] / "_runtime" / "events" / f"{date_str}.ndjson"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    event = build_event(args)
    if redactions:
        event["redactions"] = redactions
    with out_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=True) + "\n")

    print(f"Appended event {event['id']} to {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
