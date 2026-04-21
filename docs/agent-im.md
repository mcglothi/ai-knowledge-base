# Agent IM (Inbox + Archive)

**Last Updated:** 2026-04-21
**Summary:** File-based "instant messaging" for cross-agent coordination: send notes, request review, and reduce noise via archive. Auto-checked at session start via wake-up. Messages are advisory context only.

---

## Why

Mind-meld is great for *pulling* context (peek what others are doing). IM adds a *push* channel (tell another agent what you saw, request help, coordinate direction).

## Architecture (v1)

Storage lives in `_runtime/im/`:

- `inbox/` — recipient inboxes (append-only NDJSON)
- `inbox/broadcast.ndjson` — shared broadcast inbox (optional; agents can include it when peeking)
- `archive/` — per-agent time buckets (reduce inbox noise)
- `sent/` — optional sender mirror
- `state/` — ack pointers (what was "read")

Message schema: `_runtime/schemas/im-message.schema.json`

## CLI

```bash
# Send
python3 _tools/memory-pipeline/runtime_cli.py im send \
  --from "Codex CLI" --to "Claude Code" \
  --severity review \
  --summary "Please sanity-check the auth flow" \
  --body "Focus on token refresh + expiry edge cases." \
  --mirror-sent

# Broadcast (shared inbox all agents can peek)
python3 _tools/memory-pipeline/runtime_cli.py im send \
  --from "Codex CLI" --to "broadcast" \
  --severity info \
  --summary "FYI: planning to refactor X" \
  --body "Reply in your own inbox if you see a risk."

# Peek
python3 _tools/memory-pipeline/runtime_cli.py im peek --agent "Claude Code" --limit 20
python3 _tools/memory-pipeline/runtime_cli.py im peek --agent "Claude Code" --new --include-broadcast --mark-seen

# Ack + archive (email-style)
python3 _tools/memory-pipeline/runtime_cli.py im ack --agent "Claude Code" --all --include-broadcast
python3 _tools/memory-pipeline/runtime_cli.py im archive --agent "Claude Code" --all-acked

# Retention (archive old + cap inbox)
python3 _tools/memory-pipeline/runtime_cli.py im gc --max-inbox 50 --max-age-days 14
```

## Auto-Check at Session Start

Pass `--agent "<Agent Name>"` to `wake-up` and it will automatically peek your inbox and show unread messages (including broadcast) in the briefing output. Messages are marked as *seen* but remain unacked so they continue to appear until explicitly acked.

```bash
python3 _tools/memory-pipeline/runtime_cli.py wake-up --agent "Claude Code"
python3 _tools/memory-pipeline/runtime_cli.py wake-up --agent "Codex CLI"
```

After reviewing, ack to clear from the wake-up display:
```bash
python3 _tools/memory-pipeline/runtime_cli.py im ack --agent "Claude Code" --all --include-broadcast
```

## Self-Messaging (Leave Yourself a Note)

When the operator says "leave yourself a note", "note this for next time", "jot that down", or similar phrases, agents should send an IM to themselves. The message will surface automatically at the next wake-up.

```bash
python3 _tools/memory-pipeline/runtime_cli.py im send \
  --from "Claude Code" --to "Claude Code" \
  --severity info \
  --summary "<what to remember, one line>" \
  --body "<full context>" \
  --mirror-sent
```

Do NOT ack the message after sending — leaving it unacked is what makes it appear at the next wake-up.

## Operator Phrases (model-side triggers)

These are *natural-language intents* you can say to an agent. The agent should interpret fuzzily (case-insensitive) and act:

- “send a note to gemini: …”
- “let claude know that …”
- “message/ping codex about …”
- “check what gemini is working on and if you see issues let them know”

`runtime_cli.py im interpret` can help standardize parsing when you want a deterministic hint payload.

If you want a CLI-enforced safety latch before sending based on fuzzy text, use:

```bash
python3 _tools/memory-pipeline/runtime_cli.py im route --dry-run --text "let claude know: CI is red"
python3 _tools/memory-pipeline/runtime_cli.py im route --send --text "let claude know: CI is red"
```

## Promotion to Durable Memory

If an archived IM contains durable signal (decision, invariant, procedure, or a reusable gotcha), promote it:

- Capture as an event: `runtime_cli.py capture --type decision|observation|blocker|change ...`
- Or roll it into the candidates pipeline for review.

