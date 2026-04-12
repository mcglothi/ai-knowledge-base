# Stop Hook Setup — Automatic Session End

The Claude Code Stop hook runs `aikb-session-stop.sh` automatically when a session ends. This eliminates the need to manually capture closeout events, build candidates, or release your session claim.

## What it does

When your Claude Code session ends, the hook:
1. Captures a structured closeout event to `_runtime/events/YYYY-MM-DD.ndjson`
2. Runs `build_candidates.py` to process any events from this session
3. Releases your `active.md` session claim
4. Auto-commits uncommitted `_runtime/` changes to git

## Setup

**Step 1:** The hook script is already in your AIKB at `_tools/memory-pipeline/aikb-session-stop.sh`. Make it executable:

```bash
chmod +x {{LOCAL_PATH}}/_tools/memory-pipeline/aikb-session-stop.sh
```

**Step 2:** Add the hook to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash {{LOCAL_PATH}}/_tools/memory-pipeline/aikb-session-stop.sh"
          }
        ]
      }
    ]
  }
}
```

Replace `{{LOCAL_PATH}}` with your actual AIKB path (e.g. `~/code/AIKB`).

If `~/.claude/settings.json` doesn't exist, create it with just the hooks block above. If it already has other settings (like `statusLine`), merge the `hooks` key into the existing JSON.

**Step 3:** Verify the hook runs by ending a session. Check the log:

```bash
tail -20 {{LOCAL_PATH}}/_runtime/maintenance/session-stop.log
```

## What the hook logs

```
2026-04-12T19:00:00Z  --- session stop begin (host=tesla)
2026-04-12T19:00:01Z  auto-committed runtime changes
2026-04-12T19:00:02Z  --- session stop end
```

## Manual fallback

If the Stop hook is not configured, do these steps manually at session end:

```bash
# Capture a closeout event
python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py closeout \
  --agent "Claude Code" --phrase "session ending"

# Build candidates from today's events
python3 {{LOCAL_PATH}}/_tools/memory-pipeline/build_candidates.py

# Release your session claim
python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py release-session --agent "Claude Code"

# Commit runtime changes
git -C {{LOCAL_PATH}} add _runtime/ _agents/active.md && \
  git -C {{LOCAL_PATH}} commit -m "AI Checkpoint: session end" && \
  git -C {{LOCAL_PATH}} push origin main
```
