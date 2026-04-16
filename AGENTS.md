# Codex CLI — Global Agent Instructions

**Last Updated:** 2026-04-12 (rev 2)
**Summary:** Streamlined Codex instruction set. Wake-up command replaces the manual startup protocol. Session end: run the AIKB stop script before finishing.
**Config location:** `AGENTS.md` in the current repo root
**Sync:** `cp ~/code/AIKB/_agents/codex.md <project>/AGENTS.md` or `./sync-agents.sh`

---

## AI Knowledge Base (AIKB)

Private repo at `mcglothi/AIKB`. Local clone: `~/code/AIKB/` on all machines.

| Hostname | Code root | AIKB path |
|----------|-----------|-----------|
| feynman  | ~/code/   | ~/code/AIKB/ |
| tesla    | ~/code/   | ~/code/AIKB/ |
| mbp-i9   | ~/code/   | ~/code/AIKB/ |

---

## Session Start

```bash
git -C ~/code/AIKB pull && python3 ~/code/AIKB/_tools/memory-pipeline/runtime_cli.py wake-up
python3 ~/code/AIKB/_tools/memory-pipeline/runtime_cli.py claim-session \
  --agent "Codex CLI" --repo "AIKB" --scope "<scope>" --task "<brief task>"
```

**MCP mode** (no local clone): use `github-aikb` MCP server, repo `mcglothi/AIKB`, branch `main`.

---

## Loading Files

1. `wake-up` output covers 90% of session-start context needs
2. Load `_index.md` + `_state.yaml` only if you need the full picture
3. Load specific project files only when the task requires them
4. Use `aikb_search` MCP tool for freeform/diagnostic queries — **search before assuming**

Do not bulk-load domain folders.

---

## Writing to AIKB

- Edit in place — never append corrections below stale content
- Update `Last Updated` on every file you touch
- Update `_index.md` if project status changes
- Update `_state.yaml` when: incident opens/resolves, SSL cert changes, new pending item

Commit format:
```bash
git -C ~/code/AIKB add . && git -C ~/code/AIKB commit -m "AI Update: [file] — [what changed]" && git -C ~/code/AIKB push origin main
```

Add `⚠️ IN PROGRESS` at top of in-flight files. Replace with `✅` when done.

---

## Credentials

Vault at `vault.home.timmcg.net`. Session file: `~/.bw_session`.

- Never run `bw unlock` (hangs) or `bw status` without `--session`
- If `~/.bw_session` exists, assume valid. Only ask for `bwu` if `bw get` fails
- Never store clear-text secrets in AIKB — use `[Stored in Vaultwarden: <Item Name>]`

---

## Session End (Codex has no Stop hook — run this before finishing)

```bash
bash ~/code/AIKB/_tools/memory-pipeline/aikb-session-stop.sh
```

---

## Shutdown Phrases

`lets wrap up` / `let's wrap up` / `lets shut down` / `let's shut down` → required closeout:
1. Persist AIKB updates (project docs, `_index.md`, `_state.yaml`)
2. `git add` → commit → push for all touched repos
3. Run `aikb-session-stop.sh`
4. Report sync state (ahead/behind, any uncommitted files)

---

## Efficiency Rules

- Prefer `pgrep`/`ps`/`which` over directory listings for diagnostics
- **Full Deployment** keyword → production workflow: DNS, Proxy, SSL, AIKB docs
- **POC** keyword → speed-first: local-only, skip production standards
- **Deep Trace** keyword → explicit permission for exhaustive diagnostics
- Context > 50% or turns > 50 → compact, but persist to AIKB first

---

## Codex-Specific Shortcuts

### Benchmark Shortcut

Trigger: `Current Benchmark Evaluation for <PRODUCT>`

1. Build current-state snapshot from local sources first
2. Research comparable open-source projects online
3. Confer with Gemini (`gemini -p`) for second opinion
4. Save to `_runtime/benchmarks/<product-slug>-YYYY-MM-DD.md`

Output: executive summary → comparison table → 5 lead/5 lag/5 borrow → prioritized roadmap (7/30/90 day) → sources

### Memory Calibration Shortcut

Trigger: `calibrate memory` or `cmd: calibrate memory`

1. Review Memory Core proposal queue
2. Group into patterns, not individual items
3. Apply: reject transient chatter / approve documented facts / keep ambiguous for follow-up
4. Summarize: decisions made, patterns learned, hygiene rules to tighten

### Operator Intent Capture

If a terse operator phrase required >1 lookup step, capture it before session end:
- File: `home-lab/runbooks/operator-intents.md`
- Template: `_templates/operator-intent-template.md`
- Include: exact phrase, execution path, verification command
