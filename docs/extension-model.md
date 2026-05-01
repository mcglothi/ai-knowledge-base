# AIKB Extension Model
**Status:** Draft working model
**Last Updated:** 2026-05-01

## Purpose
This document explains where new features should live as AIKB evolves.

It exists to prevent scope creep in the public template and to keep contributors from placing every useful idea into the default product surface.

---

## Decision Rule
Ask these questions in order:

1. Is this required for shared, durable, inspectable context across agents, sessions, and machines?
2. Does every AIKB user need it for first success?
3. Would a new user be confused if this appeared in the main onboarding path?
4. Does it introduce platform-specific, environment-specific, or heavy runtime dependencies?
5. Is it still experimental or not yet production-ready?

If the answer to #1 and #2 is yes, it likely belongs in **Core**.
If it is useful but not required for first success, it likely belongs in **Advanced-but-Core**.
If it is optional, specialized, or dependency-heavy, it likely belongs in **Extensions**, **Companion**, or **Experimental**.

---

## Tier Definitions

### Core
Part of the default AIKB promise.

Examples:
- knowledge store and schema
- `runtime_cli.py`
- wake-up / closeout lifecycle
- search
- Agent IM
- Mind Meld
- promotion/governance pipeline

### Advanced-but-Core
Important for mature use, but not required before first value.

Examples:
- template sync discipline
- claim/release workflows
- token economy guidance
- maintenance/review helpers
- deeper architecture notes
- handoff patterns

### Extensions
Optional capabilities that build on AIKB but are not required for the standard product story.

Examples:
- dream cycle
- temporal graph tooling
- approvals/control surfaces
- proposal/reorg helpers if split from advanced-core
- platform adapters

### Companion Projects
Useful related surfaces that should not define the main product.

Examples:
- UI/HUD surfaces
- demo sites
- environment-specific bundles
- domain-specific operating stacks

### Experimental
Not stable enough for the main product surface.

Examples:
- sidecar/local inference helpers
- eval harnesses
- ranking/scoring experiments
- unfinished automation concepts

---

## Placement Guidelines

### Put it in Core when:
- removing it would weaken the core AIKB promise
- users need it in most installations
- it is lightweight, stable, and product-defining

### Put it in Advanced-but-Core when:
- it supports long-term successful use
- it should stay in the main repo
- it should not dominate onboarding or homepage messaging

### Put it in Extensions when:
- it is optional but useful
- it adds complexity or extra dependencies
- it is a power-user feature, not a first-run feature

### Put it in Companion when:
- it demonstrates AIKB in a specific context
- it is better treated as a separate surface or example
- it is not necessary for the default template

### Put it in Experimental when:
- it is incomplete
- install/runtime assumptions are not stable
- it would create support burden if treated as standard

---

## Process for New Features
1. Classify the feature before adding it.
2. If unclear, default away from Core.
3. Document the tier in the relevant README or doc.
4. If moving an existing feature, follow the migration policy in `docs/migration-2026-q2-boundary-cleanup.md`.
5. Do not move active paths without compatibility planning.

---

## Current Working Bias
AIKB should bias toward:
- a smaller public surface
- strong defaults
- optional power layers
- sync-safe evolution

When in doubt, keep the public template simpler and move complexity outward.
