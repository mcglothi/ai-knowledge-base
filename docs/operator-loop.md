# Operator Loop

**Last Updated:** 2026-04-19
**Summary:** The daily loop that makes AIKB feel alive. No commands to remember — just talk to your agent.

---

## How it works

Your agent knows what to do. You just say what you need.

| What you want | What you say |
|---|---|
| Explicit session summary | "What was I working on last time?" *(optional — agent wakes itself up automatically)* |
| Current state snapshot | "What's the current state of things?" |
| Set a session focus | "My focus today is shipping the docs refresh" |
| Flag something for sign-off | "Ask me before you publish anything public" |
| Wrap up | "Let's wrap up" |
| Capture a decision | "Remember that we switched to PostgreSQL — SQLite had deadlock issues under concurrent load" |

The agent handles all of this internally. You don't need to remember tool names or commands.

---

## The Daily Rhythm

### Starting a session

You don't need to do anything — agents configured with AIKB wake themselves up automatically at the start of each session. They'll check pending items, open incidents, SSL warnings, and in-progress tasks before you say a word.

If you want a more explicit summary, just ask:

> "What was I working on last time?"

> "Anything I should know before we start?"

The agent will give you a structured snapshot on demand, but it's already oriented — you can also just dive straight into the work.

### Setting a focus

When a session is likely to branch, set a focus early:

> "My focus for this session is debugging the deploy failure"

> "I want to ship the onboarding docs today"

This keeps the agent oriented when you go down rabbit holes. Good verification steps tell the agent what "done" looks like: "confirm the tests are green", "open the live page and check the layout."

### Approvals

For decisions with architectural consequences, spending impact, or public-facing changes, tell your agent upfront:

> "Don't push anything to production without asking me first"

> "Flag it before you delete anything"

This creates a visible trust layer instead of those decisions disappearing into chat history.

### Capturing decisions mid-session

When something important is decided, just say it out loud:

> "Remember that we're using JWT, not session tokens — session tokens don't work across services"

> "Save a checkpoint — migration 004 still isn't written, next step is UserService.getRole()"

For mid-implementation captures, richer context helps. Include what was rejected, what's still incomplete, and what the next step is. The agent will ask if it needs clarification.

### Wrapping up

> "Let's wrap up" or "Let's shut down"

The agent captures a closeout event, syncs AIKB, and releases its session claim. The next session picks up from there.

---

## What good capture sounds like

The difference between a capture that helps and one that doesn't is context.

**Thin** — preserves the decision, loses the reasoning:

> "We switched to PostgreSQL."

**Rich** — a future agent can actually resume from this:

> "We switched from SQLite to PostgreSQL for multi-user support. SQLite WAL mode deadlocked under concurrent agent writes — tested and confirmed. Migration isn't done yet, don't write to the users table. Next step is migration 004, then update UserService.getRole() to read from DB."

When you're mid-implementation or the session is getting long, say what was rejected and what's still broken. A future agent reading that capture won't ask "why didn't you just use SQLite?" or "wait, is the migration done?"

---

## Repeated shorthand

When you notice you keep saying the same short thing — "wake the lab server", "restart staging" — tell your agent to log it:

> "Add 'restart staging' to my operator intents so you remember how to do it next time"

That's how AIKB turns operator habits into reusable workflows.

---

## Under the hood

If you're curious what the agent is actually running, here's the mapping:

| What you said | Tool invoked internally |
|---|---|
| "Give me a wake-up" | `runtime_cli.py wake-up` |
| "What's the current state?" | `runtime_cli.py hud` |
| "My focus is X" | `runtime_cli.py focus set` |
| "Remember that..." | `runtime_cli.py capture` |
| "Let's wrap up" | `runtime_cli.py closeout` |
| "What's pending approval?" | `approvals_cli.py list` |

You never need to run these directly.
