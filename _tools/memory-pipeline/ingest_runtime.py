#!/usr/bin/env python3
"""Append one runtime_event record to _runtime/events/YYYY-MM-DD.ndjson."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

EVENT_TYPES = {"decision", "blocker", "change", "observation"}
SENSITIVITY = {"normal", "restricted"}
PROMOTE_HINT = {"candidate", "ignore"}
SECRET_HINTS = ("password", "api_key", "apikey", "token", "secret", "private key")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--type", required=True, choices=sorted(EVENT_TYPES))
    parser.add_argument("--project", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--sensitivity", default="normal", choices=sorted(SENSITIVITY))
    parser.add_argument("--promote-hint", default="candidate", choices=sorted(PROMOTE_HINT))
    parser.add_argument("--date", help="Override date for output file (YYYY-MM-DD)")
    return parser.parse_args()


def looks_sensitive(text: str) -> bool:
    lowered = text.lower()
    return any(hint in lowered for hint in SECRET_HINTS)


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
    return event


def main() -> int:
    args = parse_args()
    if looks_sensitive(args.summary):
        raise SystemExit(
            "Refusing to log potential secret in summary. Use Vaultwarden reference instead."
        )

    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_file = Path(__file__).resolve().parents[2] / "_runtime" / "events" / f"{date_str}.ndjson"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    event = build_event(args)
    with out_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=True) + "\n")

    print(f"Appended event {event['id']} to {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
