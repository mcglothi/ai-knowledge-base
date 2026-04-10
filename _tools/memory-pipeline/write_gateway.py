#!/usr/bin/env python3
"""Preview or apply chunk-aware markdown writes inside AIKB."""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass
class Section:
    heading: str
    level: int
    start: int
    end: int
    slug: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="AIKB repo root. Defaults to current directory.")
    parser.add_argument("--path", required=True, help="Relative path to target markdown file.")
    parser.add_argument("--chunk-id", default="", help="Target chunk id like path/to/file.md#section-slug")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["replace-section", "append-to-section", "append-to-file"],
        help="How to apply content.",
    )
    parser.add_argument("--content-file", default="", help="Read replacement/appended content from this file.")
    parser.add_argument("--text", default="", help="Inline replacement/appended content.")
    parser.add_argument("--date", default="", help="Override Last Updated date (YYYY-MM-DD).")
    parser.add_argument("--apply", action="store_true", help="Write the file instead of only previewing the diff.")
    return parser.parse_args()


def slugify(text: str) -> str:
    lowered = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return lowered or "section"


def read_content(args: argparse.Namespace) -> str:
    if args.content_file:
        return Path(args.content_file).read_text(encoding="utf-8").rstrip()
    if args.text:
        return args.text.rstrip()
    raise SystemExit("Provide either --content-file or --text.")


def resolve_root(root_arg: str) -> Path:
    root = Path(root_arg).resolve()
    if not (root / "_index.md").exists():
        raise SystemExit(f"Not an AIKB root: {root}")
    return root


def parse_sections(lines: list[str]) -> list[Section]:
    sections: list[Section] = []
    current_heading = "document"
    current_level = 0
    current_start = 0

    for idx, line in enumerate(lines):
        if not line.startswith("#"):
            continue
        if idx > current_start or current_heading != "document":
            sections.append(
                Section(
                    heading=current_heading,
                    level=current_level,
                    start=current_start,
                    end=idx,
                    slug=slugify(current_heading),
                )
            )
        current_heading = line.lstrip("#").strip() or "document"
        current_level = len(line) - len(line.lstrip("#"))
        current_start = idx

    sections.append(
        Section(
            heading=current_heading,
            level=current_level,
            start=current_start,
            end=len(lines),
            slug=slugify(current_heading),
        )
    )
    return sections


def find_section(lines: list[str], chunk_id: str, rel_path: str) -> Section:
    if not chunk_id:
        raise SystemExit("This mode requires --chunk-id.")
    expected_prefix = f"{rel_path}#"
    if not chunk_id.startswith(expected_prefix):
        raise SystemExit(f"chunk_id must start with '{expected_prefix}'")
    target_slug = chunk_id.split("#", 1)[1]
    for section in parse_sections(lines):
        if section.slug == target_slug:
            return section
    raise SystemExit(f"Could not find chunk '{chunk_id}' in {rel_path}")


def normalize_block(text: str) -> list[str]:
    stripped = text.strip("\n")
    if not stripped:
        return []
    return stripped.splitlines()


def update_last_updated(text: str, date_str: str) -> str:
    text = re.sub(r"(?m)^last_updated:\s*\d{4}-\d{2}-\d{2}\s*$", f"last_updated: {date_str}", text, count=1)
    text = re.sub(
        r"(?m)^\*\*Last Updated:\*\*\s*\d{4}-\d{2}-\d{2}(?:\s*\(.*\))?\s*$",
        f"**Last Updated:** {date_str}",
        text,
        count=1,
    )
    return text


def apply_replace_section(lines: list[str], section: Section, content: str) -> list[str]:
    new_lines = normalize_block(content)
    if not new_lines:
        raise SystemExit("Replacement content must not be empty.")
    if not new_lines[0].startswith("#"):
        heading = lines[section.start]
        new_lines = [heading, ""] + new_lines
    return lines[: section.start] + new_lines + lines[section.end :]


def apply_append_to_section(lines: list[str], section: Section, content: str) -> list[str]:
    insert_lines = normalize_block(content)
    if not insert_lines:
        raise SystemExit("Append content must not be empty.")
    before = lines[: section.end]
    after = lines[section.end :]
    if before and before[-1].strip():
        before.append("")
    before.extend(insert_lines)
    if after and after[0].strip():
        before.append("")
    return before + after


def apply_append_to_file(lines: list[str], content: str) -> list[str]:
    insert_lines = normalize_block(content)
    if not insert_lines:
        raise SystemExit("Append content must not be empty.")
    out = list(lines)
    if out and out[-1].strip():
        out.append("")
    out.extend(insert_lines)
    return out


def unified_diff(old_text: str, new_text: str, rel_path: str) -> str:
    diff_lines = difflib.unified_diff(
        old_text.splitlines(),
        new_text.splitlines(),
        fromfile=f"a/{rel_path}",
        tofile=f"b/{rel_path}",
        lineterm="",
    )
    return "\n".join(diff_lines)


def main() -> int:
    args = parse_args()
    root = resolve_root(args.root)
    rel_path = args.path.strip()
    target = (root / rel_path).resolve()
    if root not in target.parents and target != root:
        raise SystemExit(f"Refusing to write outside AIKB root: {target}")
    if not target.exists():
        raise SystemExit(f"Target file does not exist: {target}")
    if target.suffix.lower() != ".md":
        raise SystemExit("write_gateway currently supports markdown files only.")

    content = read_content(args)
    date_str = args.date or datetime.now().strftime("%Y-%m-%d")
    if not DATE_RE.fullmatch(date_str):
        raise SystemExit("Date must be YYYY-MM-DD")

    original_text = target.read_text(encoding="utf-8")
    lines = original_text.splitlines()

    if args.mode == "replace-section":
        section = find_section(lines, args.chunk_id, rel_path)
        updated_lines = apply_replace_section(lines, section, content)
    elif args.mode == "append-to-section":
        section = find_section(lines, args.chunk_id, rel_path)
        updated_lines = apply_append_to_section(lines, section, content)
    else:
        updated_lines = apply_append_to_file(lines, content)

    updated_text = "\n".join(updated_lines).rstrip() + "\n"
    updated_text = update_last_updated(updated_text, date_str)
    diff = unified_diff(original_text, updated_text, rel_path)

    if not diff:
        print("No changes.")
        return 0

    print(diff)
    if not args.apply:
        print("\nPreview only. Re-run with --apply to write changes.")
        return 0

    target.write_text(updated_text, encoding="utf-8")
    print(f"\nApplied changes to {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
