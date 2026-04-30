# Token Economy Playbook (v2)

## When to Load
- Heavy repo reads, large command output, long sessions, or nearing context limits.

## Compact Triggers (Claude parity)
- Subtask complete
- Tool output > 50 lines
- 3+ file reads in sequence
- ~40 turns / high context pressure

## Operating Pattern
1. Cap output aggressively (head/tail/filter).
2. Summarize before moving on.
3. Capture decisions before compaction.
4. Compact/compress at boundaries.

## Pre-Compact Capture (Claude pattern)
- `python3 ${AIKB_ROOT}/_tools/memory-pipeline/runtime_cli.py capture --agent "Claude Code" --session-id <id> --type decision --summary "<what>" [--rejected "<alt>"] [--assumptions "<ctx>"] [--invariants "<incomplete>"] [--next-step "<next>"]`
- `--summary` is required.

## Output Capping Defaults
- `| head -50`
- `2>&1 | tail -20`
- `| grep -c`

## Guardrails
- Keep exact commands/errors verbatim when relevant.
- Prefer precise excerpts over full dumps.
