# Gemini CLI — Global Agent Instructions

**Last Updated:** 2026-04-12 (rev 12)
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
git -C {{LOCAL_PATH}} pull && python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py wake-up
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
  --agent "Gemini CLI" --session-id <id> --type decision \
  --project <file> --summary "<what was decided>"
```

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
1. New decision not yet in AIKB? → `python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py capture --type decision --summary "..."`. Already captured? Skip.
2. Cross-agent handoff needed? → write `session_state.md`. Not a handoff? Skip.
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
