# Agent IM (Inbox + Archive)
**Last Updated:** 2026-04-21
File-based push channel for cross-agent coordination. Mind-meld pulls context; IM pushes it.
Storage: `_runtime/im/` · Schema: `_runtime/schemas/im-message.schema.json`

## Storage Layout
- `inbox/` — recipient inboxes (append-only NDJSON)
- `inbox/broadcast.ndjson` — shared broadcast all agents can peek
- `archive/` — per-agent time buckets (noise reduction)
- `sent/` — optional sender mirror
- `state/` — ack pointers

## CLI
```bash
# Send
runtime_cli.py im send --from "Codex CLI" --to "Claude Code" --severity review \
  --summary "Sanity-check the auth flow" --body "Focus on token refresh + expiry." --mirror-sent

# Broadcast
runtime_cli.py im send --from "Codex CLI" --to "broadcast" --severity info \
  --summary "FYI: refactoring X" --body "Reply in your inbox if you see a risk."

# Peek
runtime_cli.py im peek --agent "Claude Code" --limit 20
runtime_cli.py im peek --agent "Claude Code" --new --include-broadcast --mark-seen

# Ack + archive
runtime_cli.py im ack --agent "Claude Code" --all --include-broadcast
runtime_cli.py im archive --agent "Claude Code" --all-acked

# Retention
runtime_cli.py im gc --max-inbox 50 --max-age-days 14
```

## Auto-Check at Session Start
`wake-up --agent "<Name>"` peeks inbox and shows unread (including broadcast) in briefing. Messages marked seen but not acked — continue appearing until explicitly acked.
After reviewing: `runtime_cli.py im ack --agent "Claude Code" --all --include-broadcast`

## Self-Messaging
Operator says note-taking phrase → send IM to self. Surfaces at next wake-up.
```bash
runtime_cli.py im send --from "Claude Code" --to "Claude Code" --severity info \
  --summary "<one line>" --body "<full context>" --mirror-sent
```
Do NOT ack after sending — unacked = appears at next wake-up.

## Cross-Agent Phrases (fuzzy, case-insensitive)
"send a note to gemini: …" · "let claude know that …" · "message/ping codex about …"
Deterministic routing: `runtime_cli.py im route --dry-run --text "let claude know: CI is red"`
Send: `runtime_cli.py im route --send --text "let claude know: CI is red"`

## Promotion to Durable Memory
If archived IM contains durable signal → promote:
`runtime_cli.py capture --type decision|observation|blocker|change ...`
Or roll into candidates pipeline for review.
