# Token Economy
Every turn resends full context. Cost scales ~quadratically with session length (measured: 1,034-turn session = ~272M tokens sent). System prompt overhead compounds — a 2,000-token CLAUDE.md × 1,000 turns = 2M tokens from the prompt alone. Tool results dominate: 49–82% of stored tokens are bash dumps and file reads.

## Compact Triggers
Run `/compact` (Claude/Codex) or `/compress` (Gemini) when any:
1. Sub-task done — PR created, bug fixed, feature written, research phase complete
2. Tool output >50 lines — compact before continuing
3. 3+ consecutive file reads
4. ~40 turns without a prior compact

## Before Every Compact
```bash
python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py capture \
  --agent "<Agent>" --session-id <id> --type decision \
  --summary "<what was decided>" \
  [--rejected "<alternatives ruled out + why>"] \
  [--assumptions "<currently true, not obvious from code>"] \
  [--invariants "<intentionally incomplete until X>"] \
  [--next-step "<exact resumption point>"]
```
Only `--summary` required. Skip capture if already done — don't duplicate.
Write `session_state.md` only if another agent needs to pick up mid-session.

## After Compact
`aikb_search "<topic>"` to recall. Faster than re-reading files.

## Bash Output Discipline
Untruncated output is the biggest context bloat driver. Always cap:
```bash
command | head -50
command 2>&1 | tail -20
command | grep -c pattern
git log --oneline -20
```
Large output → write to `/tmp/output.txt`, then `wc -l` before reading.

## Session Strategy
| Situation | Action |
|---|---|
| Continuing same task | `/compact` — trim history, keep session |
| Switching task | New session — AIKB wake-up reconstitutes context |
| Back after hours | New session — stale context adds noise |
| Handing off | Write `session_state.md`, then new session |

## Model Routing
| Task | Tier |
|---|---|
| Compaction / summarization | Local model |
| File research 10–50 files | Local via `remote-researcher.sh` |
| File research 50+ or >128K ctx | Cloud fallback |
| Code gen from clear spec | Mid-tier (Codex) |
| Complex reasoning / synthesis | Frontier (Claude) |

## Monitoring
- `uv tool install claude-monitor` — live token progress bar, burn rate, predicted limit time
- `npx ccusage` — post-session cost analytics, cache hit rates
- `npm i -g context-lens` — shows context composition (system prompt % / tool results % / history %)
