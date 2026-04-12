# Codex CLI — Global Agent Instructions

**Last Updated:** 2026-04-08
**Summary:** Source-of-truth Codex instructions for loading, using, and updating AIKB across machines.
**Config location:** `AGENTS.md` in the current repository root
**Sync from local clone:** `cp {code_root}/AIKB/_agents/codex.md {project_root}/AGENTS.md`
**Bulk sync helper:** `{code_root}/AIKB/sync-agents.sh`

> This file is the source of truth for Codex AIKB behavior. Keep local `AGENTS.md` aligned when this file changes.

---

## File content (copy everything below this line)

---

# Codex — Global Agent Instructions

## AI Knowledge Base (AIKB)

All personal projects, infrastructure, and client work are documented in the AIKB — a private GitHub repo (`mcglothi/AIKB`) that serves as persistent memory across sessions and machines.

AIKB is accessed in one of two modes depending on whether a local clone exists. Determine the mode at session start.

---

### Step 1 — Identify the machine

Run `hostname`. Resolve the code root from this table:

| Hostname | Code root | AIKB local path |
|----------|-----------|-----------------|
| feynman  | `~/code/` | `~/code/AIKB/`  |
| tesla    | `~/code/` | `~/code/AIKB/`  |
| mbp-i9   | `~/code/` | `~/code/AIKB/`  |

If unrecognized, run `uname -s` and infer likely code root (`~/code/` on macOS, `~/code/` on Linux). Treat as MCP mode unless a local clone exists.

---

### Step 2 — Check for local AIKB clone (sets access mode)

```bash
ls {AIKB local path}
```

#### Local mode (clone exists) — preferred

1. Pull first: `git -C {AIKB path} pull`
2. Read/write files directly
3. Commit and push changes

**Commit format:**
```bash
git -C {AIKB path} add . && git -C {AIKB path} commit -m "AI Update: [file] — [what changed]" && git -C {AIKB path} push origin main
```

#### MCP mode (no local clone) — online only

Use the `github-aikb` MCP server against `mcglothi/AIKB` `main`.

- Read: `get_file_contents`
- Write: `create_or_update_file` (include SHA for updates)
- Use the same commit message format as local mode

If this machine will be reused, clone AIKB at the end of the session.

---

### Efficiency & Diagnostic Rules

- **High-Signal Diagnostics:** When troubleshooting services or installations, prioritize `pgrep`, `ps`, and `which` over exhaustive directory listings (`ls -R`). 
- **macOS Service Heuristic:** If `brew services list` reports an error but `pgrep` confirms the process is running, trust `pgrep`. Inspect the process environment (`ps -wwfp <pid>`) to find configuration paths.
- **Context Management & Token Economy:** Aggressively manage context to minimize token usage and latency.
    - **Proactive Compaction:** Do not wait for auto-compaction. Manually invoke **`/compact`** (Codex) or **`/compress`** (Gemini) when a sub-task (Research, Strategy) is complete or after receiving high-volume tool output.
    - **Thresholds:** Compact if context exceeds 50% of model limit or turns > 50.
    - **Persistence Mandate:** Before compacting, you MUST persist all critical findings, decisions, and current state to AIKB (canonical docs, `_runtime/scratchpads/`, or a `session_state.md` checkpoint).
    - **Monitor:** Use **`/stats model`** (Gemini) or equivalent to track token usage.
- **Keyword: Full Deployment:** Triggers a production-ready workflow including DNS (Pi-hole), Proxy (NPM), SSL (Vaultwarden/Cloudflare), and AIKB documentation.
- **Keyword: POC (Proof of Concept):** Triggers a "speed-first" workflow. Ignore production standards, use local-only networking, and minimize external dependency checks.
- **Keyword: Deep Trace:** Explicit permission to perform exhaustive diagnostics and read many files. Use only when a root cause is elusive after initial high-signal checks.

---

### Step 3 — Load machine + AIKB orientation

Read in this order:

1. `personal/dev-environment/README.md`
2. `personal/dev-environment/{hostname}.md`
3. `_index.md`
4. `_state.yaml`

Use `_index.md` tags or `aikb_search` before loading deeper files. Do not bulk-load unrelated domains.

If the task mentions `Memory Core`, `aikb-memory-core`, or an AIKB runtime extension, also read:

5. `_tools/extensions/registry.md`
6. `_tools/extensions/<extension-id>/README.md`

---

### Step 3b — Register in active sessions

Read and update `_agents/active.md`:

1. If another agent has a Last Write within ~2 hours, pull before each write
2. Add/update row:
   `| Codex CLI | {hostname} | local/MCP | {timestamp} | {repo name or AIKB} | {scope/path glob} | {brief task description} |`
   Preferred helper:
   `python3 _tools/memory-pipeline/runtime_cli.py claim-session --agent "Codex CLI" --repo "<repo>" --scope '<scope>' --task "<task>"`
3. For work outside AIKB itself, claim the external repo and the narrowest useful scope you can describe
4. If you encounter unexpected modified/untracked files, or any other evidence of work you did not create, re-read `_agents/active.md` and run `python3 _tools/memory-pipeline/runtime_cli.py check-repo --path <repo-or-file>` before editing. Treat dirty unclaimed repos as possible crash-recovery work until proven otherwise.
5. Commit as first AIKB write of the session
6. Remove your row and commit as final session write
   Preferred helper:
   `python3 _tools/memory-pipeline/runtime_cli.py release-session --agent "Codex CLI"`

Also read `_agents/registry.md` when collaborating across tools.

---

### Credentials

All API tokens and service keys are stored in Vaultwarden at `vault.home.timmcg.net`.

- Never store or print clear-text secrets in AIKB
- Reference secrets as `[Stored in Vaultwarden: <Item Name>]`
- If `~/.bw_session` exists, attempt `bw get` directly
- If credential retrieval fails due session expiry, ask user to run `bwu`

---

### When to update AIKB

Update AIKB before ending any session that produced reusable knowledge:

- State changes, completed work, unresolved blockers, incidents, gotchas
- Edit in place (do not append stale corrections)
- Update `Last Updated` on each touched markdown file
- Update `_index.md` when project status changes
- Update `_state.yaml` when pending items/incidents/cert dates change

For partial handoffs, add: `⚠️ IN PROGRESS`.

### Runtime memory pipeline (recommended for long sessions)

Use runtime staging to capture high-signal events before canonical merge.

In local mode, run:

```bash
# Log a key event
python3 _tools/memory-pipeline/ingest_runtime.py --agent codex --session-id <id> --type decision --project <target-file> --summary "<fact>"

# Build candidate queue
python3 _tools/memory-pipeline/build_candidates.py

# Review/update candidate state
python3 _tools/memory-pipeline/review_candidates.py --id <cand_id> --status approved|rejected|merged --reviewer codex --notes "..."
```

**Memory Hygiene:** When all items in a source candidate file reach a terminal state (`merged` or `rejected`), delete the `.yaml` file from `_runtime/candidates/` to prevent cruft.

If in MCP mode (no local clone), skip script execution and write canonical updates directly.
`_runtime/` is non-canonical staging only.

### Extension discovery

For extension work, treat `_tools/extensions/registry.md` as the source of truth for where runtime code lives.
Do not assume a standalone sibling repo unless the registry or extension README explicitly says so.

---

### Operator intent capture (prevent repeat lookup)

If a terse operator phrase (example: `WoL feynman`) required more than one lookup/search step, capture it as an operator intent before session end.

Source of truth:
- `home-lab/runbooks/operator-intents.md`

Capture minimum:
- exact phrase(s) user is likely to use
- exact execution path that worked
- verification command(s)
- optional cleanup/rollback

Use template when adding new entries:
- `_templates/operator-intent-template.md`

When receiving terse operator commands in future sessions, check `operator-intents.md` first before broader search.

---

### Session resilience

Use checkpoint commits for multi-phase or long sessions:

- After each major phase
- Before risky operations
- When launching long-running tasks

Prefer small focused commits to reduce merge conflicts with other active agents.

### Operator shutdown semantics (must-follow)

If the operator says phrases like:
- `lets shut down`
- `let's shut down`
- `lets wrap up`
- `let's wrap up`

interpret this as a required **closeout workflow**, not just conversation end.

Required closeout workflow:
1. Persist AIKB memory updates for the session (relevant project docs, `_index.md`, `_state.yaml` when applicable).
   - Capture a structured runtime closeout event first when possible:
     `~/code/AIKB/_tools/home-lab/aikb closeout --phrase "<operator phrase>"`
2. Ensure git is cleanly updated for the repo(s) touched:
   - `git add` relevant files
   - commit with clear message
   - push to the tracked remote branch
3. Verify and report final sync status:
   - branch vs upstream (`ahead/behind`)
   - any intentionally uncommitted files and why
4. Only then conclude the session.

If push fails (network/auth/conflict), report it explicitly and provide exact next action.

---

### Benchmark Shortcut Rule

If the user writes either:

- `Current Benchmark Evaluation for <PRODUCT>`
- `Current Benchamark evaluation for <PRODUCT>` (common misspelling)

then run the benchmark workflow below.

#### Required workflow

1. Parse `<PRODUCT>` and map it to the local repo/docs in `~/code` or `~/code`.
2. Build a current-state snapshot from local sources first (architecture, deployment state, tooling, known caveats).
3. Perform deep online research on comparable open-source projects and recent changes.
4. **Confer with Gemini** as a second-opinion reviewer before final recommendations.
   - Use Gemini in non-interactive oracle mode (`-p`) when available.
   - Ask Gemini for strengths/gaps/roadmap and disagreements with your own analysis.
5. Synthesize into a practical operator-facing roadmap for home-lab constraints.
6. Save a benchmark note to AIKB:
   - `_runtime/benchmarks/<product-slug>-YYYY-MM-DD.md`
7. Include the file path in the final response.

#### Output format (required)

1. Executive summary (max 10 bullets)
2. Comparison table (our stack vs alternatives)
3. Lead/Lag analysis:
   - 5 areas we lead
   - 5 areas we lag
   - 5 ideas to borrow now
4. Prioritized roadmap:
   - next 7 days
   - next 30 days
   - next 90 days
   For each item: `impact`, `effort`, `dependencies`, `success metric`
5. Failure modes to watch
6. Top 3 actions to start this week
7. Sources (links)

#### Quality bar

- Be opinionated and practical, not generic.
- Prefer self-hosted/open-source paths.
- Explicitly call out what changed since the last benchmark if prior benchmark files exist.

### Memory Calibration Shortcut Rule

If the user writes either:

- `cmd: calibrate memory`
- `calibrate memory`

then run the memory calibration workflow below.

#### Required workflow

1. Review the live AIKB Memory Core proposal queue first.
2. Group proposals into patterns instead of treating every item as unique.
3. Recommend default actions by pattern:
   - `reject`
   - `approve`
   - `apply`
   - `keep for follow-up`
4. Surface only the smallest ambiguous set for user review.
5. Learn from the user's decisions during the pass and apply that policy consistently to the rest of the queue.
6. Promote durable product backlog, runbook knowledge, workflow intent, and already-documented facts into canonical AIKB docs/state when appropriate.
7. Reject transient chatter, speculative advice, implementation progress blurts, duplicate fact/task copies, and stale debugging noise.
8. End with a short summary:
   - decision patterns learned
   - what was auto-rejected / auto-applied / approved / kept for follow-up
   - which upstream harvest/hygiene rules should be tightened so future review is faster

#### Default policy

- Keep domain behavior and real workflow/automation intent.
- Auto-apply things that are already documented or should clearly become canonical backlog/docs.
- Reject speculative, partial-progress, advisory, and transient operational chatter.
- Only turn confirmations into tasks when they contain meaningful feature/detail text.
- If something looks important but is not yet verified in-repo, keep it as follow-up instead of overstating it.

### Shutdown Wrap Shortcut Rule

If the user writes something like:

- `lets shut down for now`
- `let's shut down for now`
- `lets shut down for the day`
- `let's shut down for the day`
- `wrap up for the day`

then run the shutdown-wrap workflow below before ending the session.

#### Required workflow

1. Check AIKB git status and call out any uncommitted or untracked changes.
2. Distinguish meaningful repo changes from transient artifacts like `__pycache__`, `.pyc`, journals, and scratch outputs.
3. Check whether the Memory Core proposal queue still has `new` items.
4. Check `_agents/active.md` so no stale active-session entry is left behind.
5. Summarize whether there is any obvious commit, push, cleanup, or review work still pending before shutdown.
6. If the repo is still dirty, do not imply shutdown is clean; explicitly say what is still open.

#### Output requirement

- End with a concise “safe to stop” vs “loose ends remain” summary.
- If cleanup/commit/push is still needed, say so directly instead of implying the session is fully wrapped.
