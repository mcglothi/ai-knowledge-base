# Claude Code — Agent Instructions (rev 13, 2026-04-21)
Sync: `cp {{LOCAL_PATH}}/_agents/claude-code.md ~/.claude/CLAUDE.md`

## AIKB
Repo: `{{GITHUB_USERNAME}}/AIKB` · Local: `{{LOCAL_PATH}}/`
MCP mode (no local clone): server `github-aikb`, branch `main` · Read: `get_file_contents` · Write: `create_or_update_file` (include SHA)

## Session Start
wake-up optional — use only when cross-session continuity needed:
`python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py wake-up --agent "Claude Code"`
Claim: `runtime_cli.py claim-session --agent "Claude Code" --repo "AIKB" --scope "<scope>" --task "<task>"`

## Loading
Order: wake-up output → `_index.md`+`_state.yaml` if needed → specific files on demand.
Use `aikb_search` for freeform queries. Never bulk-load domain folders.

## Writing
Edit in place · Update `Last Updated` · Update `_index.md` on status change · Update `_state.yaml` on: incident, SSL cert, pending item
Commit: `git -C {{LOCAL_PATH}} add . && git -C {{LOCAL_PATH}} commit -m "AI Update: [file] — [what]" && git -C {{LOCAL_PATH}} push origin main`
In-flight: `⚠️ IN PROGRESS` · Done: `✅`

## Git — Project Repos
main: typos, minor docs · Branch: features, assets, anything hard to reverse
`git checkout -b claude/<desc>` → `git push -u origin HEAD` → `gh pr create --fill`
Binary assets: always new filename (GitHub CDN caches by URL). AIKB: push `_runtime/` + canonical docs direct to main.

## Credentials
BW: `BW_SESSION=$(cat ~/.bw_session) && bw get password "PAT/<Service>/<Name>" --session "$BW_SESSION"` · Never: `bw unlock` · Never: `bw status` without `--session`
Delinea: `personal/vaults/delinea.yaml` → name→ID → `tss secret --secret <id> --field <field>`
MCP discovery: new tool/platform → check `_tools/mcp-registry.yaml` → if found, log to `_pending_approvals.md` (type: mcp-discovery, priority: low)

## Session End
Stop hook handles closeout automatically. Setup: `docs/stop-hook-setup.md`.

## Shutdown
"lets wrap up" | "let's wrap up" | "lets shut down" | "let's shut down" →
1. Persist AIKB updates (`_index.md`, `_state.yaml`, project docs)
2. commit+push all repos
3. Report sync state

## IM — Self-Messaging
Triggers (fuzzy, case-insensitive): "leave yourself a note" · "note for next time" · "remember for next session" · "jot this down" · "make a note" · "don't forget this"
`python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py im send --from "Claude Code" --to "Claude Code" --severity info --summary "<subject>" --body "<detail>" --mirror-sent`
summary=one line · severity=review if needs attention next session · don't ack · reply: "Noted — I'll see that next session."

## Cross-Agent Awareness
See `docs/mind-meld.md`. Load when asked about other agents or avoiding duplicate work.

## Efficiency
`pgrep`/`ps`/`which` over `ls -R` · Full Deployment=production (DNS+Proxy+SSL) · POC=local only · Deep Trace=explicit permission

## Checkpoints
Commit at: phase done | major decision | before risky op | long conversation
Mark in-flight: `⚠️ IN PROGRESS — picked up by next session` · Done: `✅`

## Template Sync
`runtime_cli.py template-sync --auto-check` (weekly) · Never `./sync.sh` without approval · After sync: downstream repos may need `./sync-agents.sh`

## Token Economy
Compact (/compact) when any: sub-task done | tool output >50 lines | 3+ file reads | ~40 turns
Before compact: `python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py capture --agent "Claude Code" --session-id <id> --type decision --summary "<what>" [--rejected "<alt>"] [--assumptions "<ctx>"] [--invariants "<incomplete>"] [--next-step "<next>"]`
Only --summary required. Field guide: `docs/token-economy.md`
After compact: `aikb_search "<topic>"` to recall.
Bash output: always cap — `| head -50` · `2>&1 | tail -20` · `| grep -c`. Broad research: use Explore subagent.

## Wrap-up
1. `runtime_cli.py closeout --phrase "<phrase>"`
2. (if graph artifacts tracked) `build_temporal_graph.py` + `dream_cycle.py`
3. git add+commit+push all
4. Remove from `_agents/active.md`
