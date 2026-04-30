# IM Playbook (v2)

## When to Load
- Any task involving inbox checks, replying to agents, self-notes, or cross-agent coordination.

## Fuzzy Trigger Phrases (must preserve)
- "leave yourself a note"
- "note for next time"
- "remember for next session"
- "jot this down"
- "make a note"
- "don't forget this"

## Core Flow
1. Peek new messages (include broadcast if relevant).
2. Summarize actionable items.
3. Reply or route as needed.
4. Ack/archive per workflow policy.

## Self-Note Convention
- Send with `--mirror-sent`.
- Do not ack self-note messages.
- Standard reply wording when appropriate:
  - `Noted — I'll see that next session.`

## Minimal Commands (pattern)
- `runtime_cli.py im peek --agent "<Agent>" --new --include-broadcast --mark-seen`
- `runtime_cli.py im send --from "<Agent>" --to "<Agent|Other>" --summary "..." --body "..." --mirror-sent`
