# Tools
**Last Updated:** 2026-05-01

AIKB tools are organized by product tier so new users can tell what is core versus optional.

## Core
These are part of the standard AIKB product path.

- **memory-pipeline** (`_tools/memory-pipeline/`) — lifecycle, capture, closeout, IM, promotion, and maintenance helpers around `_runtime/`
- **aikb-search** (`_tools/aikb-search/`) — standard search layer for retrieval across the knowledge base

Detailed command surfaces still live in the subdirectory READMEs. This file is the tier map, not the full reference.

## Advanced-but-Core
Useful for mature setups, but not required for first success.

- **Ambient Context Injection** (`_tools/memory-pipeline/ambient_ask.sh`) — wrapper that injects relevant facts before the agent starts
- **tutorial** (`_tools/tutorial.sh`) — onboarding orientation for terminal AI workflows
- **feature-tour** (`_tools/feature-tour.sh`) — guided walkthrough of the AIKB power layer

## Extensions
These are optional capabilities. They may move into dedicated extension paths over time.

Examples include:
- dreaming / nightly consolidation
- temporal graph tooling
- approvals and operator-heavy extras
- proposal/reorg helpers if separated from advanced-core

See [`docs/product-boundaries.md`](../docs/product-boundaries.md) for the current working classification.

## Experimental
Not part of the stable public surface.

Examples include:
- local sidecar / inference helpers
- benchmark and evaluation harnesses
- unfinished automation concepts

## Near-Term Direction
Phase A cleanup is docs-first and sync-safe:
- label tiers clearly
- avoid moving active paths yet
- introduce dedicated extension locations before relocating optional scripts

See [`docs/migration-2026-q2-boundary-cleanup.md`](../docs/migration-2026-q2-boundary-cleanup.md) for migration rules.
