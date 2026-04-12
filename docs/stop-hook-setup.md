# Stop Hook Setup — Automatic Session End

AIKB supports three session-end patterns today:

1. Claude Code Stop hook in `~/.claude/settings.json`
2. Gemini CLI Stop hook in `~/.gemini/settings.json`
3. Codex CLI wrapper or manual fallback, because Codex does not currently expose a native Stop hook

All three paths converge on:

```bash
bash {{LOCAL_PATH}}/_tools/memory-pipeline/aikb-session-stop.sh
```

That script captures a structured closeout event, runs `build_candidates.py`, releases your active claim, and auto-commits tracked `_runtime/` changes.

## Shared prerequisites

Make the stop script executable:

```bash
chmod +x {{LOCAL_PATH}}/_tools/memory-pipeline/aikb-session-stop.sh
```

Replace `{{LOCAL_PATH}}` with your actual AIKB path, for example `~/code/AIKB`.

## Claude Code

Add this to `~/.claude/settings.json`:

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

If `~/.claude/settings.json` already exists, merge the `hooks` key into the existing JSON.

## Gemini CLI

Gemini CLI supports the same Stop hook shape. Add this to `~/.gemini/settings.json`:

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

If `~/.gemini/settings.json` already exists, merge the `hooks` key into the existing JSON.

## Codex CLI

Codex CLI does not currently expose a native Stop hook, so AIKB ships a wrapper workaround at `_tools/memory-pipeline/codex-wrapper.sh`.

Add this line to your shell startup file such as `~/.zshrc` or `~/.bashrc`:

```bash
source {{LOCAL_PATH}}/_tools/memory-pipeline/codex-wrapper.sh
```

The wrapper defines a `codex()` shell function that runs the real Codex binary first, then launches `aikb-session-stop.sh` on exit. Open a new shell after adding it.

If you prefer not to shadow `codex`, use the manual fallback below instead.

## Verification

End a Claude, Gemini, or Codex session, then check:

```bash
tail -20 {{LOCAL_PATH}}/_runtime/maintenance/session-stop.log
```

Expected output looks like:

```text
2026-04-12T19:00:00Z  --- session stop begin (host=tesla)
2026-04-12T19:00:01Z  auto-committed runtime changes
2026-04-12T19:00:02Z  --- session stop end
```

You should also see:

- a new closeout event in `_runtime/events/YYYY-MM-DD.ndjson`
- your row removed from `_agents/active.md`
- a small checkpoint commit if tracked `_runtime/` files changed

## Manual fallback

If no Stop hook or wrapper is configured, run this at session end:

```bash
bash {{LOCAL_PATH}}/_tools/memory-pipeline/aikb-session-stop.sh
```

If you need to run the individual steps manually instead, use:

```bash
python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py closeout \
  --phrase "session ending"

python3 {{LOCAL_PATH}}/_tools/memory-pipeline/build_candidates.py

python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py release-session \
  --agent "<Claude Code|Gemini CLI|Codex CLI>"

git -C {{LOCAL_PATH}} add _runtime/ _agents/active.md && \
  git -C {{LOCAL_PATH}} commit -m "AI Checkpoint: session end" && \
  git -C {{LOCAL_PATH}} push origin main
```
