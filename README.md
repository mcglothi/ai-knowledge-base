# AIKB — AI Knowledge Base

> Give your AI agents persistent memory that survives between sessions, works across multiple AI tools, and stays in sync on any machine.

---

## The Problem

Every AI session starts from zero. You re-explain your projects, your stack, your preferences — every time. Context windows are finite, sessions end, and nothing carries over. If you use multiple AI tools (Claude, Gemini, ChatGPT, Cursor), you're explaining the same things repeatedly across all of them.

## The Solution

AIKB is a **structured Markdown knowledge base** stored in a private GitHub repo. Your AI agents read it at the start of each session to orient themselves, and write back to it as they learn new things. The result is an AI that already knows your environment, your projects, and your history — every time.

```
Session starts → Agent reads AIKB → Agent knows everything
Session ends   → Agent writes updates → Next session picks up where this one left off
```

---

## Key Features

- **Multi-agent, multi-tool** — one knowledge base, shared across Claude Code, Gemini CLI, ChatGPT, Cursor, and more
- **Two access modes** — local clone (fast, offline-capable) or GitHub MCP (no clone needed, works from any machine)
- **Layered loading** — agents read only what they need, protecting context window budget
- **Checkpoint commits** — agents commit progress mid-session so nothing is lost if a session drops
- **Secrets-safe** — credentials are referenced by name (in your secrets manager), never stored in the repo
- **Machine-aware** — each machine has a profile so the agent uses the right paths and tools
- **Any secrets manager** — works with 1Password, Bitwarden, Vaultwarden, system keychain, or environment variables

---

## AI Tool Compatibility

| Tool | Integration | AIKB Access Mode |
|------|-------------|-----------------|
| Claude Code | `~/.claude/CLAUDE.md` auto-loaded | Local clone or GitHub MCP |
| Gemini CLI | `~/.gemini/GEMINI.md` auto-loaded | Local clone or GitHub MCP |
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
gh repo create AIKB --template mcglothi/aikb --private --clone
cd AIKB
```

### 2. Run the setup script

```bash
chmod +x install.sh
./install.sh
```

The script will ask for your GitHub username, repo name, and preferred local path, then generate personalized agent instruction files.

### 3. Configure your primary AI tool

Follow the guide for your tool in [`_agents/README.md`](_agents/README.md):

- **Claude Code** — copy `_agents/claude-code.md` to `~/.claude/CLAUDE.md`
- **Gemini CLI** — copy `_agents/gemini-cli.md` to `~/.gemini/GEMINI.md`
- **Cursor** — paste `_agents/cursor.md` into Settings → Cursor Settings → Rules → User Rules
- **ChatGPT / Gemini / Grok** — paste the relevant file into Custom Instructions

### 4. Personalize your knowledge base

Edit these files to describe yourself and your environment:

- [`example/personal/profile.md`](example/personal/profile.md) → move to `personal/profile.md` and fill in your background and skills
- [`example/personal/dev-environment.md`](example/personal/dev-environment.md) → move to `personal/dev-environment/README.md` and describe your machines

### 5. Start a session

Launch your AI tool. It will read AIKB and immediately know who you are, what machines you use, and what you're working on.

---

## How It Works

### Repository structure

```
AIKB/
├── README.md                  ← Human-readable overview (you're reading it)
├── _index.md                  ← One-line status for every project (agents read this first)
├── _state.yaml                ← Time-sensitive surface: SSL expiry, incidents, recent changes
├── _agents/                   ← Instruction files for every AI tool
│   ├── README.md              ← Setup steps and comparison table
│   ├── claude-code.md         ← Source of truth for ~/.claude/CLAUDE.md
│   ├── gemini-cli.md          ← Source of truth for ~/.gemini/GEMINI.md
│   ├── cursor.md              ← Paste into Cursor User Rules
│   ├── chatgpt.md             ← Paste into ChatGPT Custom Instructions
│   ├── gemini.md              ← Paste into Gemini Custom Instructions
│   ├── grok.md                ← Paste into Grok Customise Grok
│   ├── active.md              ← Live session presence (agents register here)
│   └── registry.md            ← Per-tool capability notes for multi-agent sessions
├── _templates/                ← Blank templates for new files
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

---

## Secrets Management

**AIKB never stores credentials.** API keys, passwords, and tokens belong in your secrets manager. AIKB stores only the reference:

```markdown
[Stored in 1Password: Work/AWS Access Key]
[Stored in Vaultwarden: PAT/GitHub/AIKB Token]
[Stored in environment: $ANTHROPIC_API_KEY]
```

AIKB works with any secrets manager. See [`docs/secrets-management.md`](docs/secrets-management.md) for integration patterns with 1Password, Bitwarden, Vaultwarden, system keychain, and environment variables.

---

## Adding New Domains

Create a folder for any area of your life you want to track:

```bash
mkdir -p AIKB/home-lab
cp AIKB/_templates/domain-readme.md AIKB/home-lab/README.md
```

Common domains people use:
- `personal/` — profile, skills, dev environments
- `projects/` — personal coding projects
- `work/` — professional context
- `home-lab/` — self-hosted services, infrastructure
- `clients/` — freelance or consulting work

After adding a domain, update `_index.md` so agents know it exists, and re-sync your agent instruction files.

---

## MCP Server Setup (Optional)

The GitHub MCP server lets agents access AIKB without a local clone — useful when working from a new machine, a cloud IDE, or anywhere you don't have a local checkout.

See [`docs/mcp-setup.md`](docs/mcp-setup.md) for setup instructions.

Short version for Claude Code:
```bash
claude mcp add github-aikb \
  -e GITHUB_TOKEN=$(cat ~/.aikb_token) \
  -- npx -y @modelcontextprotocol/server-github
```

---

## File Standards

Every file in AIKB follows a consistent format so agents can orient quickly:

```markdown
# Title

**Last Updated:** YYYY-MM-DD
**Summary:** One or two sentences — what this covers and whether it's still active.

---

[content]
```

See [`_templates/file-template.md`](_templates/file-template.md) for the full template.

Key rules:
- One topic per file — don't mix concerns that are never needed at the same time
- Keep files under 300 lines — split when they grow larger
- Fix stale info in place — never append corrections below wrong content
- Use status indicators: `✅` done, `⬜` pending, `⚠️` needs attention

---

## Security Considerations

- **Private repo** — your AIKB repo should be private. It will contain system details, architecture notes, and references to sensitive resources.
- **No credentials** — never commit API keys, passwords, or tokens. Reference them by name in your secrets manager.
- **Review before pasting** — when configuring UI-based tools (ChatGPT, etc.), review the content before pasting to ensure no sensitive data was added.
- **Rotate on exposure** — if a credential is accidentally committed, rotate it immediately and remove it from git history.

---

## Contributing

Found a bug or have an idea? Open an issue or submit a PR. The most valuable contributions are:
- Agent instruction templates for tools not yet covered
- Secrets manager integration patterns
- Example domain structures (with all personal info removed)

---

## License

MIT — use freely, adapt it to your workflow.
