# Token Economy — Managing Context Cost Across AI Sessions

**Summary:** Practical strategies for keeping AI API costs under control when using AIKB across Claude Code, Codex, and Gemini CLI. The core insight: AIKB is your persistent memory buffer, which makes aggressive compaction safe rather than risky.

---

## The Multiplier Problem

AI APIs charge per token *sent*, not per token in your knowledge base. Every turn in a session resends the full conversation history. This creates an exponential cost curve:

| Session length | Approximate multiplier | Relative cost |
|---|---|---|
| 20 turns | ~10× | 1× |
| 50 turns | ~30× | 3× |
| 100 turns | ~75× | 7.5× |
| 500 turns | ~400× | 40× |
| 1,000 turns | ~570× | 57× |

A real 1,034-turn session measured 231K unique tokens ballooning to ~272M tokens sent — approximately $815 at current Sonnet input rates for a single session.

**Tool results dominate.** 49–82% of stored tokens are typically tool outputs: bash command dumps, file reads, search results. One untruncated 500-line file read stays in context for the rest of the session.

**System prompt overhead compounds.** A 2,000-token CLAUDE.md × 1,000 turns = 2M tokens just from the system prompt repeating.

---

## The Core Strategy: Compact Aggressively, Recall from AIKB

The reason agents hesitate to compact is fear of losing context. AIKB eliminates that fear:

> Anything captured to AIKB via `runtime_cli.py capture` survives compaction permanently and is recallable on demand with `aikb_search`.

This inverts the calculus: compact is cheap (takes seconds, trims context immediately), and anything important was already written to AIKB before the compact. After compacting, `aikb_search "what was decided about X"` recovers context faster than re-reading files.

---

## Compact Triggers

All three agents (Claude Code, Codex, Gemini CLI) use event-based triggers rather than trying to count turns:

**Run `/compact` (Claude/Codex) or `/compress` (Gemini) when ANY of these occur:**

1. **Sub-task completes** — a PR is created, a bug is fixed, a feature is written, a research phase finishes. This is the primary trigger: agents always know when they've finished a thing.
2. **Large tool output received** — any single bash command, file read, or search result exceeding ~50 lines. Compact before continuing so this output doesn't ride in context for the next 30 turns.
3. **Three or more consecutive file reads** — file contents accumulate fast; compact after a read-heavy investigation phase.
4. **~40 turns without a prior compact** — backstop for long continuous tasks where sub-tasks aren't clearly bounded.

---

## Sequence Before Every Compact

Always in this order — never compact before capturing:

```
1. New decision or finding not yet in AIKB?
   → python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py capture \
       --type decision --summary "what was decided and why"
   Already captured? → skip step 1.

2. Another agent needs to pick up mid-session? (Mind Meld / handoff)
   → write session_state.md in the project root
   Not a handoff situation? → skip step 2.

3. Run /compact (Claude/Codex) or /compress (Gemini)
```

`session_state.md` is a cross-agent handoff artifact, not a backup. If AIKB writes are disciplined, step 2 is rarely needed.

---

## After Compacting: Recall from AIKB

The compact removed working memory. AIKB preserved what matters:

```bash
# Recall a specific decision
aikb_search "what was decided about X"

# Load project context fresh
python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py wake-up
```

Prefer `aikb_search` over re-reading files — it's faster and doesn't bloat context with raw file contents.

---

## New Session vs Compact

| Situation | Action |
|---|---|
| Continuing the same task | `/compact` — keep the session, trim the history |
| Switching to a different task | New session — AIKB wake-up reconstitutes context cheaply |
| Coming back after hours | New session — stale context from prior work adds noise |
| Handing off to another agent | Write `session_state.md`, then new session |

Starting a new session is cheap when AIKB is populated. The wake-up command loads the current state snapshot, recent events, and pending items in seconds.

---

## Bash Output Discipline

Untruncated tool output is the single biggest context bloat driver. Cap everything:

```bash
command | head -50          # file listings, logs, build output
command 2>&1 | tail -20     # error streams
command | grep -c pattern   # get a count, not a full match list
git log --oneline -20       # not git log (full format)
ls                          # not ls -la -R
```

If you genuinely need to inspect a large output, pipe it to a temp file and read selectively:

```bash
command > /tmp/output.txt
wc -l /tmp/output.txt       # check size first
head -30 /tmp/output.txt    # read the part you need
```

---

## Context Offload: Routing Heavy Work Away from Frontier Models

Not all tasks need your most capable (and most expensive) model. Route by task type:

| Task | Best model tier |
|---|---|
| Compaction / summarization | Local model (fast, cheap, good enough) |
| File research: 10–50 files | Local model via `remote-researcher.sh` |
| File research: 50+ files or >128K context | Cloud fallback (large context window) |
| Code generation from clear spec | Mid-tier (Codex) |
| Complex reasoning / synthesis / review | Frontier (Claude) |

The offload chain in this AIKB repo (`local-compact.sh`, `remote-researcher.sh`) automatically falls back to a cloud model when the local model is unavailable, so the routing is transparent.

---

## Monitoring Tools

These tools run alongside your AI sessions and give you visibility into context usage:

| Tool | What it does | Install |
|---|---|---|
| [claude-monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) | Live token progress bar, burn rate, predicted limit time | `uv tool install claude-monitor` |
| [ccusage](https://github.com/ryoppippi/ccusage) | Post-session analytics: daily/monthly cost breakdowns, cache hit rates | `npx ccusage` |
| [context-lens](https://github.com/larsderidder/context-lens) | Transparent proxy that shows context composition (system prompt %, tool results %, history %) | `npm i -g context-lens` |

`claude-monitor` is the highest-value first install — it gives you the signal to compact before you hit the wall rather than after.

---

## Summary Rules

1. **Capture fast** — one `runtime_cli.py capture` line per decision, then it's safe to compact
2. **Compact at sub-task boundaries** — not at arbitrary turn counts
3. **Cap bash output** — every untruncated dump rides in context for the rest of the session
4. **New session freely** — AIKB wake-up makes cold starts cheap
5. **Route heavy work** — local models for compaction and bulk research, frontier models for reasoning
