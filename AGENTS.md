# Codex CLI — Global Agent Instructions

**Last Updated:** 2026-03-05
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
| tesla    | `~/Code/` | `~/Code/AIKB/`  |
| mbp-i9   | `~/Code/` | `~/Code/AIKB/`  |

If unrecognized, run `uname -s` and infer likely code root (`~/Code/` on macOS, `~/code/` on Linux). Treat as MCP mode unless a local clone exists.

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

### Step 3 — Load machine + AIKB orientation

Read in this order:

1. `personal/dev-environment/README.md`
2. `personal/dev-environment/{hostname}.md`
3. `_index.md`
4. `_state.yaml`

Use `_index.md` tags or `aikb_search` before loading deeper files. Do not bulk-load unrelated domains.

---

### Step 3b — Register in active sessions

Read and update `_agents/active.md`:

1. If another agent has a Last Write within ~2 hours, pull before each write
2. Add/update row:
   `| Codex CLI | {hostname} | local/MCP | {timestamp} | {brief task description} |`
3. Commit as first AIKB write of the session
4. Remove your row and commit as final session write

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

If in MCP mode (no local clone), skip script execution and write canonical updates directly.
`_runtime/` is non-canonical staging only.

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

---

### Benchmark Shortcut Rule

If the user writes either:

- `Current Benchmark Evaluation for <PRODUCT>`
- `Current Benchamark evaluation for <PRODUCT>` (common misspelling)

then run the benchmark workflow below.

#### Required workflow

1. Parse `<PRODUCT>` and map it to the local repo/docs in `~/Code` or `~/code`.
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
