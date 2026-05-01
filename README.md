

<p align="center">
  <img src="_branding/hero-graphic.png" alt="AIKB" width="1000" />
</p>

<h1 align="center">AIKB — AI Knowledge Base</h1>

<p align="center">
  <img src="_branding/demo-installer-v3.gif" alt="AIKB installer" width="800" />
</p>



<p align="center">
  Shared context across sessions, tools, and machines.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License" />
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome" />
  <img src="https://img.shields.io/badge/Maintenance-Active-green.svg" alt="Maintenance" />
  <img src="https://img.shields.io/badge/Status-Public--Template-indigo.svg" alt="Status" />
</p>

---

### Shared, persistent, inspectable memory for your AI tools.

AIKB gives your agents shared context that survives across sessions, tools, and machines. It stays local-first, Git-backed, and fully inspectable, so your memory system feels like infrastructure you control instead of a black box you hope is right.

> Your AI tools should not start from zero.

AIKB is designed as a **cross-agent, cross-machine memory layer** — owned by the operator, not the platform.

[**Get Started**](#quick-start) • [**How It Works**](#how-it-works) • [**Tool Support**](#ai-tool-compatibility)

---

## What AIKB Is

AIKB is shared memory for your AI tools. It helps Claude Code, Gemini CLI, Codex, OpenCode, Cursor, and similar agent-style tools keep context across sessions and machines without making you repeat yourself every time.

The memory lives in plain markdown files in a Git-backed repo you control, so it is easy to inspect, search, and fix when something goes wrong. One of AIKB's biggest advantages is that memory is editable with ordinary tools. If the agent learns something wrong, you don't need a proprietary console — just open the repo, find the bad memory, and correct it.

## Why People Use It

Every AI session tends to start from zero. You re-explain your projects, your stack, your preferences, and your constraints every time. Context windows are finite, sessions end, and useful working memory disappears with them.

If you use multiple tools, the problem gets worse. Different agents end up relearning the same context from scratch unless you give them a shared memory layer.

## The Basic Model

Once AIKB is installed, the goal is for it to feel mostly automatic:
- the agent picks up on cues
- the agent searches AIKB before asking you to restate context
- the agent remembers useful things in the background
- the stop hooks handle closeout when configured

In practice, the two phrases worth remembering are:
- **"remember that..."** when something should stick
- **"Let's wrap up"** before ending or clearing a session when you want to be sure closeout runs

```text
Session starts → Agent reads AIKB → Agent knows what matters
Do work        → Agent captures decisions and useful context
Session ends   → AIKB preserves continuity for next time
```

---

## Key Features

- **Shared memory across tools** — one memory layer for Claude Code, Gemini CLI, Codex, OpenCode, Cursor, Copilot, and other agentic tools
- **Stored in files you control** — AIKB is local-first and Git-backed, so memory is easy to inspect, diff, sync, and correct when something goes wrong
- **Search before asking** — agents are expected to check AIKB for prior context before asking you to repeat project background, decisions, or machine details
- **Wake-up on demand** — say **"wake up"** or **"what was I working on?"** and the agent can pull recent context, current state, and unread notes so it gets oriented quickly
- **Remember important things naturally** — say **"remember that..."** and the agent can capture a durable decision, fact, blocker, or next step for later
- **Wrap up cleanly** — say **"let's wrap up"** before ending or clearing a session and the agent can run closeout so the next session starts informed
- **Cross-agent notes** — say things like **"send Claude a note..."** or **"leave Gemini a message..."** and agents can hand off context cleanly across tools and sessions
- **Shared awareness across agents** — say **"take a look at what Gemini is working on"** or **"check what Claude was doing"** and agents can review recent activity before repeating work or asking you to restate context
- **Keeps memory from getting stale** — AIKB can surface stale docs, forgotten pending items, and cleanup opportunities so the memory base stays useful over time
- **Structured memory, not random notes** — useful working context can be captured during sessions and the durable parts can be promoted into organized long-term memory instead of becoming one giant chat log
- **Mostly automatic once installed** — agents can pick up on cues, remember useful things, search AIKB before asking you to repeat yourself, and handle bookkeeping in the background
- **Editable with normal tools** — one of AIKB's biggest advantages is that memory is editable with ordinary tools. If the agent learns something wrong, you don't need a proprietary console — just open the repo, find the bad memory, and correct it
- **Token-efficient by design** — AIKB helps move important context out of the live chat so compaction is less lossy and more of the context window is available for actual work
- **Secrets-safe** — credentials stay in your secrets manager; AIKB stores references only
- **Machine-aware** — each machine gets a profile so the agent uses the right paths, tools, and conventions

## Product Snapshot

| What it gives you | Why it matters |
|-------------------|----------------|
| Persistent session memory | Stop repeating the same setup and project context |
| Inspectable storage | Trust the memory because it lives in Markdown + Git |
| Cross-tool continuity | Switch tools without losing your working context |
| Structured updates | Capture decisions, gotchas, blockers, and state changes cleanly |
| Cross-agent coordination | Keep multiple agents aligned through shared memory, IM, and mind-meld patterns |
| Optional dream consolidation | Turn noisy daily memory into bundled, reviewable nightly summaries |

## Feature Status

Current capabilities in the public template. Most of these should feel automatic in day-to-day use: you talk to the agent, and the agent calls the right AIKB tools behind the scenes.

If you only remember one thing, remember to say **"Let's wrap up"** before ending or clearing a session. That gives AIKB a clean chance to preserve end-state and continuity for the next session.

| Feature | Status | How it shows up in practice |
|---------|--------|----------------------------|
| Session start briefing + IM inbox check | ✅ Built | Ask the agent to **wake up**, or just begin a normal session and let it orient itself |
| Manual memory capture | ✅ Built | Say **"remember that..."** when you make a durable decision or learn something important |
| In-session memory writes (MCP) | ✅ Built | The agent can save durable memories during work without you editing files directly |
| Session HUD | ✅ Built | Ask **"what's the current state?"** or **"what was I working on?"** |
| Candidate pipeline | ✅ Built | AIKB stages raw runtime signal and turns it into reviewable memory updates behind the scenes |
| Interactive candidate review | ✅ Built | Power-user or maintainer workflow for reviewing queued memory updates |
| Session closeout capture | ✅ Built | Say **"Let's wrap up"** before you end or clear a session |
| Claude Code Stop hook | ✅ Built | Closeout can happen automatically at the end of a Claude Code session once configured |
| Gemini CLI Stop hook | ✅ Built | Closeout can happen automatically at the end of a Gemini CLI session once configured |
| Codex closeout workaround | ✅ Built | Use the wrapper or say **"Let's wrap up"** before the session is cleared |
| Keyword search | ✅ Built | The agent can look up prior context instead of asking you to restate it |
| Semantic / hybrid search | ✅ Built | The agent can retrieve relevant context even when the wording changes |
| MCP search tool | ✅ Built | AIKB can answer questions like **"what did we decide about auth?"** from memory |
| Retention policy enforcement | ✅ Built | Helps maintainers keep stale or low-value memory from piling up over time |
| Operator intents / runbooks | ✅ Built | You can teach shorthand workflows once, then reuse them naturally in conversation |
| Template sync / self-update | ✅ Built | Existing AIKB instances can pull framework improvements without overwriting personal content |
| Nightly maintenance | ✅ Built | Optional background cleanup and housekeeping for mature AIKB instances |
| Mind Meld (cross-agent awareness) | ✅ Built | Agents can see what neighboring agents are doing and avoid duplicate work |
| Agent IM (cross-agent + self-messaging) | ✅ Built | Agents can leave notes for each other — or for their future selves — across sessions |
| Dream cycle consolidation | ✅ Built (Optional Extension) | Optional background summarization and consolidation layer for power users |

---

## What The Operator Loop Looks Like

The core AIKB workflow is simple:

```text
Start session -> agent runs wake-up, reads recent state
Do work        -> capture decisions, blockers, and approvals as needed
Wrap up        -> Stop hook, wrapper, or manual closeout records the end state
Next session   -> wake-up synthesizes what changed, agent starts informed
```

**You don't run any of this yourself.** Once AIKB is installed, the agent handles the mechanics in the background. There are no commands to memorize and no files you normally need to touch. You just talk to your agent:

| What you want | What you say |
|---|---|
| Session context | Agent orients itself automatically at start — nothing required |
| Explicit summary | "What was I working on last time?" |
| Set a focus | "My focus today is shipping the dashboard cleanup" |
| Flag for sign-off | "Ask me before you push anything public" |
| Capture a decision | "Remember that we switched to Postgres — SQLite deadlocked under concurrent writes" |
| Leave a note for your next session | "Leave yourself a note: resume from the auth middleware refactor" |
| Wrap up | "Let's wrap up" |

The agent calls the right tools internally. You never need to remember a command name. See [`docs/operator-loop.md`](docs/operator-loop.md) for the full daily rhythm and examples.

Claude Code and Gemini CLI can both call the Stop hook from their settings JSON files. Codex does not expose a native Stop hook today, so AIKB includes a small wrapper script plus a manual fallback. All three routes converge on `aikb-session-stop.sh`, which captures a closeout event, runs the candidate pipeline, releases the active claim, and commits tracked `_runtime/` changes.

During a session, agents can write durable memories directly via the `aikb_remember` MCP tool, without touching files:

```
aikb_remember(
  summary="Decided to use Postgres instead of SQLite for scale",
  project="projects/my-api.md",
  type="decision"
)
# → writes to _runtime/events/, queued for review pipeline
```

By default, raw runtime event files are local working memory. Promote durable signal into candidates, approvals, summaries, or canonical docs instead of auto-committing every event log.

---

## Under the Hood

AIKB does use CLI tools under the hood, but once installed you should mostly interact with it through normal conversation. The tools below are for power users, maintainers, and people who want to understand the plumbing:

- **Session Briefing** (`runtime_cli.py wake-up`) — Synthesizes a compact session-start briefing from recent events and current state. Agents orient in seconds instead of reading through full docs.
- **Interactive Candidate Review** (`aikb_review.py`) — Presents queued memory candidates one-by-one with `[a]pprove / [r]eject / [s]kip / [?]events` prompts. Shows source events on demand, tracks progress, offers to run `propose_patches.py` at the end.
- **Retention Enforcer** (`retention_check.py`) — Scans for stale docs (>90 days), forgotten `_state.yaml` pending items without priority, complete/decommissioned index entries linked to old docs, and fully-terminal candidate bundles ready for deletion. Run with `--delete-terminal-candidates` to clean up automatically.
- **Hybrid Search** (`memory_search.py`) — Keyword, semantic (requires `sentence-transformers`), or hybrid mode. Run `memory_search.py --rebuild-index` to build the vector index after install.
- **MCP Search + Memory** (`_tools/aikb-search/server.py`) — Registers `aikb_search` and `aikb_remember` as MCP tools. Implements advanced retrieval with **Graph-RAG**, intent-aware priors, temporal filters, and linear recency decay.
- **Ambient Context Injection** (`ambient_ask.sh`) — A wrapper for your AI CLI that automatically injects relevant facts from your AIKB into your prompt *before* the agent starts.
- **Temporal Knowledge Graph** (`build_temporal_graph.py`) — Generates a structured JSON graph of your knowledge, extracting entities like IPs and tools to track how they change over time.

---

## AI Tool Compatibility

AIKB is primarily built for agentic tools that can load instructions, read files, search memory, and participate in session lifecycle workflows.

### Primary AIKB lane

| Tool | Integration | AIKB Access Mode |
|------|-------------|-----------------|
| Claude Code | `~/.claude/CLAUDE.md` auto-loaded | Local clone or GitHub MCP |
| Gemini CLI | `~/.gemini/GEMINI.md` auto-loaded | Local clone or GitHub MCP |
| Codex CLI | `AGENTS.md` in project root | Local clone (or MCP if configured) |
| GitHub Copilot | `.github/copilot-instructions.md` in project root | Local workspace context |
| OpenCode | `instructions` array in `~/.config/opencode/opencode.json` | Local clone or GitHub MCP |
| Cursor | User Rules (Settings UI) | Local clone |

### Future-agent lane

If you are wiring up a new agent in the future — such as Goose, Hermes, OpenClaw, or another model-specific tool — the docs in this repo are meant to be sufficient for the agent to configure itself appropriately.

The key expectations are:
- load the AIKB instruction file or equivalent system guidance
- use AIKB search before asking the operator to restate context
- participate in wake-up / memory capture / closeout workflows
- treat AIKB as the durable source of shared context across sessions and machines

---

## Quick Start

### Step 1: Create your private repo

**GitHub CLI (fastest):**
```bash
gh repo create AIKB --template mcglothi/ai-knowledge-base --private --clone
cd AIKB
```

**Or manually:** click **Use this template** → name it `AIKB` → set Private → clone it.

### Step 2: Run the installer

```bash
chmod +x install.sh
./install.sh
```

The installer will ask a few questions (most are pre-filled) and configure whichever
AI tools you use. Takes about 3 minutes.

**Windows users:** see [docs/windows-wsl.md](docs/windows-wsl.md) first.

### Step 3: Push, then just chat

```bash
git push origin main
```

Open Claude Code (or your preferred agent) and say:

> "I just set up AIKB — let's fill in my profile."

From there, AIKB is meant to feel natural:
- agents pick up on phrases like "remember that..."
- agents search AIKB before asking you to repeat context they should already know
- stop hooks and closeout automation run behind the scenes once configured
- "Let's wrap up" is the one phrase worth remembering when you want to be sure a session closes out cleanly before ending, clearing, or switching contexts

The agent will ask about your background, skills, stack, and machine — and write `personal/profile.md` and `personal/dev-environment/[hostname].md` directly from the conversation. No manual editing required.

Once done, agents should stop asking "what's your stack?" or "what machine are you on?" unless something is missing, stale, or ambiguous.

---

## What AIKB Is Not

AIKB is not:
- a hosted SaaS memory platform
- a black-box memory API
- a full autonomous agent runtime
- a homelab operating environment
- a benchmark lab as part of the core product story

### Go deeper

| Goal | Where to look |
|------|--------------|
| Full setup walkthrough | [docs/getting-started.md](docs/getting-started.md) |
| Understand the product boundary | [docs/product-boundaries.md](docs/product-boundaries.md) |
| Understand extensions vs core | [docs/extension-model.md](docs/extension-model.md) |
| Add MCP search + in-session memory | [docs/mcp-setup.md](docs/mcp-setup.md) |
| Set up session-end automation | [docs/stop-hook-setup.md](docs/stop-hook-setup.md) |
| Configure the runtime memory workflow | [docs/search-setup.md](docs/search-setup.md) |
| Learn the operator loop | [docs/operator-loop.md](docs/operator-loop.md) |
| Windows / WSL setup | [docs/windows-wsl.md](docs/windows-wsl.md) |

## Staying Up to Date

When improvements are made to the template (better agent instructions, new tool support, updated schemas), you can pull them without touching your personal content.

`install.sh` automatically adds this repo as an `upstream` git remote and saves your personal config to a git-ignored `.aikb-config.d/` directory. When you want updates, run:

```bash
python3 _tools/memory-pipeline/runtime_cli.py template-sync --auto-check
python3 _tools/memory-pipeline/runtime_cli.py template-sync --set-interval 7
./sync.sh
```

`sync.sh` will:
1. Fetch the latest changes from upstream
2. Use `.aikb-config.d/template-sync-state.json` to remember when you last checked and which upstream SHA you last applied
3. In `--check` mode, show whether framework updates are waiting without touching tracked files
4. In normal mode, show you exactly what changed in the framework dirs (`AGENTS.md`, `.github/copilot-instructions.md`, `_agents/`, `_templates/`, `_tools/`, `docs/`, and selected root framework files)
5. Ask for confirmation before applying anything
6. Re-apply your personal values (username, repo name, paths, secrets manager) automatically
7. Re-copy to `~/.claude/CLAUDE.md` or `~/.gemini/GEMINI.md` if you set those up during install
8. Commit the result

**What gets updated:** `AGENTS.md`, `.github/copilot-instructions.md`, `_agents/`, `_templates/`, `_tools/`, `docs/`, `_pending_approvals.md`, `sync.sh`, `sync-agents.sh`, `install.sh`, `.gitignore`

**What is never touched:** `_index.md`, `_state.yaml`, `personal/`, `projects/`, `work/`, and any other dirs you've created

Suggested habit:
- Let agents run `python3 _tools/memory-pipeline/runtime_cli.py template-sync --auto-check` during session setup or when you explicitly ask about updates.
- Keep the default cadence at `7` days unless the public template is changing quickly; use `--set-interval 3` for active rollout periods or `--set-interval 14` for a quieter cadence.
- Keep actual `./sync.sh` application operator-approved, since it changes tracked framework files.
- After a framework sync, re-sync downstream project agent files with `./sync-agents.sh --all /path/to/project`.

---

## How It Works

### Repository structure

```text
AIKB/
├── README.md                  ← Human-readable overview (you're reading it)
├── .github/copilot-instructions.md ← Repo instructions for GitHub Copilot
├── _index.md                  ← One-line status for every project (agents read this first)
├── _state.yaml                ← Time-sensitive surface: SSL expiry, incidents, recent changes
├── _pending_approvals.md      ← Human sign-off queue for high-impact agent actions
├── _agents/                   ← Instruction files for every AI tool
│   ├── README.md              ← Setup steps and comparison table
│   ├── claude-code.md         ← Source of truth for ~/.claude/CLAUDE.md
│   ├── gemini-cli.md          ← Source of truth for ~/.gemini/GEMINI.md
│   ├── codex.md               ← Source of truth for repo-level AGENTS.md
│   ├── copilot.md             ← Source of truth for .github/copilot-instructions.md
│   ├── opencode.md            ← Referenced via instructions array in opencode.json
│   ├── cursor.md              ← Paste into Cursor User Rules
│   ├── chatgpt.md             ← Paste into ChatGPT Custom Instructions
│   ├── gemini.md              ← Paste into Gemini Custom Instructions
│   ├── grok.md                ← Paste into Grok Customise Grok
│   ├── active.md              ← Live session presence (agents register here)
│   └── registry.md            ← Per-tool capability notes for multi-agent sessions
├── _runtime/                  ← Session event logs, memory candidates, and nightly artifacts
├── _templates/                ← Blank templates for new files
├── _tools/                    ← Optional CLI helpers for search and memory pipeline
├── personal/                  ← Your profile, machines, and dev environments
├── projects/                  ← Your coding projects
├── work/                      ← Work context (non-sensitive)
└── [your-domain]/             ← Add folders for home lab, clients, etc.
```

### The reading protocol (what agents do)

Agents follow a layered loading strategy to avoid blowing the context window:

1. **Read `_index.md`** — one row per project/system, quick orientation
2. **Read `_state.yaml`** — time-sensitive items (SSL expiry, open incidents, pending tasks)
3. **Load specific files** only when the task requires them

This means a session about Project A never loads Project B's files. Context budget is preserved for actual work.

### The writing protocol (how agents update AIKB)

Agents update AIKB when they learn something useful for future sessions:
- A system's state changed
- A decision was made (and the rationale should be preserved)
- A gotcha or pitfall was discovered
- A task was completed or a new one identified

Updates go directly into the relevant file (no append-only corrections), followed by a commit and push. Mid-session checkpoint commits are encouraged.

If you enable runtime memory, the writing protocol also gains a non-canonical staging layer:
- `_runtime/events/` for session observations and closeout captures
- `_pending_approvals.md` for human sign-off items
- `_runtime/candidates/` and related tools for review-before-promotion workflows
- `_runtime/im/` for cross-agent inbox + archive notes (optional; see `docs/agent-im.md`)
