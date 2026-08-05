# Gemini CLI — Agent Instructions (rev 14, 2026-04-21)
Sync: `cp {{LOCAL_PATH}}/_agents/gemini-cli.md ~/.gemini/GEMINI.md`

## AIKB
Repo: `{{GITHUB_USERNAME}}/AIKB` · Local: `{{LOCAL_PATH}}/`
MCP mode (no local clone): server `github-aikb`, branch `main` · Read: `get_file_contents` · Write: `create_or_update_file` (include SHA)

## Session Start
wake-up optional — use only when cross-session continuity needed:
`python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py wake-up --agent "Gemini CLI"`
Claim: `runtime_cli.py claim-session --agent "Gemini CLI" --repo "AIKB" --scope "<scope>" --task "<task>"`

## Loading
Order: wake-up output → `_index.md`+`_state.yaml` if needed → specific files on demand.
Use `aikb_search` for freeform queries. Never bulk-load domain folders.
**Search before asking.** Before asking the operator for project background, prior decisions, machine details, or current state, first use `aikb_search` and relevant AIKB files. Ask only if the information is missing, stale, or ambiguous.

## Writing
Edit in place · Update `Last Updated` · Update `_index.md` on status change · Update `_state.yaml` on: incident, SSL cert, pending item
Commit: `git -C {{LOCAL_PATH}} add . && git -C {{LOCAL_PATH}} commit -m "AI Update: [file] — [what]" && git -C {{LOCAL_PATH}} push origin main`
In-flight: `⚠️ IN PROGRESS` · Done: `✅`

## Credentials
Secrets manager: {{SECRETS_MANAGER}}. Retrieve with `{{SECRETS_RETRIEVE}}`. Never echo secret values or pass them as CLI arguments.
MCP discovery: new tool/platform → check `_tools/mcp-registry.yaml` → if found, log to `_pending_approvals.md` (type: mcp-discovery, priority: low)

## Session End
Stop hook fires automatically (`~/.gemini/settings.json`). Setup: `docs/stop-hook-setup.md`.
Mid-session capture: `runtime_cli.py capture --agent "Gemini CLI" --session-id <id> --type decision --summary "<what>" [--rejected "<alt>"] [--assumptions "<ctx>"] [--invariants "<incomplete>"] [--next-step "<next>"]`

## IM — Self-Messaging
Triggers (fuzzy, case-insensitive): "leave yourself a note" · "note for next time" · "remember for next session" · "jot this down" · "make a note" · "don't forget this"
`python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py im send --from "Gemini CLI" --to "Gemini CLI" --severity info --summary "<subject>" --body "<detail>" --mirror-sent`
summary=one line · severity=review if needs attention next session · don't ack · reply: "Noted — I'll see that next session."

## Efficiency
`pgrep`/`ps`/`which` over `ls -R` · Full Deployment=production (DNS+Proxy+SSL) · POC=local only · Deep Trace=explicit permission

## Template Sync
`runtime_cli.py template-sync --auto-check` (weekly) · Never `./sync.sh` without approval · After sync: downstream repos may need `./sync-agents.sh`

## Token Economy
Compress (/compress) when any: sub-task done | tool output >50 lines | 3+ file reads | ~40 turns
Before compress: `runtime_cli.py capture --agent "Gemini CLI" --session-id <id> --type decision --summary "<what>" [--rejected "<alt>"] [--assumptions "<ctx>"] [--invariants "<incomplete>"] [--next-step "<next>"]`
Only --summary required. Field guide: `docs/token-economy.md`
After compress: `aikb_search "<topic>"` to recall.
Bash output: always cap — `| head -50` · `2>&1 | tail -20` · `| grep -c`.

## Wrap-up
"lets wrap up" | "let's wrap up" | "lets shut down" | "let's shut down" →
1. `runtime_cli.py closeout --phrase "<phrase>"`
2. (if graph artifacts tracked) `build_temporal_graph.py` + `dream_cycle.py`
3. git add+commit+push all
4. Remove from `_agents/active.md`
