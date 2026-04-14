<p align="center">
  <img src="_branding/hero-graphic.png" alt="AIKB" width="1000" />
</p>

<p align="center">
  <img src="_branding/demo-installer.gif" alt="AIKB installer" width="800" />
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

<p align="center">
  <img src="_branding/demo-wakeup.gif" alt="AIKB session wake-up" width="800" />
  <br><em>What your agent sees at the start of every session.</em>
</p>

---

## Key Features

- **Shared context across tools** — one memory layer for Claude Code, Gemini CLI, Codex, OpenCode, Cursor, ChatGPT, and more
- **Local-first and Git-backed** — durable memory in files you can inspect, diff, sync, and own
- **Two access modes** — local clone for speed, or GitHub MCP for remote sessions and new machines
- **Advanced search & context expansion** — `aikb_search` MCP tool for natural-language queries; hybrid BM25 + vector retrieval with **Graph-RAG relationship expansion**, intent-aware priors, and 14-day recency decay
- **In-session memory indexing** — `aikb_remember` captures durable memories from within a session; the search indexer automatically scans these event logs, making memories searchable instantly
- **Session-end automation** — Claude Code and Gemini CLI can run the AIKB Stop hook automatically; Codex can use the shipped wrapper or manual fallback
- **Session-start briefing** — `runtime_cli.py wake-up` synthesizes a compact briefing from recent events and current state so agents orient in seconds, not minutes
- **Interactive candidate review** — `aikb_review.py` presents queued memory candidates one-by-one for approve/reject/skip with source event drill-down
- **Retention enforcement** — `retention_check.py` flags stale docs, forgotten pending items, and terminal candidate bundles for cleanup
- **Local model offload** — `sidecar.py` optional helper routes scoring, briefing synthesis, and patch drafting to a local Ollama instance; configurable via env vars, falls back silently when unavailable
- **Runtime memory pipeline** — `_runtime/` staging and `_tools/memory-pipeline/` helpers for event capture, candidate review, nightly maintenance, and dream-style consolidation
- **Operator HUD + approvals log** — `runtime_cli.py` and `_pending_approvals.md` workflows for focus, verification, and sign-off visibility
- **Operator intents** — runbooks that teach your agents how to execute your shorthand requests and recurring workflows
- **Layered loading** — agents read only what they need, preserving context window budget
- **Checkpoint commits** — agents save progress during long sessions so memory survives interruptions
- **Mind Meld** — agents read the shared runtime event log to see what other agents are doing right now; no extra infrastructure required
- **Token economy** — compact triggers, AIKB-as-memory-buffer pattern, and bash output discipline keep API costs under control across long sessions; see `docs/token-economy.md`
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

## Feature Status

What's built, what's a prototype, and what's planned. No vague "coming soon."

| Feature | Status | How to use |
|---------|--------|------------|
| Session start briefing | ✅ Built | `runtime_cli.py wake-up` |
| Manual memory capture | ✅ Built | `runtime_cli.py capture` |
| In-session memory writes (MCP) | ✅ Built | `aikb_remember` MCP tool |
| Session HUD | ✅ Built | `runtime_cli.py hud` |
| Candidate pipeline | ✅ Built | `build_candidates.py` → `review_candidates.py` |
| Interactive candidate review | ✅ Built | `aikb_review.py` |
| Session closeout capture | ✅ Built | `runtime_cli.py closeout` |
| Claude Code Stop hook | ✅ Built | `aikb-session-stop.sh` + `docs/stop-hook-setup.md` |
| Gemini CLI Stop hook | ✅ Built | `aikb-session-stop.sh` + `docs/stop-hook-setup.md` |
| Codex closeout workaround | ✅ Built | `codex-wrapper.sh` or manual `aikb-session-stop.sh` |
| Keyword search | ✅ Built | `memory_search.py --mode keyword` |
| Semantic / hybrid search | ✅ Built | `memory_search.py --mode hybrid` (requires `sentence-transformers`) |
| MCP search tool | ✅ Built | `aikb_search` via `_tools/aikb-search/` |
| Retention policy enforcement | ✅ Built | `retention_check.py` |
| Operator intents / runbooks | ✅ Built | `_templates/operator-intent-template.md` |
| Template sync / self-update | ✅ Built | `./sync.sh`, `runtime_cli.py template-sync` |
| Nightly maintenance | ✅ Built | `nightly_maintenance.py`, cron/launchd installers |
| Local model offload (sidecar) | ✅ Built | `sidecar.py` + `AIKB_SIDECAR_URL` env var |
| Mind Meld (cross-agent awareness) | ✅ Built | Read `_runtime/events/YYYY-MM-DD.ndjson`; see agent instruction files |
| Dream cycle consolidation | 🔨 Prototype | `dream_cycle.py` (outputs not yet auto-promoted) |
| Automatic conflict detection | 🔨 Prototype | `conflict_scan.py` (offline, not wired to writes) |
| Sidecar-enriched pipeline scoring | 🔨 In progress | `build_candidates.py` + `sidecar.py` |
| LoRA fine-tuning from memory | 🔬 Research | Future roadmap |

---

## What The Operator Loop Looks Like

The core AIKB workflow is simple:

```text
Start session -> agent runs wake-up, reads recent state
Do work        -> capture decisions, blockers, and approvals as needed
Wrap up        -> Stop hook, wrapper, or manual closeout records the end state
Next session   -> wake-up synthesizes what changed, agent starts informed
```

If you enable the runtime helpers, that operator loop becomes tangible:

```bash
# Synthesize a compact briefing from recent events and current state
python3 _tools/memory-pipeline/runtime_cli.py wake-up

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

## Intelligence Tools

The AIKB includes a set of optional CLI tools to help automate knowledge curation and retrieval:

- **Session Briefing** (`runtime_cli.py wake-up`) — Synthesizes a compact session-start briefing from recent events and current state. Agents orient in seconds instead of reading through full docs.
- **Interactive Candidate Review** (`aikb_review.py`) — Presents queued memory candidates one-by-one with `[a]pprove / [r]eject / [s]kip / [?]events` prompts. Shows source events on demand, tracks progress, offers to run `propose_patches.py` at the end.
- **Retention Enforcer** (`retention_check.py`) — Scans for stale docs (>90 days), forgotten `_state.yaml` pending items without priority, complete/decommissioned index entries linked to old docs, and fully-terminal candidate bundles ready for deletion. Run with `--delete-terminal-candidates` to clean up automatically.
- **Hybrid Search** (`memory_search.py`) — Keyword, semantic (requires `sentence-transformers`), or hybrid mode. Run `memory_search.py --rebuild-index` to build the vector index after install.
- **MCP Search + Memory** (`_tools/aikb-search/server.py`) — Registers `aikb_search` and `aikb_remember` as MCP tools. Implements advanced retrieval with **Graph-RAG**, intent-aware priors, temporal filters, and linear recency decay.
- **Local Model Offload** (`sidecar.py`) — Optional helper that routes scoring, briefing synthesis, and patch drafting to a local Ollama instance. Set `AIKB_SIDECAR_URL` to your Ollama endpoint (default: `http://localhost:11434`). Falls back silently to rule-based behavior when unreachable. Keeps frontier model context budget for reasoning, not document processing.
- **Ambient Context Injection** (`ambient_ask.sh`) — A wrapper for your AI CLI that automatically injects relevant facts from your AIKB into your prompt *before* the agent starts.
- **Temporal Knowledge Graph** (`build_temporal_graph.py`) — Generates a structured JSON graph of your knowledge, extracting entities like IPs and tools to track how they change over time.

---

## AI Tool Compatibility

| Tool | Integration | AIKB Access Mode |
|------|-------------|-----------------|
| Claude Code | `~/.claude/CLAUDE.md` auto-loaded | Local clone or GitHub MCP |
| Gemini CLI | `~/.gemini/GEMINI.md` auto-loaded | Local clone or GitHub MCP |
| Codex CLI | `AGENTS.md` in project root | Local clone (or MCP if configured) |
| OpenCode | `instructions` array in `~/.config/opencode/opencode.json` | Local clone or GitHub MCP |
| Cursor | User Rules (Settings UI) | Local clone |
| ChatGPT | Custom Instructions (Settings UI) | Manual paste at session start |
| Google Gemini | Custom Instructions (Settings UI) | Manual paste at session start |
| Grok | Customise Grok (Settings UI) | Manual paste at session start |

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

### Step 3: Push and fill in your profile

```bash
git push origin main
```

Then open these two files and fill in the `[TODO]` sections:
- `personal/profile.md` — your background, skills, stack
- `personal/dev-environment/[hostname].md` — tools on this machine

Once filled, agents won't ask "what's your stack?" or "what machine are you on?" again.

---

### Go deeper

| Goal | Where to look |
|------|--------------|
| Full setup walkthrough | [docs/getting-started.md](docs/getting-started.md) |
| Add MCP search + in-session memory | [docs/mcp-setup.md](docs/mcp-setup.md) |
| Set up session-end automation | [docs/stop-hook-setup.md](docs/stop-hook-setup.md) |
| Configure the runtime memory workflow | [docs/search-setup.md](docs/search-setup.md) |
| Connect a local model sidecar | [docs/getting-started.md#local-model](docs/getting-started.md) |
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
