#!/usr/bin/env python3
"""Evaluate AIKB search quality with a labeled query set (hit@k, MRR, precision@k)."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from search import search


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", default="", help="Path to eval JSON. Default: _runtime/benchmarks/search-eval-set.json")
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--out", default="", help="Optional markdown report path")
    p.add_argument("--include-related", action="store_true", help="Enable graph expansion during eval")
    return p.parse_args()


def default_dataset_path(root: Path) -> Path:
    return root / "_runtime" / "benchmarks" / "search-eval-set.json"


def default_out_path(root: Path) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return root / "_runtime" / "benchmarks" / f"search-eval-{ts}.md"


def evaluate(cases: list[dict], k: int, include_related: bool) -> dict:
    hits = 0
    reciprocal_ranks: list[float] = []
    precision_scores: list[float] = []
    rows: list[dict] = []

    for case in cases:
        query = case["query"]
        category = case.get("category", "uncategorized")
        expected = [e.lower() for e in case.get("expected_paths", [])]
        results = search(query, top_k=k, include_related=include_related)
        result_paths = [r["file"].lower() for r in results]

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

        rows.append(
            {
                "query": query,
                "category": category,
                "hit": hit,
                "matched_rank": matched_rank,
                "matched_count": matched_count,
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

    category_metrics = {
        cat: {
            "cases": stats["total"],
            "hit_at_k": stats["hits"] / max(1, stats["total"]),
            "mrr": stats["rr_sum"] / max(1, stats["total"]),
            "precision_at_k": stats["precision_sum"] / max(1, stats["total"]),
        }
        for cat, stats in sorted(by_category.items())
    }

    return {
        "total": total,
        "hit_at_k": hits / max(1, total),
        "mrr": sum(reciprocal_ranks) / max(1, total),
        "precision_at_k": sum(precision_scores) / max(1, total),
        "by_category": category_metrics,
        "rows": rows,
    }


def write_report(path: Path, dataset_path: Path, k: int, include_related: bool, result: dict) -> None:
    lines = [
        "# AIKB Search Eval Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"**Dataset:** `{dataset_path}`",
        f"**k:** {k}",
        f"**include_related:** {include_related}",
        "",
        "## Metrics",
        "",
        f"- hit@{k}: {result['hit_at_k']:.3f}",
        f"- precision@{k}: {result['precision_at_k']:.3f}",
        f"- MRR: {result['mrr']:.3f}",
        f"- cases: {result['total']}",
        "",
        "## Metrics by Category",
        "",
        "| Category | Cases | hit@k | precision@k | MRR |",
        "|---|---:|---:|---:|---:|",
    ]

    for category, stats in result.get("by_category", {}).items():
        lines.append(
            f"| {category} | {stats['cases']} | {stats['hit_at_k']:.3f} | {stats['precision_at_k']:.3f} | {stats['mrr']:.3f} |"
        )

    lines.extend(
        [
            "",
        "## Per Query",
        "",
        ]
    )

    for row in result["rows"]:
        lines.append(f"### [{row['category']}] {row['query']}")
        lines.append(f"- hit: {row['hit']}")
        lines.append(f"- matched_rank: {row['matched_rank']}")
        lines.append(f"- matched_count: {row['matched_count']}")
        lines.append(f"- expected_paths: {', '.join(row['expected_paths'])}")
        top = ", ".join(row["top_paths"][:k]) if row["top_paths"] else "(none)"
        lines.append(f"- top_paths: {top}")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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

    result = evaluate(cases, k=max(1, args.k), include_related=args.include_related)

    print(f"hit@{args.k}: {result['hit_at_k']:.3f}")
    print(f"precision@{args.k}: {result['precision_at_k']:.3f}")
    print(f"MRR: {result['mrr']:.3f}")
    print(f"cases: {result['total']}")

    out = Path(args.out) if args.out else default_out_path(root)
    write_report(out, dataset_path, args.k, args.include_related, result)
    print(f"Report: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
