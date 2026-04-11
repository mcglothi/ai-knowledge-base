<p align="center">
  <img src="_branding/hero-graphic.png" alt="AIKB" width="1000" />
</p>


<h1 align="center">AIKB — AI Knowledge Base</h1>

<p align="center">
  <strong>Persistent memory for your AI tools.</strong>
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

### Persistent memory for your AI tools.

AIKB gives your agents shared context that survives across sessions, tools, and machines. It stays local-first, Git-backed, and fully inspectable, so your memory system feels like infrastructure you control instead of a black box you hope is right.

> Your AI tools should not start from zero.

[**Get Started**](#quick-start) • [**How It Works**](#how-it-works) • [**Tool Support**](#ai-tool-compatibility)

---

## Why AIKB

Every AI session starts from zero. You re-explain your projects, your stack, your preferences, and your constraints every time. Context windows are finite, sessions end, and the useful working memory disappears with them.

If you use multiple tools, the problem gets worse. Claude, Gemini, Codex, Cursor, ChatGPT, and web copilots all end up relearning the same context from scratch.

## The Solution

AIKB is a structured knowledge base stored in a private GitHub repo. Your agents read it at the start of a session to orient themselves, and write back to it when they learn something durable. The result is memory that stays inspectable, portable, and under your control.

```text
Session starts → Agent reads AIKB → Agent knows everything
Session ends   → Agent writes updates → Next session picks up where this one left off
```

---

## Key Features

- **Shared context across tools** — one memory layer for Claude Code, Gemini CLI, Codex, Cursor, ChatGPT, and more
- **Local-first and Git-backed** — durable memory in files you can inspect, diff, sync, and own
- **Two access modes** — local clone for speed, or GitHub MCP for remote sessions and new machines
- **Semantic search** — optional `aikb_search` MCP tool for natural-language queries across your knowledge base
- **Runtime memory pipeline** — optional `_runtime/` staging and `_tools/memory-pipeline/` helpers for event capture, candidate review, nightly maintenance, and dream-style consolidation
- **Operator HUD + approvals log** — optional `runtime_cli.py` and `_pending_approvals.md` workflows for focus, verification, and sign-off visibility
- **Structured closeout capture** — optional `runtime_cli.py closeout` command for end-of-session memory capture when you wrap up work
- **Operator intents** — optional runbooks that teach your agents how to execute your shorthand requests and recurring workflows
- **Nightly dream cycle** — optional bundle, quality, contradiction, and distilled-memory artifacts for higher-signal overnight memory synthesis
- **Layered loading** — agents read only what they need, preserving context window budget
- **Checkpoint commits** — agents can save progress during long sessions so memory survives interruptions
- **Secrets-safe** — credentials stay in your secrets manager; AIKB stores references only
- **Machine-aware** — each machine gets a profile so the agent uses the right paths, tools, and conventions

## Product Snapshot

| What it gives you | Why it matters |
|-------------------|----------------|
| Persistent session memory | Stop repeating the same setup and project context |
| Inspectable storage | Trust the memory because it lives in Markdown + Git |
| Cross-tool continuity | Switch tools without losing your working context |
| Structured updates | Capture decisions, gotchas, blockers, and state changes cleanly |
| Optional dream consolidation | Turn noisy daily memory into bundled, reviewable nightly summaries |

---

## What The Operator Loop Looks Like

The core AIKB workflow is simple:

```text
Start session -> agent reads _index.md + _state.yaml
Do work        -> capture decisions, blockers, and approvals as needed
Wrap up        -> record a structured closeout event
Next session   -> load the latest state instead of starting cold
```

If you enable the runtime helpers, that operator loop becomes tangible:

```bash
# See what AIKB thinks is active right now
python3 _tools/memory-pipeline/runtime_cli.py hud

# Keep a current objective visible during longer work
python3 _tools/memory-pipeline/runtime_cli.py focus set \
  --task "Ship dashboard cleanup" \
  --verify "Run tests and confirm deploy status"

# When you finish for now, capture the wrap-up state
python3 _tools/memory-pipeline/runtime_cli.py closeout \
  --phrase "lets wrap up for now"
```

That closeout event is stored in `_runtime/events/YYYY-MM-DD.ndjson`, so the next session can recover not just what exists in your docs, but how the current stretch of work ended.

By default, those raw runtime event files are local working memory. Promote durable signal into candidates, approvals, summaries, or canonical docs instead of auto-committing every event log.

---

## Intelligence Tools

The AIKB includes a set of optional CLI tools to help automate knowledge curation and retrieval:

- **Ambient Context Injection** (`_tools/memory-pipeline/ambient_ask.sh`) — A wrapper for your AI CLI that automatically injects relevant facts from your AIKB into your prompt *before* the agent starts.
- **Temporal Knowledge Graph** (`_tools/memory-pipeline/build_temporal_graph.py`) — Generates a structured JSON graph of your knowledge, extracting entities like IPs and tools to track how they change over time.
- **Semantic Search** (`_tools/memory-pipeline/memory_search.py`) — A hybrid keyword/semantic search tool to quickly locate specific memories across your entire repository.

---

## AI Tool Compatibility

| Tool | Integration | AIKB Access Mode |
|------|-------------|-----------------|
| Claude Code | `~/.claude/CLAUDE.md` auto-loaded | Local clone or GitHub MCP |
| Gemini CLI | `~/.gemini/GEMINI.md` auto-loaded | Local clone or GitHub MCP |
| Codex CLI | `AGENTS.md` in project root | Local clone (or MCP if configured) |
| Cursor | User Rules (Settings UI) | Local clone |
| ChatGPT | Custom Instructions (Settings UI) | Manual paste at session start |
| Google Gemini | Custom Instructions (Settings UI) | Manual paste at session start |
| Grok | Customise Grok (Settings UI) | Manual paste at session start |

---

## Quick Start

**Prerequisites:** Git, a GitHub account, and at least one AI tool.

### 1. Create your private AIKB repo

Click **[Use this template](../../generate)** → name it `AIKB` → set it to **Private**.

Or from the CLI:
```bash
gh repo create AIKB --template mcglothi/ai-knowledge-base --private --clone
cd AIKB
```

### 2. Run the setup script

```bash
chmod +x install.sh
./install.sh
```

The script will ask for your GitHub username, repo name, and preferred local path, then generate personalized agent instruction files.
If you cloned from your own GitHub repo first, it auto-detects the GitHub username and repo name from `origin`, so most people can accept the defaults.

### 3. Configure your primary AI tool

Follow the guide for your tool in [`_agents/README.md`](_agents/README.md):

- **Claude Code** — copy `_agents/claude-code.md` to `~/.claude/CLAUDE.md`
- **Gemini CLI** — copy `_agents/gemini-cli.md` to `~/.gemini/GEMINI.md`
- **Codex CLI** — copy `_agents/codex.md` to `AGENTS.md` in each Codex project repo, or use `./sync-agents.sh /path/to/project [...]`
- **Cursor** — paste `_agents/cursor.md` into Settings → Cursor Settings → Rules → User Rules
- **ChatGPT / Gemini / Grok** — paste the relevant file into Custom Instructions

### 4. Fill in your personal files

`install.sh` creates these files automatically — they just need your details:

- `personal/profile.md` — your background, skills, and communication preferences
- `personal/dev-environment/README.md` — your machine inventory (hostnames, OS, code roots)
- `personal/dev-environment/<hostname>.md` — installed tools on your primary machine

The `example/` directory has annotated examples showing what good entries look like.

### 5. (Optional) Set up semantic search

Run one command to enable natural language queries across all your AIKB files:

```bash
bash _tools/aikb-search/setup.sh
```

After setup, your agent can answer questions like "what's currently broken?" or "what SSL certs expire soon?" without you having to know which file to load. See [`docs/search-setup.md`](docs/search-setup.md) for details.

### 6. (Optional) Enable runtime memory workflow

If you want more than static docs, AIKB also supports an operator-facing runtime layer:

```bash
python3 _tools/memory-pipeline/runtime_cli.py hud
python3 _tools/memory-pipeline/runtime_cli.py closeout --phrase "lets wrap up for now"
python3 _tools/memory-pipeline/approvals_cli.py list
```

This gives you:
- a compact session HUD
- a structured wrap-up capture path
- a visible sign-off queue for high-impact actions

You can also capture recurring shorthand requests in a runbook so future sessions do not need to rediscover them:

```text
"restart staging"
"wrap up for now"
"wake lab server"
```

See [`home-lab/runbooks/operator-intents.md`](home-lab/runbooks/operator-intents.md) and [`_templates/operator-intent-template.md`](_templates/operator-intent-template.md).

### 7. Learn the operator loop

If you want the fastest path from "installed" to "this feels useful," follow the lightweight operator loop:

```bash
python3 _tools/memory-pipeline/runtime_cli.py hud
python3 _tools/memory-pipeline/runtime_cli.py focus set \
  --task "Your current task" \
  --verify "What you will verify next"
python3 _tools/memory-pipeline/runtime_cli.py closeout \
  --phrase "lets wrap up for now"
```

See [`docs/operator-loop.md`](docs/operator-loop.md) for the public-facing workflow, when to use approvals, and how operator intents fit into the loop.

If you want a terminal walkthrough instead of reading docs, run:

```bash
bash _tools/feature-tour.sh
```

### 8. Start a session

Launch your AI tool. It will read AIKB and immediately know who you are, what machines you use, and what you're working on.

### On a new machine

Clone your private AIKB repo and run `install.sh` again. It detects the new hostname, scaffolds a machine profile for it, and sets up your AI tools — your existing personalization is already in the repo, no re-entering needed.

---

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
4. In normal mode, show you exactly what changed in the framework dirs (`AGENTS.md`, `_agents/`, `_templates/`, `_tools/`, `docs/`, and selected root framework files)
5. Ask for confirmation before applying anything
6. Re-apply your personal values (username, repo name, paths, secrets manager) automatically
7. Re-copy to `~/.claude/CLAUDE.md` or `~/.gemini/GEMINI.md` if you set those up during install
8. Commit the result

**What gets updated:** `AGENTS.md`, `_agents/`, `_templates/`, `_tools/`, `docs/`, `_pending_approvals.md`, `sync.sh`, `sync-agents.sh`, `install.sh`, `.gitignore`

**What is never touched:** `_index.md`, `_state.yaml`, `personal/`, `projects/`, `work/`, and any other dirs you've created

Suggested habit:
- Let agents run `python3 _tools/memory-pipeline/runtime_cli.py template-sync --auto-check` during session setup or when you explicitly ask about updates.
- Keep the default cadence at `7` days unless the public template is changing quickly; use `--set-interval 3` for active rollout periods or `--set-interval 14` for a quieter cadence.
- Keep actual `./sync.sh` application operator-approved, since it changes tracked framework files.
- After a framework sync, re-sync downstream Codex project repos with `./sync-agents.sh`.

---

## How It Works

### Repository structure

```text
AIKB/
├── README.md                  ← Human-readable overview (you're reading it)
├── _index.md                  ← One-line status for every project (agents read this first)
├── _state.yaml                ← Time-sensitive surface: SSL expiry, incidents, recent changes
├── _pending_approvals.md      ← Human sign-off queue for high-impact agent actions
├── _agents/                   ← Instruction files for every AI tool
│   ├── README.md              ← Setup steps and comparison table
│   ├── claude-code.md         ← Source of truth for ~/.claude/CLAUDE.md
│   ├── gemini-cli.md          ← Source of truth for ~/.gemini/GEMINI.md
│   ├── codex.md               ← Source of truth for repo-level AGENTS.md
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
