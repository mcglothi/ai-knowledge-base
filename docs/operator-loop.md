# Operator Loop
**Last Updated:** 2026-04-21
No commands to remember — just talk to your agent.

## Quick Reference
AIKB is meant to work mostly through normal conversation. Once installed, the agent should do the tool-calling for you.

| What you want | What to say |
|---|---|
| Explicit session summary | "What was I working on last time?" |
| Current state snapshot | "What's the current state of things?" |
| Set session focus | "My focus today is X" |
| Flag for sign-off | "Ask me before you do X" |
| Wrap up | "Let's wrap up" |
| Capture a decision | "Remember that we switched to PostgreSQL — SQLite deadlocked" |

The two most useful phrases to remember are:
- **"Remember that..."** for durable memory
- **"Let's wrap up"** for an explicit closeout before ending, clearing, or switching sessions

## Daily Rhythm

**Starting:** Agents wake themselves up automatically — check pending items, incidents, SSL warnings, in-progress tasks. Or ask: "What was I working on?" / "Anything I should know?"

**Setting focus:** Name it early when the session might branch. Include what "done" looks like: "confirm tests are green", "open the live page and check layout."

**Approvals:** State constraints upfront:
> "Don't push to production without asking me first"
> "Flag it before you delete anything"

**Capturing decisions:** Say it out loud — the agent handles the rest. Include rejected alternatives and next steps for mid-implementation captures.

**Wrapping up:** "Let's wrap up" or "Let's shut down" → agent captures closeout, syncs AIKB, releases session claim. If you clear or end a session and want to be sure AIKB closes out cleanly first, say "Let's wrap up" before you do it.

## What Good Capture Looks Like

**Thin** (preserves decision, loses reasoning):
> "We switched to PostgreSQL."

**Rich** (future agent can resume):
> "Switched from SQLite to PostgreSQL for multi-user support. SQLite WAL mode deadlocked under concurrent agent writes — confirmed. Migration not done — don't write to users table. Next: migration 004, then update UserService.getRole() to read from DB."

## Command Reference (for the curious)
| You said | Tool invoked |
|---|---|
| "Give me a wake-up" | `runtime_cli.py wake-up` |
| "What's the current state?" | `runtime_cli.py hud` |
| "My focus is X" | `runtime_cli.py focus set` |
| "Remember that..." | `runtime_cli.py capture` |
| "Let's wrap up" | `runtime_cli.py closeout` |
| "What's pending approval?" | `approvals_cli.py list` |
