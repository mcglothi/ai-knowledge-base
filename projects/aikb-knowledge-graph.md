---
tags: [aikb, graph, backlinks, search, ui, publish, obsidian]
status: in-progress
last_updated: 2026-03-04
---

# Project: AIKB Knowledge Graph + UI

**Last Updated:** 2026-03-04
**Status:** In progress
**Summary:** Add Obsidian-like discovery features to AIKB: backlinks, graph view, and a lightweight UI for search + navigation.

---

## Goals (Best-in-Class Features)
1. Backlinks (linked + unlinked mentions)
2. Graph view (global + local)
3. Search UI (fast, human-friendly)
4. Publish pipeline (graph + search)
5. Hover preview / quick peek

## Current Build
- ✅ Link graph + backlinks indexer (JSON output)
  - Tool: `_tools/aikb-links/indexer.py`
  - Outputs: `aikb_links.json`, `aikb_backlinks.json`, `aikb_graph.json`
- ✅ Unlinked mentions indexer (Obsidian-style)
  - Output: `aikb_unlinked_mentions.json`
- ✅ Minimal UI (MVP)
  - Path: `_tools/aikb-links/ui/`
  - Features: filename/title search, backlinks, unlinked mentions
- ✅ Content search index (snippet-based)
  - Output: `aikb_content_index.json`
- ✅ Basic visual graph (force layout)
  - Canvas view with selectable nodes
- ✅ QA dashboard (missing links + unlinked mentions)
  - UI tab for triage
- ✅ Static export pipeline
  - `bash _tools/aikb-links/publish.sh`

## Next Milestones
1. Improve graph layout (folder clustering refinement + labels)
2. Optional: publish to aikb.timmcg.net or a new subpath

## Notes
- Start with a static UI that reads JSON artifacts.
- Keep storage local-first; no external services required.
