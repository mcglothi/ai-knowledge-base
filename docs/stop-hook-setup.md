# Stop Hook Setup
All three patterns converge on:
`bash {{LOCAL_PATH}}/_tools/memory-pipeline/aikb-session-stop.sh`
(captures closeout event · runs build_candidates.py · releases active claim · auto-commits _runtime/)

Prerequisites: `chmod +x {{LOCAL_PATH}}/_tools/memory-pipeline/aikb-session-stop.sh`
Replace `{{LOCAL_PATH}}` with your AIKB path (e.g. `~/code/AIKB`).

## Claude Code — `~/.claude/settings.json`
```json
{
  "hooks": {
    "Stop": [
      {"matcher": "", "hooks": [{"type": "command", "command": "bash {{LOCAL_PATH}}/_tools/memory-pipeline/aikb-session-stop.sh"}]}
    ]
  }
}
```
Merge `hooks` key if file already exists.

## Gemini CLI — `~/.gemini/settings.json`
Same JSON shape as Claude Code above. Merge `hooks` key if file exists.

## Codex CLI — no native hook
Add to `~/.zshrc` or `~/.bashrc`:
`source {{LOCAL_PATH}}/_tools/memory-pipeline/codex-wrapper.sh`
Defines `codex()` shell function that runs stop hook on exit. Restart shell after adding.

## Verify
`tail -20 {{LOCAL_PATH}}/_runtime/maintenance/session-stop.log`
Expected: `session stop begin` → `auto-committed runtime changes` → `session stop end`
Also check: new event in `_runtime/events/YYYY-MM-DD.ndjson` · row removed from `_agents/active.md`

## Manual fallback
```bash
bash {{LOCAL_PATH}}/_tools/memory-pipeline/aikb-session-stop.sh
```
Or individual steps:
```bash
python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py closeout --phrase "session ending"
python3 {{LOCAL_PATH}}/_tools/memory-pipeline/build_candidates.py
python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py release-session --agent "<Agent Name>"
git -C {{LOCAL_PATH}} add _runtime/ _agents/active.md && git -C {{LOCAL_PATH}} commit -m "AI Checkpoint: session end" && git -C {{LOCAL_PATH}} push origin main
```
