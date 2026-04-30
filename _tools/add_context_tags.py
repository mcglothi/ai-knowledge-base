#!/usr/bin/env python3
"""
add_context_tags.py — Inject 'context:' field into AIKB file frontmatter.

Mapping:
  home-lab/**          -> personal-homelab
  personal/**          -> personal
  personal-projects/** -> personal
  work/**              -> llbean-work
  side-gigs/**         -> personal
  projects/**          -> per-file (see PROJECT_CONTEXT below)
"""

import os
import re
import sys
from pathlib import Path

AIKB_ROOT = Path(__file__).parent.parent

DIR_CONTEXT = {
    "home-lab": "personal-homelab",
    "personal": "personal",
    "personal-projects": "personal",
    "work": "llbean-work",
    "side-gigs": "personal",
}

PROJECT_CONTEXT = {
    "projects/dream-vault.md": "personal",
    "projects/aikb-knowledge-graph.md": "shared",
    "projects/README.md": "shared",
    # zscaler-training.md moved to work/ — not present here anymore
}

YAML_FRONT_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def get_context(rel_path: str) -> str | None:
    parts = rel_path.replace("\\", "/").split("/")
    top = parts[0]
    if top in DIR_CONTEXT:
        return DIR_CONTEXT[top]
    if rel_path in PROJECT_CONTEXT:
        return PROJECT_CONTEXT[rel_path]
    return None


def inject_context(content: str, context: str) -> tuple[str, bool]:
    """Return (new_content, was_changed)."""
    # File already has context tag — skip
    if re.search(r"^context:", content, re.MULTILINE):
        return content, False

    match = YAML_FRONT_RE.match(content)
    if match:
        # Has frontmatter — insert context: after opening ---
        fm_body = match.group(1)
        rest = content[match.end():]
        new_content = f"---\ncontext: {context}\n{fm_body}\n---\n{rest}"
        return new_content, True
    else:
        # No frontmatter — prepend a minimal block
        new_content = f"---\ncontext: {context}\n---\n{content}"
        return new_content, True


def process_dir(top_dir: str) -> tuple[int, int]:
    changed = 0
    skipped = 0
    base = AIKB_ROOT / top_dir
    for path in sorted(base.rglob("*.md")):
        rel = path.relative_to(AIKB_ROOT).as_posix()
        context = get_context(rel)
        if not context:
            print(f"  SKIP (no mapping): {rel}")
            skipped += 1
            continue

        original = path.read_text(encoding="utf-8")
        updated, was_changed = inject_context(original, context)
        if was_changed:
            path.write_text(updated, encoding="utf-8")
            print(f"  + tagged [{context}]: {rel}")
            changed += 1
        else:
            print(f"  . already tagged: {rel}")

    return changed, skipped


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("DRY RUN — no files will be written\n")

    dirs = list(DIR_CONTEXT.keys()) + ["projects"]
    total_changed = 0
    total_skipped = 0

    for d in dirs:
        target = AIKB_ROOT / d
        if not target.exists():
            print(f"[skip] {d}/ not found")
            continue
        print(f"\n[{d}/]")
        if not dry_run:
            c, s = process_dir(d)
            total_changed += c
            total_skipped += s

    print(f"\nDone. {total_changed} files updated, {total_skipped} skipped.")


if __name__ == "__main__":
    main()
