# OpenCode — Agent Instructions (rev 2, 2026-04-21)
Config: `~/.config/opencode/opencode.json` → `instructions` array (file loaded directly, no copy needed)

## AIKB
Repo: `{{GITHUB_USERNAME}}/AIKB` · Local: `{{LOCAL_PATH}}/`
MCP mode (no local clone): server `github-aikb`, branch `main` · Read: `get_file_contents` · Write: `create_or_update_file` (include SHA)

## Session Start
wake-up optional — use only when cross-session continuity needed:
`python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py wake-up --agent "OpenCode"`
Claim: `runtime_cli.py claim-session --agent "OpenCode" --repo "AIKB" --scope "<scope>" --task "<task>"`

## Loading
Order: wake-up output → `_index.md`+`_state.yaml` if needed → specific files on demand.
Use `aikb_search` for freeform queries. Never bulk-load domain folders.
**Search before asking.** Before asking the operator for project background, prior decisions, machine details, or current state, first use `aikb_search` and relevant AIKB files. Ask only if the information is missing, stale, or ambiguous.

## Writing
Edit in place · Update `Last Updated` · Update `_index.md` on status change · Update `_state.yaml` on: incident, SSL cert, pending item
Commit: `git -C {{LOCAL_PATH}} add . && git -C {{LOCAL_PATH}} commit -m "AI Update: [file] — [what]" && git -C {{LOCAL_PATH}} push origin main`
In-flight: `⚠️ IN PROGRESS` · Done: `✅`

## Git — Project Repos
main: typos, minor docs · Branch: features, assets, anything hard to reverse
`git checkout -b opencode/<desc>` → `git push -u origin HEAD` → `gh pr create --fill`
Binary assets: always new filename (GitHub CDN caches by URL). AIKB: push `_runtime/` + canonical docs direct to main.

## Credentials
Secrets manager. Reference: `[Stored in Vaultwarden: <Item Name>]`

## Session End
No native stop hook. Options:
1. Preferred: add to `~/.zshrc`: `source {{LOCAL_PATH}}/_tools/memory-pipeline/opencode-wrapper.sh`
2. Fallback: `bash {{LOCAL_PATH}}/_tools/memory-pipeline/aikb-session-stop.sh` before finishing
Setup: `docs/stop-hook-setup.md` · install.sh does not add wrapper automatically.
Mid-session capture: `runtime_cli.py capture --agent "OpenCode" --session-id <id> --type decision --summary "<what>" [--rejected "<alt>"] [--assumptions "<ctx>"] [--invariants "<incomplete>"] [--next-step "<next>"]`

## Shutdown
"lets wrap up" | "let's wrap up" | "lets shut down" | "let's shut down" →
1. Persist AIKB updates (`_index.md`, `_state.yaml`, project docs)
2. commit+push all repos
3. `bash {{LOCAL_PATH}}/_tools/memory-pipeline/aikb-session-stop.sh` (unless wrapper installed)
4. Report sync state

## IM — Self-Messaging
Triggers (fuzzy, case-insensitive): "leave yourself a note" · "note for next time" · "remember for next session" · "jot this down" · "make a note" · "don't forget this"
`python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py im send --from "OpenCode" --to "OpenCode" --severity info --summary "<subject>" --body "<detail>" --mirror-sent`
summary=one line · severity=review if needs attention next session · don't ack · reply: "Noted — I'll see that next session."

## Cross-Agent Awareness
See `docs/mind-meld.md`. Load when asked about other agents or avoiding duplicate work.

## Efficiency
`pgrep`/`ps`/`which` over `ls -R` · Full Deployment=production (DNS+Proxy+SSL) · POC=local only · Deep Trace=explicit permission

## Token Economy
Compact (/compact) when any: sub-task done | tool output >50 lines | 3+ file reads | ~40 turns
Before compact: `runtime_cli.py capture --agent "OpenCode" --session-id <id> --type decision --summary "<what>" [--rejected "<alt>"] [--assumptions "<ctx>"] [--invariants "<incomplete>"] [--next-step "<next>"]`
Only --summary required. Field guide: `docs/token-economy.md`
After compact: `aikb_search "<topic>"` to recall.
Bash output: always cap — `| head -50` · `2>&1 | tail -20` · `| grep -c`.
