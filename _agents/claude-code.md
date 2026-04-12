# Claude Code — Global Agent Instructions

**Last Updated:** 2026-04-12 (rev 11)
**Summary:** Streamlined Claude Code instruction set. Wake-up command replaces the manual startup protocol. Stop hook handles session end automatically.
**Config location:** `~/.claude/CLAUDE.md`
**Sync:** `cp {{LOCAL_PATH}}/_agents/claude-code.md ~/.claude/CLAUDE.md`

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
  --agent "Claude Code" --repo "AIKB" --scope "<scope>" --task "<brief task>"
```

**MCP mode** (no local clone): use the `github-aikb` MCP server, repo `{{GITHUB_USERNAME}}/AIKB`, branch `main`.
Read via `get_file_contents`. Write via `create_or_update_file` (include current SHA).

---

## Loading Files

1. `wake-up` output covers 90% of session-start context needs
2. Load `_index.md` + `_state.yaml` only if you need the full picture
3. Load specific project files only when the task requires them
4. Use `aikb_search` MCP tool for freeform/diagnostic queries

Do not bulk-load domain folders.

---

## Writing to AIKB

- Edit in place — update `Last Updated` on every file you touch
- Update `_index.md` if project status changes
- Update `_state.yaml` when: incident opens/resolves, SSL cert changes, new pending item

Commit format:
```bash
git -C {{LOCAL_PATH}} add . && git -C {{LOCAL_PATH}} commit -m "AI Update: [file] — [what changed]" && git -C {{LOCAL_PATH}} push origin main
```

Add `⚠️ IN PROGRESS` at top of in-flight files. Replace with `✅` when done.

---

## Credentials

Use your secrets manager (configure in `personal/dev-environment/<hostname>.md`).

**Bitwarden / Vaultwarden pattern:**
```bash
BW_SESSION=$(cat ~/.bw_session)
bw get password "PAT/<Service>/<Name>" --session "$BW_SESSION"
```
- Never run `bw unlock` (hangs interactively)
- Never run `bw status` without `--session`

---

## Session End

The Claude Code **Stop hook** handles session end automatically when configured:
- Captures a closeout event to `_runtime/events/`
- Runs `build_candidates.py`
- Releases `active.md` claim
- Auto-commits `_runtime/` changes

**Setup:** See `docs/stop-hook-setup.md` to configure `aikb-session-stop.sh` in `~/.claude/settings.json`.

---

## Shutdown Phrases

`lets wrap up` / `let's wrap up` / `lets shut down` / `let's shut down` → **required closeout workflow:**
1. Persist AIKB memory updates (project docs, `_index.md`, `_state.yaml`)
2. `git add` → commit → push for all touched repos
3. Report final sync state (ahead/behind, any uncommitted files)

---

## Efficiency Rules

- Prefer `pgrep`/`ps`/`which` over `ls -R` for diagnostics
- **Full Deployment** → production workflow (DNS, Proxy, SSL)
- **POC** → speed-first (local-only, skip production standards)
- **Deep Trace** → explicit permission for exhaustive diagnostics
