---
tags: [aikb, memory, metadata, schema, governance, retrieval]
status: planning
last_updated: 2026-03-07
---

# AIKB Memory Metadata Contract
**Last Updated:** 2026-03-07
**Summary:** Baseline metadata contract for AIKB canonical docs and memory-producing artifacts. Defines the minimum fields we expect now and the stricter contract that later retrieval, write-gateway, and graph work will build on.

---

## Purpose

This contract exists to make AIKB memory:
- easier to validate
- easier to retrieve and filter
- safer to mutate through tooling
- easier to evolve into graph and lifecycle sidecars

It is intentionally incremental:
- body headers are required now
- frontmatter is required for all new memory-producing docs
- stricter enforcement on older docs can happen gradually as files are touched

## Canonical Markdown Contract (v1)

### Required body fields

Every canonical markdown doc should include:

```md
# Title

**Last Updated:** YYYY-MM-DD
**Summary:** One or two sentences describing current status and scope.
```

### Required frontmatter for new memory-producing docs

```yaml
---
tags: [aikb, memory, example]
status: planning
last_updated: 2026-03-07
---
```

Required frontmatter fields:
- `tags`
- `last_updated`

Recommended frontmatter fields:
- `status`
- `hosts`
- `project`
- `scope`

### Consistency rule

If frontmatter `last_updated` is present, it must match body `**Last Updated:**`.

## Runtime / Proposal Metadata Direction

The next schema pass should standardize these fields across candidates, proposals, graph entities, and retrieval records:

- `type`
- `scope`
- `confidence`
- `freshness`
- `provenance`
- `merge_policy`
- `entity_refs`

These are not all enforced yet, but this is the field set future validators and write-path tooling should target.

## Retrieval Record Metadata (v1)

Normalized retrieval results should now expose:

- `path` — source file path
- `chunk_id` — stable retrieval target identifier
- `section_title` — heading title for markdown-derived chunks when available
- `section_level` — markdown heading depth for canonical chunks

For canonical markdown files:
- `chunk_id` should use `relative/path.md#section-slug`
- whole-document fallback records may use just `relative/path`

This gives future write-gateway and graph work a stable handle that is more precise than file-only references.

## Validation Policy

### Current policy

- Missing title, body `Last Updated`, or body `Summary` is an error.
- Invalid frontmatter is an error.
- Missing frontmatter is currently a warning by default and an error in strict mode.
- Missing or invalid `tags` / `last_updated` in frontmatter is currently a warning by default and an error in strict mode.

### Target policy

Once the repo is cleaned up, frontmatter becomes required for all canonical memory-producing docs in:
- `personal-projects/`
- `projects/`
- `home-lab/`
- `side-gigs/`
- `work/`

## Validation Command

```bash
python3 _tools/memory-pipeline/validate_memory_metadata.py
python3 _tools/memory-pipeline/validate_memory_metadata.py --strict-frontmatter
```

## Near-Term Follow-Ups

- Add schema coverage for lifecycle and retrieval fields.
- Add a lint command to CI or nightly maintenance.
- Auto-suggest fixes for missing frontmatter and mismatched dates.
- Use stable chunk IDs as the next layer above this contract.
