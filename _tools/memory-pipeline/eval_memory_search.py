#!/usr/bin/env python3
"""Evaluate memory_search.py quality with a labeled query set."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


# Ablation modes. "memory" drives memory_search.py; "mcp" drives the
# aikb-search hybrid+graph engine (needs its venv / index built).
MODES: dict[str, dict] = {
    "keyword": {"engine": "memory", "flags": ["--no-semantic"]},
    "hybrid": {"engine": "memory", "flags": []},
    "hybrid-no-recency": {"engine": "memory", "flags": ["--no-recency"]},
    "mcp-hybrid": {"engine": "mcp", "flags": []},
    "mcp-no-graph": {"engine": "mcp", "flags": ["--no-graph"]},
    "mcp-no-usage": {"engine": "mcp", "flags": ["--no-usage"]},
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", default="", help="Path to eval JSON. Default: _runtime/benchmarks/search-eval-set.json")
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--out", default="", help="Optional markdown report path")
    p.add_argument("--scope", default="all", choices=["all", "runtime", "events", "candidates", "canonical"])
    p.add_argument("--include-rejected", action="store_true")
    p.add_argument("--no-semantic", action="store_true")
    p.add_argument("--runs-per-query", type=int, default=1, help="Run each query multiple times and average latency.")
    p.add_argument(
        "--modes",
        default="",
        help=f"Comma-separated ablation modes to compare ({', '.join(MODES)}), or 'all'. "
        "Omit for the classic single-run behavior.",
    )
    return p.parse_args()


def default_dataset_path(root: Path) -> Path:
    return root / "_runtime" / "benchmarks" / "search-eval-set.json"


def default_out_path(root: Path) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return root / "_runtime" / "benchmarks" / f"memory-search-eval-{ts}.md"


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, math.ceil((pct / 100.0) * len(ordered)) - 1))
    return ordered[idx]


def mcp_python(root: Path) -> str:
    """Prefer the aikb-search venv python (has fastembed etc.), else fall back."""
    venv_python = root / "_tools" / "aikb-search" / ".venv" / "bin" / "python"
    return str(venv_python) if venv_python.exists() else sys.executable


def run_query(
    root: Path,
    query: str,
    k: int,
    scope: str,
    include_rejected: bool,
    no_semantic: bool,
    runs_per_query: int,
    engine: str = "memory",
    extra_flags: list[str] | None = None,
) -> tuple[list[dict], float]:
    if engine == "mcp":
        cmd = [
            mcp_python(root),
            str(root / "_tools" / "aikb-search" / "search.py"),
            "--query",
            query,
            "--top-k",
            str(k),
            "--json",
        ]
        cmd.extend(extra_flags or [])
    else:
        cmd = [
            sys.executable,
            str(root / "_tools" / "memory-pipeline" / "memory_search.py"),
            "--query",
            query,
            "--limit",
            str(k),
            "--scope",
            scope,
            "--json",
        ]
        if include_rejected:
            cmd.append("--include-rejected")
        if no_semantic:
            cmd.append("--no-semantic")
        cmd.extend(extra_flags or [])

    durations_ms: list[float] = []
    payload: list[dict] | None = None
    for _ in range(max(1, runs_per_query)):
        started = time.perf_counter()
        proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
        durations_ms.append((time.perf_counter() - started) * 1000.0)
        if proc.returncode != 0:
            raise RuntimeError(f"memory_search failed for query {query!r}: {proc.stderr or proc.stdout}")
        if payload is None:
            payload = json.loads(proc.stdout)
    return payload or [], sum(durations_ms) / len(durations_ms)


def evaluate(
    cases: list[dict],
    root: Path,
    k: int,
    scope: str,
    include_rejected: bool,
    no_semantic: bool,
    runs_per_query: int,
    engine: str = "memory",
    extra_flags: list[str] | None = None,
) -> dict:
    hits = 0
    reciprocal_ranks: list[float] = []
    precision_scores: list[float] = []
    latencies_ms: list[float] = []
    rows: list[dict] = []

    for case in cases:
        query = case["query"]
        category = case.get("category", "uncategorized")
        expected = [e.lower() for e in case.get("expected_paths", [])]
        results, avg_latency_ms = run_query(
            root,
            query,
            k,
            scope,
            include_rejected,
            no_semantic,
            runs_per_query,
            engine=engine,
            extra_flags=extra_flags,
        )
        # memory_search emits "path"; the aikb-search engine emits "file".
        result_paths = [(r.get("path") or r.get("file") or "").lower() for r in results]
        latencies_ms.append(avg_latency_ms)

        matched_rank = None
        matched_count = 0
        for i, rp in enumerate(result_paths, 1):
            ok = any(exp in rp for exp in expected)
            if ok:
                matched_count += 1
                if matched_rank is None:
                    matched_rank = i

        hit = matched_rank is not None
        if hit:
            hits += 1
            reciprocal_ranks.append(1.0 / matched_rank)
        else:
            reciprocal_ranks.append(0.0)

        precision_scores.append(matched_count / max(1, k))

        risk_flags: list[str] = []
        if not hit:
            risk_flags.append("miss")
        elif matched_rank and matched_rank > 1:
            risk_flags.append("buried")
        if matched_count == 0:
            risk_flags.append("no_expected_in_top_k")
        elif matched_count == 1 and k > 1:
            risk_flags.append("low_precision")

        rows.append(
            {
                "query": query,
                "category": category,
                "hit": hit,
                "matched_rank": matched_rank,
                "matched_count": matched_count,
                "avg_latency_ms": avg_latency_ms,
                "risk_flags": risk_flags,
                "top_paths": result_paths,
                "expected_paths": expected,
            }
        )

    total = len(cases)
    by_category: dict[str, dict] = {}
    for row in rows:
        cat = row["category"]
        bucket = by_category.setdefault(
            cat,
            {"total": 0, "hits": 0, "rr_sum": 0.0, "precision_sum": 0.0},
        )
        bucket["total"] += 1
        if row["hit"]:
            bucket["hits"] += 1
            bucket["rr_sum"] += 1.0 / row["matched_rank"]
        bucket["precision_sum"] += row["matched_count"] / max(1, k)
        bucket.setdefault("latencies_ms", []).append(row["avg_latency_ms"])

    category_metrics = {
        cat: {
            "cases": stats["total"],
            "hit_at_k": stats["hits"] / max(1, stats["total"]),
            "mrr": stats["rr_sum"] / max(1, stats["total"]),
            "precision_at_k": stats["precision_sum"] / max(1, stats["total"]),
            "avg_latency_ms": sum(stats["latencies_ms"]) / max(1, len(stats["latencies_ms"])),
            "p95_latency_ms": percentile(stats["latencies_ms"], 95),
        }
        for cat, stats in sorted(by_category.items())
    }

    risky_rows = [row for row in rows if row["risk_flags"]]

    return {
        "total": total,
        "hit_at_k": hits / max(1, total),
        "mrr": sum(reciprocal_ranks) / max(1, total),
        "precision_at_k": sum(precision_scores) / max(1, total),
        "avg_latency_ms": sum(latencies_ms) / max(1, len(latencies_ms)),
        "p50_latency_ms": percentile(latencies_ms, 50),
        "p95_latency_ms": percentile(latencies_ms, 95),
        "max_latency_ms": max(latencies_ms) if latencies_ms else 0.0,
        "risky_queries": len(risky_rows),
        "by_category": category_metrics,
        "risky_rows": risky_rows,
        "rows": rows,
    }


def write_report(
    path: Path,
    dataset_path: Path,
    k: int,
    scope: str,
    include_rejected: bool,
    no_semantic: bool,
    result: dict,
) -> None:
    lines = [
        "# Memory Search Eval Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"**Dataset:** `{dataset_path}`",
        f"**k:** {k}",
        f"**scope:** {scope}",
        f"**include_rejected:** {include_rejected}",
        f"**semantic_mode:** {'disabled' if no_semantic else 'auto'}",
        f"**runs_per_query:** {result.get('runs_per_query', 1)}",
        "",
        "## Metrics",
        "",
        f"- hit@{k}: {result['hit_at_k']:.3f}",
        f"- precision@{k}: {result['precision_at_k']:.3f}",
        f"- MRR: {result['mrr']:.3f}",
        f"- cases: {result['total']}",
        f"- avg_latency_ms: {result['avg_latency_ms']:.1f}",
        f"- p50_latency_ms: {result['p50_latency_ms']:.1f}",
        f"- p95_latency_ms: {result['p95_latency_ms']:.1f}",
        f"- max_latency_ms: {result['max_latency_ms']:.1f}",
        f"- risky_queries: {result['risky_queries']}",
        "",
        "## Metrics by Category",
        "",
        "| Category | Cases | hit@k | precision@k | MRR | avg ms | p95 ms |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]

    for category, stats in result.get("by_category", {}).items():
        lines.append(
            f"| {category} | {stats['cases']} | {stats['hit_at_k']:.3f} | {stats['precision_at_k']:.3f} | {stats['mrr']:.3f} | {stats['avg_latency_ms']:.1f} | {stats['p95_latency_ms']:.1f} |"
        )

    lines.extend(["", "## At-Risk Queries", ""])

    if result.get("risky_rows"):
        for row in result["risky_rows"]:
            lines.append(f"- [{row['category']}] {row['query']} :: {', '.join(row['risk_flags'])} :: matched_rank={row['matched_rank']} :: avg_latency_ms={row['avg_latency_ms']:.1f}")
    else:
        lines.append("- None")

    lines.extend(["", "## Per Query", ""])

    for row in result["rows"]:
        lines.append(f"### [{row['category']}] {row['query']}")
        lines.append(f"- hit: {row['hit']}")
        lines.append(f"- matched_rank: {row['matched_rank']}")
        lines.append(f"- matched_count: {row['matched_count']}")
        lines.append(f"- avg_latency_ms: {row['avg_latency_ms']:.1f}")
        lines.append(f"- risk_flags: {', '.join(row['risk_flags']) if row['risk_flags'] else '(none)'}")
        lines.append(f"- expected_paths: {', '.join(row['expected_paths'])}")
        top = ", ".join(row["top_paths"][:k]) if row["top_paths"] else "(none)"
        lines.append(f"- top_paths: {top}")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_comparison_report(
    path: Path,
    dataset_path: Path,
    k: int,
    results_by_mode: dict[str, dict],
) -> None:
    lines = [
        "# Memory Search Ablation Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"**Dataset:** `{dataset_path}`",
        f"**k:** {k}",
        "",
        "## Mode Comparison",
        "",
        f"| Mode | Engine | hit@{k} | precision@{k} | MRR | avg ms | p95 ms | risky |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for mode, result in results_by_mode.items():
        engine = MODES[mode]["engine"]
        lines.append(
            f"| {mode} | {engine} | {result['hit_at_k']:.3f} | {result['precision_at_k']:.3f} "
            f"| {result['mrr']:.3f} | {result['avg_latency_ms']:.1f} "
            f"| {result['p95_latency_ms']:.1f} | {result['risky_queries']} |"
        )

    for mode, result in results_by_mode.items():
        lines.extend(["", f"## At-Risk Queries — {mode}", ""])
        risky = result.get("risky_rows", [])
        if risky:
            for row in risky:
                lines.append(
                    f"- [{row['category']}] {row['query']} :: {', '.join(row['risk_flags'])} "
                    f":: matched_rank={row['matched_rank']}"
                )
        else:
            lines.append("- None")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def resolve_modes(spec: str) -> list[str]:
    if spec.strip().lower() == "all":
        return list(MODES)
    modes = [m.strip() for m in spec.split(",") if m.strip()]
    unknown = [m for m in modes if m not in MODES]
    if unknown:
        raise SystemExit(f"Unknown mode(s): {', '.join(unknown)}. Available: {', '.join(MODES)}")
    return modes


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    dataset_path = Path(args.dataset) if args.dataset else default_dataset_path(root)

    if not dataset_path.exists():
        raise SystemExit(f"Dataset not found: {dataset_path}")

    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    if not cases:
        raise SystemExit("Dataset has no cases.")

    if args.modes:
        modes = resolve_modes(args.modes)
        results_by_mode: dict[str, dict] = {}
        for mode in modes:
            spec = MODES[mode]
            print(f"[{mode}] running {len(cases)} cases via {spec['engine']} engine...")
            result = evaluate(
                cases,
                root=root,
                k=max(1, args.k),
                scope=args.scope,
                include_rejected=args.include_rejected,
                no_semantic=False,
                runs_per_query=max(1, args.runs_per_query),
                engine=spec["engine"],
                extra_flags=spec["flags"],
            )
            results_by_mode[mode] = result
            print(
                f"[{mode}] hit@{args.k}={result['hit_at_k']:.3f} "
                f"precision@{args.k}={result['precision_at_k']:.3f} MRR={result['mrr']:.3f} "
                f"avg_ms={result['avg_latency_ms']:.1f} risky={result['risky_queries']}"
            )

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # "search-eval" in the name keeps this out of the index (see indexer SKIP_FILE_RE)
        out = Path(args.out) if args.out else root / "_runtime" / "benchmarks" / f"memory-search-eval-ablation-{ts}.md"
        write_comparison_report(out, dataset_path=dataset_path, k=args.k, results_by_mode=results_by_mode)
        print(f"Report: {out}")
        return 0

    result = evaluate(
        cases,
        root=root,
        k=max(1, args.k),
        scope=args.scope,
        include_rejected=args.include_rejected,
        no_semantic=args.no_semantic,
        runs_per_query=max(1, args.runs_per_query),
    )
    result["runs_per_query"] = max(1, args.runs_per_query)

    print(f"hit@{args.k}: {result['hit_at_k']:.3f}")
    print(f"precision@{args.k}: {result['precision_at_k']:.3f}")
    print(f"MRR: {result['mrr']:.3f}")
    print(f"cases: {result['total']}")
    print(f"avg_latency_ms: {result['avg_latency_ms']:.1f}")
    print(f"p95_latency_ms: {result['p95_latency_ms']:.1f}")
    print(f"risky_queries: {result['risky_queries']}")

    out = Path(args.out) if args.out else default_out_path(root)
    write_report(
        out,
        dataset_path=dataset_path,
        k=args.k,
        scope=args.scope,
        include_rejected=args.include_rejected,
        no_semantic=args.no_semantic,
        result=result,
    )
    print(f"Report: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
