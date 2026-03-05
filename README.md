<p align="center">
  <img src="docs/assets/logo.svg" width="160" />
</p>

<h1 align="center">AIKB — AI Knowledge Base</h1>

<p align="center">
  <strong>Unified long-term memory for the agentic era.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License" />
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome" />
  <img src="https://img.shields.io/badge/Maintenance-Active-green.svg" alt="Maintenance" />
  <img src="https://img.shields.io/badge/Status-Public--Template-indigo.svg" alt="Status" />
</p>

---

### Give your AI agents persistent memory that survives between sessions, works across multiple AI tools, and stays in sync on any machine.

AIKB is a structured Markdown knowledge base designed to eliminate context loss. Your AI agents read it at the start of each session to orient themselves and write back as they learn, ensuring they always know your environment, projects, and history.

[**Get Started**](#quick-start) • [**How It Works**](#how-it-works) • [**Tool Support**](#ai-tool-compatibility) • [**MCP Server**](#mcp-server-setup-optional)

---

## 🧠 Why AIKB?

| Problem | AIKB Solution |
| :--- | :--- |
| **Amnesia** | Persistent memory across sessions. |
| **Fragmentation** | Shared context between Claude, Gemini, ChatGPT, etc. |
| **Blindness** | Machine-aware profiles (paths, tools, env). |
| **Exposure** | Secrets-safe reference system (never store keys). |
| **Bloat** | Layered loading protects your context window. |

---

## 🛠️ AI Tool Compatibility

AIKB is designed to be the "source of truth" for all your AI assistants.

| Tool | Integration | Mode |
| :--- | :--- | :--- |
| **Claude Code** | `~/.claude/CLAUDE.md` | Local / MCP |
| **Gemini CLI** | `~/.gemini/GEMINI.md` | Local / MCP |
| **Codex CLI** | `AGENTS.md` | Local |
| **Cursor** | User Rules | Local |
| **ChatGPT** | Custom Instructions | Manual |

---

## 🚀 Quick Start

### 1. Create your repo
Click **[Use this template](../../generate)** to create your own private `AIKB` repository.

### 2. Install
```bash
gh repo create AIKB --template mcglothi/ai-knowledge-base --private --clone
cd AIKB
chmod +x install.sh && ./install.sh
```

### 3. Configure
Follow the guide in [`_agents/README.md`](_agents/README.md) to link your AIKB to your favorite tools.

---

## 🏗️ Repository Architecture

```text
AIKB/
├── 🗂️ _agents/       # Instruction files for every AI tool
├── 🗂️ personal/      # Your profile, machines, and environments
├── 🗂️ projects/      # Your coding projects & technical context
├── 🗂️ work/          # Professional context (non-sensitive)
├── 📄 _index.md      # High-level system orientation (read first)
└── 📄 _state.yaml    # Real-time surface (SSL, incidents, status)
```

---

## 🔄 Staying in Sync

The framework evolves. Stay updated without touching your personal content:

```bash
./sync.sh
```
*This fetches upstream improvements and safely applies them to your private repo.*

---

## 🔒 Secrets Management

**AIKB never stores credentials.** It uses a reference system:

`[Stored in Vaultwarden: PAT/GitHub/AIKB Token]`

Works with **1Password**, **Bitwarden**, **Vaultwarden**, and more. See [Secrets Management](docs/secrets-management.md).

---

<p align="center">
  <i>"Context is the new currency."</i>
</p>
