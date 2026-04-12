# Gemini CLI — Global Agent Instructions

**Last Updated:** 2026-04-12 (rev 11)
**Summary:** Streamlined Gemini instruction set. Wake-up command replaces manual startup.
**Config location:** `~/.gemini/GEMINI.md`
**Sync:** `cp {{LOCAL_PATH}}/_agents/gemini.md ~/.gemini/GEMINI.md`

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

```bash
python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py capture \
  --agent "Gemini CLI" --session-id <id> --type decision \
  --project <file> --summary "<what was decided>"

python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py release-session --agent "Gemini CLI"
```

---

## Efficiency Rules

- Prefer `pgrep`/`ps`/`which` over `ls -R` for diagnostics
- **Full Deployment** → production workflow (DNS, Proxy, SSL)
- **POC** → speed-first (local-only, skip production standards)
- **Deep Trace** → explicit permission for exhaustive diagnostics
