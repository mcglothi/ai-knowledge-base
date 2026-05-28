#!/usr/bin/env python3
"""Memory proposal review/apply CLI for AIKB Memory Core."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib import parse, request


def resolve_server() -> str:
    return os.environ.get("MEMORY_CORE_URL", "http://localhost:8080")


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


def api_call(
    *,
    method: str,
    path: str,
    api_key: str,
    params: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = resolve_server().rstrip("/")
    qs = ""
    if params:
        qs = "?" + parse.urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{base}{path}{qs}"

    data = None
    headers = {"X-API-Key": api_key}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url, method=method, data=data, headers=headers)
    with request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
    if not raw:
        return {}
    return json.loads(raw)


def find_aikb_root() -> Path:
    cands = [Path.home() / "code" / "AIKB", Path.home() / "Code" / "AIKB"]
    for cand in cands:
        if cand.exists() and (cand / "_index.md").exists():
            return cand
    raise SystemExit("Could not locate AIKB root")


def append_proposal_markdown(target_file: Path, proposal: dict[str, Any]) -> None:
    target_file.parent.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%d %H:%M:%S")

    block = [
        "",
        f"## Memory Proposal Applied ({ts})",
        f"- Proposal ID: `{proposal['proposal_id']}`",
        f"- Kind: `{proposal['kind']}`",
        f"- Confidence: `{proposal['confidence']}`",
        f"- Summary: {proposal['summary']}",
    ]
    evidence = proposal.get("evidence", {})
    if evidence.get("event_id"):
        block.append(f"- Evidence Event: `{evidence['event_id']}`")
    block.append("- Payload:")
    block.append("```json")
    block.append(json.dumps(proposal.get("payload", {}), indent=2, sort_keys=True))
    block.append("```")
    target_file.write_text(
        target_file.read_text(encoding="utf-8") + "\n" + "\n".join(block) + "\n",
        encoding="utf-8",
    )


def render_proposal_markdown(proposal: dict[str, Any]) -> str:
    payload = proposal.get("payload", {})
    suggested_file = payload.get("suggested_file") or payload.get("target_file")
    suggested_chunk = payload.get("suggested_chunk_id") or payload.get("chunk_id")
    lines = [
        f"## Memory Proposal Applied ({time.strftime('%Y-%m-%d %H:%M:%S')})",
        "",
        f"- Summary: {proposal['summary']}",
        f"- Proposal ID: `{proposal['proposal_id']}`",
        f"- Kind: `{proposal['kind']}`",
        f"- Confidence: `{proposal['confidence']}`",
    ]
    evidence = proposal.get("evidence", {})
    if evidence.get("event_id"):
        lines.append(f"- Evidence Event: `{evidence['event_id']}`")
    if suggested_file:
        lines.append(f"- Suggested File: `{suggested_file}`")
    if suggested_chunk:
        lines.append(f"- Suggested Chunk: `{suggested_chunk}`")

    compact_payload = {
        key: value
        for key, value in payload.items()
        if key
        not in {
            "content",
            "proposed_markdown",
            "review_notes",
            "raw_payload",
            "full_payload",
            "prompt",
        }
        and value not in ("", None, [], {})
    }
    if compact_payload:
        lines.extend(["", "### Payload Summary", ""])
        for key, value in sorted(compact_payload.items()):
            if isinstance(value, (dict, list)):
                rendered = json.dumps(value, sort_keys=True)
            else:
                rendered = str(value)
            if len(rendered) > 180:
                rendered = rendered[:177] + "..."
            lines.append(f"- `{key}`: {rendered}")
    return "\n".join(lines)


def load_proposal_from_file(path_str: str) -> dict[str, Any]:
    path = Path(path_str).resolve()
    if not path.exists():
        raise SystemExit(f"Proposal file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("Proposal file must contain one JSON object.")
    return data


def resolve_write_target(
    args: argparse.Namespace, proposal: dict[str, Any], aikb_root: Path
) -> tuple[str, str, str, str, bool]:
    normalized, normalization_notes = normalize_proposal_payload(proposal, aikb_root)
    payload = normalized.get("payload", {})
    rel_target = args.file or payload.get("suggested_file") or payload.get("target_file") or ""
    chunk_id = args.chunk_id or payload.get("suggested_chunk_id") or payload.get("chunk_id") or ""
    mode = args.mode or payload.get("apply_mode") or ""
    content = payload.get("proposed_markdown") or payload.get("content") or ""
    used_fallback = bool(normalization_notes)

    if not rel_target:
        rel_target = "_runtime/memory-proposals-applied.md"
        used_fallback = True

    if not content:
        content = render_proposal_markdown(normalized)
        used_fallback = True

    if not mode:
        mode = "append-to-section" if chunk_id else "append-to-file"

    if mode in {"replace-section", "append-to-section"} and not chunk_id:
        mode = "append-to-file"
        used_fallback = True

    return rel_target, chunk_id, mode, content, used_fallback


def normalize_proposal_payload(proposal: dict[str, Any], aikb_root: Path) -> tuple[dict[str, Any], list[str]]:
    normalized = json.loads(json.dumps(proposal))
    payload = normalized.setdefault("payload", {})
    notes: list[str] = []

    summary = str(normalized.get("summary", "")).strip()
    suggested_file = payload.get("suggested_file") or payload.get("target_file") or ""
    suggested_chunk = payload.get("suggested_chunk_id") or payload.get("chunk_id") or ""

    if not suggested_file:
        inferred_file = infer_target_file(aikb_root, summary)
        if inferred_file:
            payload["suggested_file"] = inferred_file
            suggested_file = inferred_file
            notes.append("inferred_file")

    if suggested_file and not suggested_chunk:
        inferred_chunk = infer_chunk_id(aikb_root, suggested_file, summary)
        if inferred_chunk:
            payload["suggested_chunk_id"] = inferred_chunk
            suggested_chunk = inferred_chunk
            notes.append("inferred_chunk")

    if not payload.get("apply_mode"):
        payload["apply_mode"] = "append-to-section" if suggested_chunk else "append-to-file"
        notes.append("inferred_apply_mode")

    if not payload.get("proposed_markdown") and not payload.get("content"):
        payload["proposed_markdown"] = render_proposal_markdown(normalized)
        notes.append("rendered_markdown")

    return normalized, notes


def infer_target_file(aikb_root: Path, summary: str) -> str:
    query = summary.strip()
    if not query:
        return ""
    rows = run_local_memory_search(aikb_root, query)
    for row in rows:
        path = str(row.get("path", ""))
        if not path.endswith(".md"):
            continue
        if path.startswith("_runtime/benchmarks/"):
            continue
        return path
    return ""


def infer_chunk_id(aikb_root: Path, rel_target: str, summary: str) -> str:
    query = summary.strip()
    if not query:
        return ""
    rows = run_local_memory_search(aikb_root, query)
    for row in rows:
        if row.get("path") == rel_target and row.get("chunk_id"):
            return str(row["chunk_id"])
    return ""


def run_local_memory_search(aikb_root: Path, query: str) -> list[dict[str, Any]]:
    search_script = aikb_root / "_tools" / "memory-pipeline" / "memory_search.py"
    cmd = [
        sys.executable,
        str(search_script),
        "--query",
        query,
        "--limit",
        "12",
        "--scope",
        "canonical",
        "--json",
    ]
    res = subprocess.run(cmd, cwd=str(aikb_root), check=False, capture_output=True, text=True)
    if res.returncode != 0:
        return []
    try:
        rows = json.loads(res.stdout)
    except json.JSONDecodeError:
        return []
    return rows


def run_write_gateway(
    *,
    aikb_root: Path,
    rel_target: str,
    chunk_id: str,
    mode: str,
    content: str,
    apply: bool,
) -> subprocess.CompletedProcess[str]:
    gateway = aikb_root / "_tools" / "memory-pipeline" / "write_gateway.py"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".md") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        cmd = [
            sys.executable,
            str(gateway),
            "--root",
            str(aikb_root),
            "--path",
            rel_target,
            "--mode",
            mode,
            "--content-file",
            tmp_path,
        ]
        if chunk_id:
            cmd.extend(["--chunk-id", chunk_id])
        if apply:
            cmd.append("--apply")
        return subprocess.run(cmd, check=False, capture_output=True, text=True)
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass


def cmd_harvest(args: argparse.Namespace) -> int:
    api_key = resolve_api_key(args.api_key)
    if not api_key:
        print("No API key found.")
        return 2
    out = api_call(
        method="POST",
        path="/api/v1/proposals/harvest",
        api_key=api_key,
        payload={"max_events": args.max_events, "state_name": args.state_name},
    )
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    api_key = resolve_api_key(args.api_key)
    if not api_key:
        print("No API key found.")
        return 2
    out = api_call(
        method="GET",
        path="/api/v1/proposals",
        api_key=api_key,
        params={"status": args.status, "kind": args.kind, "limit": args.limit},
    )
    proposals = out.get("proposals", [])
    if not proposals:
        print("No proposals.")
        return 0
    for p in proposals:
        print(
            f"{p['proposal_id']} | {p['status']} | {p['kind']} | {p['confidence']:.2f} | {p['summary'][:120]}"
        )
    return 0


def cmd_review(args: argparse.Namespace, status: str) -> int:
    api_key = resolve_api_key(args.api_key)
    if not api_key:
        print("No API key found.")
        return 2
    out = api_call(
        method="PATCH",
        path=f"/api/v1/proposals/{args.proposal_id}",
        api_key=api_key,
        payload={"status": status, "review_notes": args.notes},
    )
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    proposal: dict[str, Any]
    api_key = ""
    if args.proposal_file:
        proposal = load_proposal_from_file(args.proposal_file)
    else:
        api_key = resolve_api_key(args.api_key)
        if not api_key:
            print("No API key found.")
            return 2

        proposal = api_call(
            method="GET",
            path=f"/api/v1/proposals/{args.proposal_id}",
            api_key=api_key,
        )

    aikb_root = find_aikb_root()
    rel_target, chunk_id, mode, content, used_fallback = resolve_write_target(args, proposal, aikb_root)
    target = (aikb_root / rel_target).resolve()
    if aikb_root.resolve() not in target.parents and target != aikb_root.resolve():
        print(f"Refusing to write outside AIKB root: {target}")
        return 2

    if not target.exists():
        if rel_target == "_runtime/memory-proposals-applied.md":
            target.write_text(
                "# Memory Proposal Applied Log\n\n"
                f"**Last Updated:** {time.strftime('%Y-%m-%d')}\n"
                "**Summary:** Auto-appended proposal applications from Memory Core review flow.\n",
                encoding="utf-8",
            )
        else:
            print(f"Target file does not exist: {target}")
            return 2

    result = run_write_gateway(
        aikb_root=aikb_root,
        rel_target=rel_target,
        chunk_id=chunk_id,
        mode=mode,
        content=content,
        apply=args.write,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    if result.returncode != 0:
        return result.returncode

    if not args.write:
        if used_fallback:
            print("\nPreview used payload normalization/inference because structured proposal fields were incomplete.")
        if "Preview only." not in result.stdout:
            print("\nPreview only. Re-run with --write to apply and mark proposal applied.")
        return 0

    print(f"Applied to: {target}")
    if used_fallback:
        print("Apply path used payload normalization/inference because structured proposal fields were incomplete.")
    if args.proposal_file:
        print("Local proposal file mode: skipped remote proposal status update.")
        return 0

    out = api_call(
        method="PATCH",
        path=f"/api/v1/proposals/{args.proposal_id}",
        api_key=api_key,
        payload={
            "status": "applied",
            "review_notes": args.notes,
            "applied_file": str(target.relative_to(aikb_root)),
        },
    )
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    api_key = resolve_api_key(args.api_key)
    if not api_key:
        print("No API key found.")
        return 2
    out = api_call(
        method="GET",
        path="/api/v1/search",
        api_key=api_key,
        params={"q": args.query, "limit": args.limit},
    )
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


def cmd_prune(args: argparse.Namespace) -> int:
    api_key = resolve_api_key(args.api_key)
    if not api_key:
        print("No API key found.")
        return 2

    summary_filters = [s.strip().lower() for s in args.summary_contains if s.strip()]
    has_filter = bool(summary_filters) or args.older_than_hours > 0 or args.before_ts > 0
    if not has_filter:
        print(
            "Refusing prune without filters. Use --older-than-hours, --before-ts, or --summary-contains."
        )
        return 2

    out = api_call(
        method="GET",
        path="/api/v1/proposals",
        api_key=api_key,
        params={"status": args.status, "kind": args.kind, "limit": args.limit},
    )
    proposals = out.get("proposals", [])
    if not proposals:
        print("No proposals.")
        return 0

    cutoff_ts = int(time.time() - (args.older_than_hours * 3600))
    selected: list[dict[str, Any]] = []
    for proposal in proposals:
        if args.before_ts > 0 and int(proposal["created_ts"]) >= args.before_ts:
            continue
        if args.older_than_hours > 0 and int(proposal["created_ts"]) >= cutoff_ts:
            continue
        summary = str(proposal.get("summary", "")).lower()
        if summary_filters and not any(token in summary for token in summary_filters):
            continue
        selected.append(proposal)
        if len(selected) >= args.max_count:
            break

    if not selected:
        print("No proposals matched prune filters.")
        return 0

    print(
        f"Matched {len(selected)} proposal(s) for status='{args.set_status}' "
        f"(dry_run={args.dry_run})."
    )
    for proposal in selected:
        print(
            f"- {proposal['proposal_id']} | {proposal['kind']} | "
            f"{proposal['created_ts']} | {proposal['summary'][:100]}"
        )

    if args.dry_run:
        return 0

    updated = 0
    for proposal in selected:
        api_call(
            method="PATCH",
            path=f"/api/v1/proposals/{proposal['proposal_id']}",
            api_key=api_key,
            payload={"status": args.set_status, "review_notes": args.notes},
        )
        updated += 1
    print(f"Updated {updated} proposal(s).")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory proposal review/apply CLI")
    parser.add_argument("--api-key", default="", help="Memory Core API key")

    sub = parser.add_subparsers(dest="command", required=True)

    p_harvest = sub.add_parser("harvest", help="Run harvester once")
    p_harvest.add_argument("--max-events", type=int, default=200)
    p_harvest.add_argument("--state-name", default="default")

    p_list = sub.add_parser("list", help="List proposals")
    p_list.add_argument("--status", default="new")
    p_list.add_argument("--kind", default=None)
    p_list.add_argument("--limit", type=int, default=30)

    p_approve = sub.add_parser("approve", help="Approve proposal")
    p_approve.add_argument("proposal_id")
    p_approve.add_argument("--notes", default="")

    p_reject = sub.add_parser("reject", help="Reject proposal")
    p_reject.add_argument("proposal_id")
    p_reject.add_argument("--notes", default="")

    p_apply = sub.add_parser("apply", help="Apply proposal to AIKB file")
    p_apply.add_argument("proposal_id")
    p_apply.add_argument("--proposal-file", default="", help="Local JSON proposal file for offline preview/apply testing.")
    p_apply.add_argument("--file", default="", help="AIKB-relative target file override")
    p_apply.add_argument("--chunk-id", default="", help="Chunk target override like file.md#section-slug")
    p_apply.add_argument(
        "--mode",
        default="",
        choices=["", "replace-section", "append-to-section", "append-to-file"],
        help="Override write mode. Defaults to proposal payload hint or append heuristic.",
    )
    p_apply.add_argument("--notes", default="")
    p_apply.add_argument("--write", action="store_true", help="Actually write and mark proposal as applied.")

    p_search = sub.add_parser("search", help="Run hybrid memory search")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=10)

    p_prune = sub.add_parser("prune", help="Bulk prune noisy proposals")
    p_prune.add_argument("--status", default="new")
    p_prune.add_argument("--kind", default=None)
    p_prune.add_argument("--limit", type=int, default=500)
    p_prune.add_argument("--max-count", type=int, default=200)
    p_prune.add_argument("--older-than-hours", type=float, default=0.0)
    p_prune.add_argument("--before-ts", type=int, default=0)
    p_prune.add_argument(
        "--summary-contains",
        action="append",
        default=[],
        help="Case-insensitive substring filter; repeatable.",
    )
    p_prune.add_argument(
        "--set-status",
        choices=["new", "approved", "rejected", "applied"],
        default="rejected",
    )
    p_prune.add_argument("--notes", default="Pruned noisy proposal")
    p_prune.add_argument("--dry-run", action="store_true")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.command == "harvest":
        return cmd_harvest(args)
    if args.command == "list":
        return cmd_list(args)
    if args.command == "approve":
        return cmd_review(args, "approved")
    if args.command == "reject":
        return cmd_review(args, "rejected")
    if args.command == "apply":
        return cmd_apply(args)
    if args.command == "search":
        return cmd_search(args)
    if args.command == "prune":
        return cmd_prune(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
