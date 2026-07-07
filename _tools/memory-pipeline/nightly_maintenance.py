#!/usr/bin/env python3
"""Nightly memory maintenance: extraction, dream consolidation, reorg queueing, graph refresh, compaction, and eval."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--date", default="", help="Runtime date (YYYY-MM-DD). Defaults to today UTC")
    p.add_argument("--allow-future-date", action="store_true", help="Allow --date values after today UTC")
    p.add_argument("--compact-archive-raw", action="store_true", help="Archive raw historical event files as gzip")
    p.add_argument("--compact-older-than-days", type=int, default=21)
    p.add_argument("--reorg-limit", type=int, default=30)
    p.add_argument("--run-search-eval", action="store_true", help="Run memory_search eval harness")
    p.add_argument("--strict", action="store_true", help="Exit non-zero if any maintenance step fails")
    return p.parse_args()


def run_step(cmd: list[str], cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()


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


def main() -> int:
    args = parse_args()
    here = Path(__file__).resolve().parent
    root = here.parents[1]
    date_str = resolve_runtime_date(args.date, allow_future=args.allow_future_date)

    compact_step = [sys.executable, str(here / "compact_events.py"), "--older-than-days", str(args.compact_older_than_days)]
    if args.compact_archive_raw:
        compact_step.append("--archive-raw")

    steps = [
        [sys.executable, str(here / "build_candidates.py"), "--date", date_str],
        [sys.executable, str(here / "dream_cycle.py"), "--date", date_str],
        [sys.executable, str(here / "autonomous_reorg.py"), "--limit", str(args.reorg_limit)],
        [sys.executable, str(here / "queue_reorg_suggestions.py")],
        [sys.executable, str(here / "build_temporal_graph.py")],
        compact_step,
        # Refresh access/feedback ranking signals even on commit-free days
        # (otherwise the access boost never decays between index runs).
        [sys.executable, str(root / "_tools" / "aikb-search" / "usage_stats.py")],
    ]

    # Optional LLM entity enrichment: exits 0 when no local endpoint is up,
    # so LLM-less hosts stay green. Needs the aikb-search venv (numpy).
    enrich_py = root / "_tools" / "aikb-search" / "llm_enrich.py"
    venv_python = root / "_tools" / "aikb-search" / ".venv" / "bin" / "python"
    if enrich_py.exists() and venv_python.exists():
        steps.append([str(venv_python), str(enrich_py)])

    if args.run_search_eval:
        eval_py = here / "eval_memory_search.py"
        if eval_py.exists():
            steps.append([sys.executable, str(eval_py), "--k", "5"])

    log_dir = root / "_runtime" / "maintenance"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"nightly-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.log"

    lines = [
        f"# Nightly maintenance {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"runtime_date={date_str}",
    ]
    failed = False

    for cmd in steps:
        rc, out = run_step(cmd, cwd=root)
        lines.append(f"\n$ {' '.join(cmd)}")
        if out:
            lines.append(out)
        lines.append(f"exit={rc}")
        if rc != 0:
            failed = True

    log_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Nightly maintenance log: {log_file}")
    if failed:
        print("One or more maintenance steps failed (see log).")
        return 1 if args.strict else 0
    print("Nightly maintenance completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
