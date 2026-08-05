#!/usr/bin/env python3
"""Validate AIKB markdown metadata/frontmatter conventions."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Domain folders shipped by the template. Add your own domains here (or pass
# them explicitly) if your instance uses a different top-level layout.
DEFAULT_PATHS = [
    "personal",
    "projects",
    "runbooks",
    "work",
]

EXCLUDED_PARTS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "_runtime",
}

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BODY_LAST_UPDATED_RE = re.compile(
    r"^\*\*Last Updated:\*\*\s*(\d{4}-\d{2}-\d{2})(?:\s*\(.*\))?\s*$",
    re.MULTILINE,
)
BODY_SUMMARY_RE = re.compile(r"^\*\*Summary:\*\*\s*(.+?)\s*$", re.MULTILINE)
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


@dataclass
class Finding:
    level: str
    path: Path
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root. Defaults to current directory.",
    )
    parser.add_argument(
        "--path",
        action="append",
        dest="paths",
        help="Relative path to validate. May be passed multiple times.",
    )
    parser.add_argument(
        "--strict-frontmatter",
        action="store_true",
        help="Treat missing or incomplete frontmatter as errors instead of warnings.",
    )
    parser.add_argument(
        "--include-readmes",
        action="store_true",
        help="Also validate README.md files. By default, only non-README markdown docs are checked.",
    )
    return parser.parse_args()


def iter_markdown_files(root: Path, targets: list[str], include_readmes: bool) -> list[Path]:
    files: list[Path] = []
    for target in targets:
        base = root / target
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            rel = path.relative_to(root)
            if any(part in EXCLUDED_PARTS for part in rel.parts):
                continue
            if not include_readmes and path.name.lower() == "readme.md":
                continue
            files.append(path)
    return files


def split_frontmatter(text: str) -> tuple[dict | None, str]:
    if not text.startswith("---\n"):
        return None, text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return None, text
    _, remainder = parts
    frontmatter_text = text[len("---\n") : len(text) - len(remainder) - len("\n---\n")]
    data = parse_simple_frontmatter(frontmatter_text)
    return data, remainder


def parse_simple_frontmatter(frontmatter_text: str) -> dict:
    data: dict[str, object] = {}
    for raw_line in frontmatter_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"Invalid frontmatter line: {raw_line}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if inner:
                data[key] = [item.strip() for item in inner.split(",")]
            else:
                data[key] = []
        elif value.startswith('"') and value.endswith('"'):
            data[key] = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            data[key] = value[1:-1]
        else:
            data[key] = value
    return data


def add_finding(findings: list[Finding], level: str, path: Path, message: str) -> None:
    findings.append(Finding(level=level, path=path, message=message))


def validate_markdown(path: Path, root: Path, strict_frontmatter: bool) -> list[Finding]:
    findings: list[Finding] = []
    rel = path.relative_to(root)
    text = path.read_text(encoding="utf-8")

    try:
        frontmatter, body = split_frontmatter(text)
    except Exception as exc:  # pragma: no cover - defensive parse guard
        add_finding(findings, "ERROR", rel, f"frontmatter parse failed: {exc}")
        return findings

    title_match = TITLE_RE.search(body)
    if not title_match:
        add_finding(findings, "ERROR", rel, "missing H1 title")

    body_last_updated_match = BODY_LAST_UPDATED_RE.search(body)
    if not body_last_updated_match:
        add_finding(findings, "ERROR", rel, "missing body '**Last Updated:** YYYY-MM-DD'")
        body_last_updated = None
    else:
        body_last_updated = body_last_updated_match.group(1)

    summary_match = BODY_SUMMARY_RE.search(body)
    if not summary_match:
        add_finding(findings, "ERROR", rel, "missing body '**Summary:** ...'")

    if frontmatter is None:
        level = "ERROR" if strict_frontmatter else "WARN"
        add_finding(findings, level, rel, "missing YAML frontmatter")
        return findings

    tags = frontmatter.get("tags")
    fm_last_updated = frontmatter.get("last_updated")

    if not isinstance(tags, list) or not tags or not all(isinstance(tag, str) for tag in tags):
        level = "ERROR" if strict_frontmatter else "WARN"
        add_finding(findings, level, rel, "frontmatter 'tags' should be a non-empty list of strings")

    if not isinstance(fm_last_updated, str) or not DATE_RE.match(fm_last_updated):
        level = "ERROR" if strict_frontmatter else "WARN"
        add_finding(findings, level, rel, "frontmatter 'last_updated' should be YYYY-MM-DD")
    elif body_last_updated and fm_last_updated != body_last_updated:
        add_finding(
            findings,
            "ERROR",
            rel,
            f"frontmatter last_updated ({fm_last_updated}) does not match body Last Updated ({body_last_updated})",
        )

    status = frontmatter.get("status")
    if status is not None and not isinstance(status, str):
        add_finding(findings, "ERROR", rel, "frontmatter 'status' must be a string when present")

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    paths = args.paths or DEFAULT_PATHS
    files = iter_markdown_files(root, paths, args.include_readmes)

    all_findings: list[Finding] = []
    for path in files:
        all_findings.extend(validate_markdown(path, root, args.strict_frontmatter))

    errors = [finding for finding in all_findings if finding.level == "ERROR"]
    warns = [finding for finding in all_findings if finding.level == "WARN"]

    print(f"Validated {len(files)} markdown files.")
    for finding in all_findings:
        print(f"{finding.level}: {finding.path} :: {finding.message}")

    print(f"Summary: {len(errors)} error(s), {len(warns)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
