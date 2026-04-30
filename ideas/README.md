# Ideas Inbox

**Last Updated:** 2026-04-23
**Summary:** Quick-capture landing zone for mobile or chat-based ideas that need follow-up later. Notes arrive here first, then get triaged into canonical project docs or closed out if they are noise.

## Purpose

This folder is the low-friction inbox for thoughts that show up away from the workstation.

Typical entry points:
- Signal
- Telegram
- Discord
- SMS or other chat bridges

## Flow

1. Capture the idea into `ideas/inbox/YYYY-MM-DD/`.
2. Keep the note self-contained: what it is, why it matters, and what follow-up is needed.
3. Triage it later into one of three paths:
   - promote into a project note or runbook
   - move into `ideas/follow-up/` if it needs more shaping
   - close it out if it is stale or not worth pursuing
4. Mark handled notes with:

```bash
python3 _tools/memory-pipeline/runtime_cli.py idea triage \
  --path ideas/inbox/2026-04-23/example.md \
  --status closed \
  --by "Codex CLI"
```

That keeps wake-up output focused on open ideas only.

## Capture Command

Use the operator-facing CLI directly:

```bash
python3 _tools/memory-pipeline/runtime_cli.py idea add \
  --source telegram \
  --sender "Tim" \
  --title "Expose quick note intake" \
  --text "Add a mobile note bridge so ideas land in AIKB before I forget them." \
  --tag mobile --tag chatops
```

The command writes a dated markdown note into the inbox and keeps the raw text readable for later review.
