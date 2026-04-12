# Codex CLI — Global Agent Instructions

**Last Updated:** 2026-04-12 (rev 12)
**Summary:** Streamlined Codex instruction set. Wake-up command replaces manual startup. Session end uses the AIKB stop script.
**Config location:** `AGENTS.md` in the current repository root
**Sync:** `./sync-agents.sh` in AIKB root to propagate changes to project repos

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
  --agent "Codex CLI" --repo "AIKB" --scope "<scope>" --task "<brief task>"
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
- Update `_state.yaml` when: incident opens/resolves, SSL cert changes, new pending item

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

Codex CLI does not currently expose a native Stop hook.

Use one of these paths:

1. Preferred: source `{{LOCAL_PATH}}/_tools/memory-pipeline/codex-wrapper.sh` from your shell config so `aikb-session-stop.sh` runs automatically after Codex exits
2. Manual fallback: run `bash {{LOCAL_PATH}}/_tools/memory-pipeline/aikb-session-stop.sh` before finishing

**Setup:** See `docs/stop-hook-setup.md` for the wrapper and manual fallback workflow.

To manually capture a key decision mid-session:
```bash
python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py capture \
  --agent "Codex CLI" --session-id <id> --type decision \
  --project <file> --summary "<what was decided>"
```

---

## Shutdown Phrases

`lets wrap up` / `let's wrap up` / `lets shut down` / `let's shut down` → **required closeout workflow:**
1. Persist AIKB memory updates (project docs, `_index.md`, `_state.yaml`)
2. `git add` → commit → push for all touched repos
3. Run `bash {{LOCAL_PATH}}/_tools/memory-pipeline/aikb-session-stop.sh` unless the Codex wrapper is already installed
4. Report final sync state (ahead/behind, any uncommitted files)

---

## Efficiency Rules

- Prefer `pgrep`/`ps`/`which` over `ls -R` for diagnostics
- **Full Deployment** → production workflow (DNS, Proxy, SSL)
- **POC** → speed-first (local-only, skip production standards)
- **Deep Trace** → explicit permission for exhaustive diagnostics
