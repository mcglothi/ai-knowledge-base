# AIKB Migration Plan — 2026 Q2 Boundary Cleanup
**Status:** Draft for team review
**Last Updated:** 2026-05-01

## Purpose
This document defines how AIKB should reorganize its public template **without breaking existing private AIKB instances** when users run `sync.sh`.

Current known user base is small, but trust is high-value. The migration approach should optimize for:
- no unexpected breakage
- gradual transitions
- explicit deprecation
- clear operator messaging

---

## Migration Principles

### 1. Compatibility First
Do not break existing private AIKB instances simply because framework files move.

If paths change, provide a transition layer first.

### 2. Additive Before Destructive
First release:
- add new structure
- update docs
- preserve old entry points

Later release:
- warn on deprecated entry points
- remove only after at least one stable transition window

### 3. Preserve Existing Automation
Assume current users may have local hooks, wrappers, or scripts pointing at existing framework paths.

This includes:
- stop hooks
- shell wrappers
- launchd/cron hooks
- custom agent instructions
- local helper scripts

### 4. Migration Must Be Explained
Every structural change should be documented in one operator-facing migration note.

### 5. Sync Should Be Safe By Default
`sync.sh` should favor safe compatibility over aggressive cleanup.

---

## Highest-Risk Migration Areas
The riskiest breakages are the ones that fail silently.

Priority order:
1. stop-hook paths with absolute references into AIKB
2. launchd/cron jobs referencing moved scripts
3. agent instruction files with hardcoded script or doc paths
4. doc links referenced by agent overlays or prompts

These risks should be checked explicitly before any structural move.

---

## Required Pre-Move Audit
Before moving any script or doc path, audit references across:
- `_agents/`
- setup/install scripts
- shell wrappers and stop hooks
- scheduler setup scripts
- docs
- sync logic

At minimum, grep for exact path references before Phase B changes ship.

---

## Proposed Rollout Strategy

### Phase A — Classification + Docs Only
Safe, no-break phase.

Actions:
- publish `docs/product-boundaries.md`
- publish this migration note
- update README language
- label tools/docs as core, advanced, extension, companion, or legacy
- avoid moving executable paths yet

Goal:
- improve clarity without breaking any private instance

---

### Phase B — Introduce New Canonical Paths with Compatibility Shims
Begin structural cleanup carefully.

Actions:
- create new extension-oriented directories
- move optional features to new canonical locations
- leave wrapper/shim files at old paths
- old paths forward to new paths and emit a deprecation note
- update docs to prefer new paths
- update agent instruction files before planning wrapper removal

Example:
- old: `_tools/memory-pipeline/dream_cycle.py`
- new: `_tools/extensions/dreaming/dream_cycle.py`
- transition: old path remains as compatibility entry point for one or more release cycles

Goal:
- allow docs and new installs to use the clean structure
- allow existing installs to keep working during transition

---

### Phase C — Remove Deprecated Paths
Only after sufficient transition time.

Actions:
- remove old wrappers
- update sync/check messaging
- simplify docs to new structure only

Prerequisites:
- minimum 60 days have passed since the compatibility release shipped
- at least one successful sync has been confirmed from a non-owner instance

Without both conditions, do not remove compatibility wrappers.

---

## Compatibility Techniques

### 1. Wrapper Scripts / Shim Files
When moving scripts, keep a small wrapper at the old path that calls the new path.

Use when:
- script paths may be referenced directly by local automation
- agent instructions or docs may lag behind

### 2. Redirect Documentation
If docs move or split:
- keep old doc with short pointer note when practical
- or update links everywhere in the same release

### 3. Deprecation Messaging
Compatibility wrappers should print a short warning such as:

> This path is deprecated and will be removed in a future release. Use: `<new path>`

For nightly or scheduled jobs, print the warning on every run during the transition period.

### 4. Sync Messaging
When major structural changes land, `sync.sh` should surface a brief notice like:

> AIKB framework boundary update detected. Optional features have moved to new extension paths. Compatibility wrappers are included. See `docs/migration-2026-q2-boundary-cleanup.md`.

---

## Paths Most Likely to Need Migration Care
Likely high-risk changes:
- `_tools/memory-pipeline/*` script moves
- stop hook and wrapper references
- install/setup instructions
- docs links referenced by agent instructions
- optional automation scripts used by existing users manually

Likely lower-risk changes:
- new docs additions
- new extension folders added without moving active paths yet
- presentation/demo content being reorganized

---

## Draft Safe Sequence for Existing Users

### Release 1
- add boundary docs
- rewrite public messaging
- mark optional features clearly
- no path breakage

### Release 2
- introduce new extension directories
- move optional features to new canonical locations
- leave compatibility wrappers in old locations
- update docs to prefer new paths

### Release 3
- remove deprecated wrappers only after warning period and successful sync adoption

---

## What Existing Users Should Never Experience
Users should never run `sync.sh` and discover that:
- wake-up no longer works
- closeout hooks silently fail
- IM paths break
- search commands disappear
- moved files break local cron/launchd tasks without warning
- agents silently stop loading referenced docs or scripts after path moves

Any change with that risk must ship behind a compatibility layer first.

---

## Launch Readiness Requirement
Before promoting AIKB more broadly, there should be at least one successful test of:
1. fresh public install
2. sync from an older private instance through the compatibility release
3. continued operation of core lifecycle commands after sync
4. verification that stop hooks still execute closeout successfully

---

## Open Implementation Notes
- stop-hook path safety should be treated as the loudest migration warning
- scheduler-installed jobs for `nightly_maintenance.py` need especially explicit deprecation messaging
- agent instruction files must be updated before shims are retired
- doc moves require a path-reference audit across `_agents/`

---

## Proposed Next Step
After review, define:
- the first batch of paths that can be safely relabeled without moving
- the first batch of extension candidates to move behind compatibility wrappers
- the operator-facing sync messaging for the first migration release
