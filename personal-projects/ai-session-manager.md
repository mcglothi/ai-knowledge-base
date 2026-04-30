---
tags: [project, ai-tools, claude-code, gemini-cli, tui, token-optimization, context-window]
status: partial — interim pattern operational, TUI not started
last_updated: 2026-04-14
---

# Project: AI Session Manager TUI

**Last Updated:** 2026-04-14
**Status:** Partial — interim token economy pattern is operational; TUI not started
**Summary:** TUI wrapper for Claude Code + Gemini CLI that shows live context usage, triggers auto-compact at a threshold, and provides session management controls. The compaction and memory-buffer problems are now solved operationally; the TUI gap that remains is real-time visibility and automated triggering.

---

## What Is Now Operational (as of 2026-04-14)

The following pieces of the token economy strategy are live and instrumented:

| Component | Status | Location |
|---|---|---|
| Compact triggers (event-based) | ✅ In all agent instructions | `_agents/claude-code.md`, `codex.md`, `gemini.md` |
| AIKB-as-buffer pattern | ✅ Documented + in all agent instructions | `_agents/claude-code.md` |
| `local-compact.sh` Hopper→Gemini auto-fallback | ✅ Implemented | `~/code/scripts/local-compact.sh` |
| `remote-researcher.sh` Hopper→Gemini auto-fallback | ✅ Implemented | `~/code/scripts/remote-researcher.sh` |
| `gemini-log` wrapper + invocation metrics | ✅ Implemented | `~/code/scripts/gemini-log`, `_runtime/gemini-invocations.ndjson` |
| Hopper pipeline metrics (scoring, briefing, drafting) | ✅ Implemented | `_runtime/hopper-invocations.ndjson`, `_agents/hopper-offload-log.md` |
| Task routing matrix | ✅ In agent instructions | `_agents/claude-code.md` |

**Key insight shipped:** AIKB is the persistent memory buffer. Anything captured via `runtime_cli.py capture` survives compaction and is recallable with `aikb_search`. This makes aggressive compaction safe — agents no longer need heavyweight `session_state.md` writes before every compact.

---

## Active Interim Pattern — Offload Chain

The offload chain is now fully wired with automatic fallback:

```
Claude/Codex/Gemini session
    → sub-task completes or output >50 lines
    → capture to AIKB if new decision
    → /compact (in-session)
    → recall with aikb_search if needed

Heavy work:
    → local-compact.sh / remote-researcher.sh
        → Hopper (LAN) → Gemini fallback (off-LAN, auto)

Invocations logged to:
    _runtime/hopper-invocations.ndjson
    _runtime/gemini-invocations.ndjson
```

Protocol: `_agents/llm-context-offload.md`
Stats docs: `_agents/hopper-offload-log.md`, `_agents/gemini-context-offload-log.md`

---

## Remaining Gap — What the TUI Would Add

This covers the **pre-compaction**, **context recovery**, and **offload routing** problems. The TUI project (below) would address **real-time visibility** and **automated triggering** — complementary concerns, not overlapping.

---

## Why This Exists — Findings From Token Analysis

Analysis of local Claude Code JSONL session logs revealed how token costs actually accumulate:

| Finding | Detail |
|---------|--------|
| **Context resend multiplier** | 1,034-turn session had a 571× multiplier — 231K unique tokens became ~272M tokens sent to API |
| **Actual API cost for that session** | ~$815 at Sonnet input rates ($3/MTok) |
| **Tool results dominate** | 49–82% of stored tokens are tool results (bash output, file reads) |
| **CLAUDE.md overhead** | 2,348 tokens × 1,034 turns = 2.4M tokens just from system prompt repeating |
| **Single biggest lever** | Session length — a 100-turn session costs ~1/100th of a 1,000-turn session |

### Token Optimization Rules (apply every session)

1. **Start new sessions aggressively** — switch task = new session. Context from prior work stops helping well before turn 500.
2. **Run `/compact` mid-session** — built into Claude Code; compresses history, dramatically cuts resend cost
3. **Trim CLAUDE.md** — every token removed propagates across every API call forever
4. **Pipe verbose bash output** — `| head -50`, `2>&1 | tail -20` etc; large outputs stay in context the entire session
5. **Avoid re-reading large files** — once in context it's there; reading again doubles the cost for that content
6. **Use subagents (Task tool) for research** — isolates large content from the main context window

### Claude.ai Plan Analysis

| Plan | Monthly | Notes |
|------|---------|-------|
| Pro | $20 | Usage cap resets every ~5 hours; heavy Claude Code use hits cap 2×/day |
| Max (5×) | $100 | Should eliminate cap hits at current usage level |
| Max (20×) | $200 | Overkill unless usage grows significantly |
| API (Sonnet 4.6) | ~$135–270 est. | $3/MTok input, $15/MTok output; no caps but unpredictable; heavy sessions cost far more than subscription |

**Verdict:** Max $100 is the right upgrade from Pro at current usage patterns. API only makes sense for lighter, predictable usage.

---

## Existing Tools Landscape

Several tools already exist — know these before building anything:

### Use immediately
| Tool | What it does | Install |
|------|-------------|---------|
| [claude-monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor) | Real-time terminal monitor alongside Claude Code. Shows token progress bar, burn rate, ML-predicted limit time, cost. Reads local JSONL. | `uv tool install claude-monitor && claude-monitor --plan pro` |
| [ccusage](https://github.com/ryoppippi/ccusage) | Post-session analytics: daily/monthly breakdowns, cost totals, cache token tracking | `npx ccusage` |

### Worth evaluating
| Tool | What it does | Notes |
|------|-------------|-------|
| [context-lens](https://github.com/larsderidder/context-lens) | Transparent proxy (port 4040) that captures API calls; web UI shows context composition (system prompt %, tool results %, history %) with timeline and diffs | Works with Claude Code, Gemini, Aider, Codex. `npm i -g context-lens && context-lens claude` |
| [tokscale](https://github.com/junhoyeo/tokscale) | Multi-platform tracker: Claude Code, Gemini CLI, Cursor, Codex — global leaderboard, cost breakdown | Rust-based |
| [tokentap](https://github.com/jmuncor/tokentap) | Intercepts LLM API traffic, real-time terminal dashboard | Similar approach to context-lens |

### Adjacent (not primary targets)
- [opencode](https://github.com/opencode-ai/opencode) — alternative AI coding agent with built-in auto-compact; worth watching
- [aichat](https://github.com/sigoden/aichat) — multi-provider LLM CLI (not a wrapper for Claude Code/Gemini)

---

## The Gap — What Doesn't Exist Yet

All existing tools are **monitors alongside** the session, not **wrappers around** it. The missing piece:

> A TUI that runs Claude Code / Gemini CLI **inside** it, with an inline context bar, auto-compact trigger at a user-set %, and cross-tool session management — all without leaving the terminal.

### Specific gaps
- No tool triggers `/compact` automatically at a threshold
- No tool runs the AI **inside** a split pane (monitors sit in a separate window/pane)
- No unified session manager that works identically for Claude Code and Gemini CLI
- No inline session controls (new session, clear, compact) without switching windows

---

## Proposed Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  AI Session Manager TUI                                     │
│                                                             │
│  ┌────────────────────────────────┐  ┌──────────────────┐  │
│  │                                │  │ CONTEXT           │  │
│  │   Claude Code / Gemini CLI     │  │ ████████░░  78%  │  │
│  │   (running in pty pane)        │  │                  │  │
│  │                                │  │ Turns:     142   │  │
│  │   > what does lookup_pdfs.php  │  │ Input est: 89K   │  │
│  │     do?                        │  │ Burn rate: ↑ fast│  │
│  │                                │  │ Limit ETA: ~20m  │  │
│  │                                │  ├──────────────────┤  │
│  │                                │  │ AUTO-COMPACT: 80%│  │
│  │                                │  │ [toggle on/off]  │  │
│  └────────────────────────────────┘  ├──────────────────┤  │
│                                      │ [Compact now]    │  │
│  Tool: [Claude Code ▼]  [New Session]│ [New Session]    │  │
│                                      │ [Clear + Reset]  │  │
└─────────────────────────────────────────────────────────────┘
```

### Tech stack options

| Option | Pros | Cons |
|--------|------|------|
| **Python + Textual** | Excellent TUI library, good pty support, fast to prototype | Python startup overhead |
| **Go + Bubbletea** | Fast, single binary, great pty handling | More verbose code |
| **Rust + Ratatui** | Fastest, best terminal handling | Slowest to build |

Recommendation: **Python + Textual** for MVP — fastest path to working prototype.

### Token data sources per tool

| Tool | How to get token counts |
|------|------------------------|
| Claude Code | Watch `~/.claude/projects/<project>/<session>.jsonl` with inotify; parse new entries as they arrive |
| Gemini CLI | Proxy approach (like context-lens): set `GOOGLE_API_BASE_URL` to local proxy, intercept responses |
| Others (Aider, etc.) | Proxy approach |

### Auto-compact implementation

For Claude Code: when context % hits threshold, send `/compact` as a keystroke to the pty. Claude Code handles it natively.

For Gemini CLI: more complex — would need to inject a `/compress` or equivalent, or just alert the user.

### MVP scope (Phase 1)
- Claude Code only
- Context bar from JSONL watcher
- Auto-compact at configurable % (default 80%)
- New session shortcut
- Sidebar stats (turns, est. tokens, burn rate)

### Phase 2
- Gemini CLI support via proxy
- Cross-session history / cost totals
- Session naming and search

---

## Build Decision

**Not started.** First: install and use `claude-monitor` for several sessions to validate that a sidebar approach satisfies the need. If context bar in a separate pane is sufficient, the TUI wrapper may not be worth building. If the cross-tool unified experience is still the goal after that, proceed.

---

## References

- [Shipyard: How to track Claude Code usage](https://shipyard.build/blog/claude-code-track-usage/)
- [Gemini CLI persistent token display feature request](https://github.com/google-gemini/gemini-cli/issues/12788)
- [OpenCode auto-compact docs](https://thinkfleet.ai/en/docs/reference/session-management-compaction)
- [coding_agent_session_search](https://github.com/Dicklesworthstone/coding_agent_session_search) — unified TUI to search session history across 11+ providers; different use case but relevant
