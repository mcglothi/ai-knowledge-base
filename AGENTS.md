# Codex CLI — Agent Instructions (rev 16, 2026-04-21)
Sync: `./sync-agents.sh` in AIKB root to propagate to project repos

## AIKB
Repo: `mcglothi/AIKB` · Local: `/home/mcglothi/code/AIKB/`
MCP mode (no local clone): server `github-aikb`, branch `main` · Read: `get_file_contents` · Write: `create_or_update_file` (include SHA)

## Session Start
wake-up optional — use only when cross-session continuity needed:
`python3 /home/mcglothi/code/AIKB/_tools/memory-pipeline/runtime_cli.py wake-up --agent "Codex CLI"`
Claim: `runtime_cli.py claim-session --agent "Codex CLI" --repo "AIKB" --scope "<scope>" --task "<task>"`

## Loading
Order: wake-up output → `_index.md`+`_state.yaml` if needed → specific files on demand.
Use `aikb_search` for freeform queries. Never bulk-load domain folders.

## Writing
Edit in place · Update `Last Updated` · Update `_index.md` on status change · Update `_state.yaml` on: incident, SSL cert, pending item
Commit: `git -C /home/mcglothi/code/AIKB add . && git -C /home/mcglothi/code/AIKB commit -m "AI Update: [file] — [what]" && git -C /home/mcglothi/code/AIKB push origin main`
In-flight: `⚠️ IN PROGRESS` · Done: `✅`

## Git — Project Repos
main: typos, minor docs · Branch: features, assets, anything hard to reverse
`git checkout -b codex/<desc>` → `git push -u origin HEAD` → `gh pr create --fill`
Binary assets: always new filename (GitHub CDN caches by URL). AIKB: push `_runtime/` + canonical docs direct to main.

## Credentials
Secrets manager. Delinea: `personal/vaults/delinea.yaml` → name→ID → `tss secret --secret <id> --field <field>`
MCP discovery: new tool/platform → check `_tools/mcp-registry.yaml` → if found, log to `_pending_approvals.md` (type: mcp-discovery, priority: low)

## Session End
No native stop hook. Options:
1. Preferred: source `codex-wrapper.sh` from shell config → `aikb-session-stop.sh` runs on exit
2. Fallback: `bash /home/mcglothi/code/AIKB/_tools/memory-pipeline/aikb-session-stop.sh` before finishing
Setup: `docs/stop-hook-setup.md`
Mid-session capture: `runtime_cli.py capture --agent "Codex CLI" --session-id <id> --type decision --summary "<what>" [--rejected "<alt>"] [--assumptions "<ctx>"] [--invariants "<incomplete>"] [--next-step "<next>"]`

## Shutdown
"lets wrap up" | "let's wrap up" | "lets shut down" | "let's shut down" →
1. Persist AIKB updates (`_index.md`, `_state.yaml`, project docs)
2. commit+push all repos
3. `bash /home/mcglothi/code/AIKB/_tools/memory-pipeline/aikb-session-stop.sh` (unless wrapper installed)
4. Report sync state

## IM — Self-Messaging
Triggers (fuzzy, case-insensitive): "leave yourself a note" · "note for next time" · "remember for next session" · "jot this down" · "make a note" · "don't forget this"
`python3 /home/mcglothi/code/AIKB/_tools/memory-pipeline/runtime_cli.py im send --from "Codex CLI" --to "Codex CLI" --severity info --summary "<subject>" --body "<detail>" --mirror-sent`
summary=one line · severity=review if needs attention next session · don't ack · reply: "Noted — I'll see that next session."

## Cross-Agent Awareness
See `docs/mind-meld.md`. Load when asked about other agents or avoiding duplicate work.

## Efficiency
`pgrep`/`ps`/`which` over `ls -R` · Full Deployment=production (DNS+Proxy+SSL) · POC=local only · Deep Trace=explicit permission

## Checkpoints
Commit at: phase done | major decision | before risky op | long conversation. Prefer small focused commits (multi-agent conflict reduction).
Mark in-flight: `⚠️ IN PROGRESS — picked up by next session` · Done: `✅`

## Template Sync
`runtime_cli.py template-sync --auto-check` (weekly) · Never `./sync.sh` without approval · After sync: `./sync-agents.sh <project-path>` for downstream repos

## Caveman Modes
Activate: "caveman [lite|full|ultra]" or "less tokens" · Deactivate: "normal mode"
Auto-clarity: drop for security, confirmations, or complexity. Resume after.

| Mode | Rules |
|------|-------|
| lite | No filler/hedging. Professional but tight. |
| full | Drop articles, fragments OK. Default caveman. |
| ultra | Abbreviate technicals (auth/cfg/fn), arrows (X→Y). |

Code, tech-terms, errors: always exact. Pattern: `[thing] [action] [reason]. [next].`

## Token Economy
Compact (/compact) when: sub-task done | output >50 lines | 3 reads | ~35 turns.
MANDATORY: At turn 35 or context >80%, `runtime_cli.py capture` then ask user for `/compact`. Stop until cleared.
Before compact: `runtime_cli.py capture --agent "Codex CLI" --session-id <id> --type decision --summary "<what>" [--rejected "<alt>"] [--assumptions "<ctx>"] [--invariants "<incomplete>"] [--next-step "<next>"]`
Field guide: `docs/token-economy.md` · After compact: `aikb_search` to recall.
Bash output: cap everything — `| head -50` · `2>&1 | tail -20` · `| grep -c`.

## Wrap-up
1. `runtime_cli.py closeout --phrase "<phrase>"`
2. (if graph artifacts tracked) `build_temporal_graph.py` + `dream_cycle.py`
3. git add+commit+push all
4. Remove from `_agents/active.md`
