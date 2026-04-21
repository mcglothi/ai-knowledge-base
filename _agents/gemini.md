# Gemini CLI — Global Agent Instructions

**Last Updated:** 2026-04-21 (rev 13)
**Summary:** Streamlined Gemini instruction set. Wake-up command replaces manual startup. Stop hook handles session end automatically.
**Config location:** `~/.gemini/GEMINI.md`
**Sync:** `cp {{LOCAL_PATH}}/_agents/gemini-cli.md ~/.gemini/GEMINI.md`

---

## AI Knowledge Base (AIKB)

Private repo at `{{GITHUB_USERNAME}}/AIKB`. Local clone: `{{LOCAL_PATH}}/` (set during `install.sh`).

Add your machines to `personal/dev-environment/README.md`.

---

## Session Start

```bash
git -C {{LOCAL_PATH}} pull && python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py wake-up --agent "Gemini CLI"
```

Then register your session:

```bash
python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py claim-session \
  --agent "Gemini CLI" --repo "AIKB" --scope "<scope>" --task "<brief task>"
```

**MCP mode** (no local clone): use the `github-aikb` MCP server, repo `{{GITHUB_USERNAME}}/AIKB`, branch `main`.

---

## Loading Files

1. `wake-up` output covers 90% of session-start context needs
2. Load `_index.md` + `_state.yaml` only if you need the full picture
3. Use `aikb_search` for freeform/diagnostic queries

Do not bulk-load domain folders.

---

## Writing to AIKB

- Edit in place — update `Last Updated` on every file you touch
- Update `_index.md` if project status changes
- Update `_state.yaml` for incidents, SSL dates, or pending items

Commit format:
```bash
git -C {{LOCAL_PATH}} add . && git -C {{LOCAL_PATH}} commit -m "AI Update: [file] — [what changed]" && git -C {{LOCAL_PATH}} push origin main
```

Add `⚠️ IN PROGRESS` at top of in-flight files. Replace with `✅` when done.

---

## Credentials

Use your secrets manager. Reference secrets as `[Stored in Vaultwarden: <Item Name>]`.

---

## Session End

Stop hook fires automatically (`~/.gemini/settings.json`). No manual action needed.

**Setup:** See `docs/stop-hook-setup.md` to configure `aikb-session-stop.sh` in `~/.gemini/settings.json`.

To manually capture a key decision mid-session:

```bash
python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py capture \
  --agent "Gemini CLI" --session-id <id> \
  --type decision \
  --project <target-file> \
  --summary "what was decided or found" \
  --rejected "what was tried/considered and ruled out, and why" \
  --assumptions "things true right now that won't be obvious from the code" \
  --invariants "things intentionally incomplete or broken until X happens" \
  --next-step "exact next action when this work resumes"
```

The goal is that a future agent reading this capture can continue without asking "why didn't you just...?" or "wait, is X done yet?" Only `--summary` is required.

---

## Agent Self-Messaging — IM Triggers

When the operator says any of the following (interpret fuzzily, case-insensitive):

- "leave yourself a note"
- "note this for next time" / "note that for next time"
- "remember this for the next session" / "remember that for next time"
- "jot this down" / "jot that down"
- "make a note of that"
- "save that for next session" / "save this for later"
- "don't forget this" (addressed to you)

**Action:** Send an IM to yourself using the IM feature. This message will appear automatically in the next session's wake-up output.

```bash
python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py im send \
  --from "Gemini CLI" --to "Gemini CLI" \
  --severity info \
  --summary "<one-line subject: what to remember>" \
  --body "<full context, next step, or whatever the operator just said to note>" \
  --mirror-sent
```

- Keep `--summary` to a single clear sentence — it's what shows in wake-up.
- Use `--body` for the full detail (context, next-step, links).
- Use `--severity review` if the note needs deliberate attention next session.
- Do NOT ack the message — leaving it unacked is what makes it appear at the next wake-up.
- After sending, tell the operator: "Noted — I'll see that at the start of the next session."

---

## Efficiency Rules

- Prefer `pgrep`/`ps`/`which` over `ls -R` for diagnostics
- **Full Deployment** → production workflow (DNS, Proxy, SSL)
- **POC** → speed-first (local-only, skip production standards)
- **Deep Trace** → explicit permission for exhaustive diagnostics

---

### Template update hygiene

If this AIKB repo includes `sync.sh` and `.aikb-config.d/template-sync-state.json`, prefer:

`python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py template-sync --auto-check`

That helper reads the saved check window and only runs `./sync.sh --check` when the template check is stale or missing, or when the operator asks about updates.

- Use `--check` only for safe periodic nudges.
- Weekly is the default cadence; if the operator wants a different rhythm, update it with `python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py template-sync --set-interval <days>`.
- If updates are available, summarize the changed framework paths first.
- Do not run `./sync.sh` without operator approval, because it updates tracked framework files.
- After a framework sync, remind the operator that downstream Codex project repos may also need `./sync-agents.sh`.

### Token Economy

Every turn resends the full context. A 100-turn session costs ~25× a 20-turn session. See `docs/token-economy.md` for the full strategy.

**Compact triggers — run `/compress` when ANY of these occur:**
- A discrete sub-task finishes (PR created, doc written, research phase done)
- Any single tool output exceeds ~50 lines — compress before continuing
- 3+ consecutive file reads completed
- ~40 turns with no prior compress this session

**AIKB is your memory buffer.** Anything written via `runtime_cli.py capture` survives `/compress` and is recallable with `aikb_search`. Compress freely once it's captured.

**Sequence before compressing:**

**Before compressing, capture what a fresh agent would need to continue without re-reading the whole session:**

```bash
python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py capture \
  --agent "Gemini CLI" --session-id <id> \
  --type decision \
  --project <target-file> \
  --summary "what was decided or found" \
  --rejected "what was tried/considered and ruled out, and why" \
  --assumptions "things true right now that won't be obvious from the code" \
  --invariants "things intentionally incomplete or broken until X happens" \
  --next-step "exact next action when this work resumes"
```

Only `--summary` is required. Add the others when mid-implementation or when the session involved ruling out alternatives.

**What each field is for:**

| Field | Captures | Example |
|-------|----------|---------|
| `--summary` | The decision or finding | "switched auth to JWT" |
| `--rejected` | Ruled-out alternatives + reason | "session tokens rejected: don't work across services" |
| `--assumptions` | Currently-true context not in code | "API gateway not yet enforcing token expiry" |
| `--invariants` | Intentionally incomplete states | "refresh token table exists but seeder not written yet" |
| `--next-step` | Exact resumption point | "write token refresh endpoint, then update middleware" |

**Pre-compact checklist — run through this before compacting:**
- [ ] Is there unfinished implementation in flight? → use `--invariants` and `--next-step`
- [ ] Were alternatives considered and rejected this session? → use `--rejected`  
- [ ] Are there assumptions a fresh agent could easily get wrong? → use `--assumptions`
- [ ] Is `session_state.md` needed? (another agent might pick this up) → write it now
- Already captured? Skip directly to compact — don't duplicate.

3. Run `/compress`

**After compressing:** use `aikb_search "what was decided about X"` to recall — faster than re-reading files.

**Bash output:** cap everything that could be large — it stays in context all session:
```bash
command | head -50 && command 2>&1 | tail -20 && command | grep -c pattern
```

---

### Wrap-up workflow

When the operator uses a closing phrase like `lets wrap up for now` or `let's shut down`, perform these steps before ending the session:

1. **Capture Closeout:** If runtime tools are available, record a structured closeout event:
   `python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py closeout --phrase "<operator phrase>"`
2. **Optional advanced maintenance:** only if this repo intentionally tracks graph/dream artifacts, run:
   `python3 {{LOCAL_PATH}}/_tools/memory-pipeline/build_temporal_graph.py`
   `python3 {{LOCAL_PATH}}/_tools/memory-pipeline/dream_cycle.py`
3. **Final Sync:** Add, commit, and push all changes (including tracked `_runtime/` updates) to the remote repository.
4. **Release Session:** Remove your entry from `_agents/active.md`.
