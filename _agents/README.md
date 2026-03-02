# Agent Instructions

**Last Updated:** YYYY-MM-DD
**Summary:** Per-agent instruction files for every AI tool in use. Each file contains the exact text to configure that tool, plus setup steps. The files in this directory are the source of truth — when new projects are added, update the relevant file here AND sync to the tool's UI or config location.

---

## Files in this directory

### Shared infrastructure

| File | Purpose |
|------|---------|
| [`registry.md`](registry.md) | One entry per AI tool — capabilities, access mode, gotchas. Read this before working alongside another tool. |
| [`active.md`](active.md) | Live session presence. Agents register at start, clear at end. Pull before writes if another agent is listed. |

### Per-tool instructions

| File | Tool | Config mechanism |
|------|------|-----------------|
| [`claude-code.md`](claude-code.md) | Claude Code CLI | `~/.claude/CLAUDE.md` (auto-loaded) |
| [`gemini-cli.md`](gemini-cli.md) | Gemini CLI | `~/.gemini/GEMINI.md` (auto-loaded) |
| [`codex.md`](codex.md) | Codex CLI | `AGENTS.md` in repo root (project-scoped) |
| [`cursor.md`](cursor.md) | Cursor IDE | Settings → Cursor Settings → Rules → User Rules |
| [`chatgpt.md`](chatgpt.md) | ChatGPT | Settings → Personalization → Custom Instructions |
| [`gemini.md`](gemini.md) | Google Gemini | Settings → Custom Instructions |
| [`grok.md`](grok.md) | Grok | Settings → Customise Grok |

---

## Setup by tool

### Claude Code
```bash
# After running install.sh (it does this automatically if Claude Code is detected)
cp /path/to/your/AIKB/_agents/claude-code.md ~/.claude/CLAUDE.md

# Re-sync whenever agent instructions are updated:
cp /path/to/your/AIKB/_agents/claude-code.md ~/.claude/CLAUDE.md
```

Optional — GitHub MCP server for remote AIKB access:
```bash
# See docs/mcp-setup.md for full instructions
claude mcp add github-aikb \
  -e GITHUB_TOKEN=$(cat ~/.aikb_token) \
  -- npx -y @modelcontextprotocol/server-github
```

### Gemini CLI
```bash
cp /path/to/your/AIKB/_agents/gemini-cli.md ~/.gemini/GEMINI.md
```

### Codex CLI
```bash
cp /path/to/your/AIKB/_agents/codex.md /path/to/your/project/AGENTS.md
```

### Cursor
Cursor Settings → Rules → User Rules → paste the content of `cursor.md`.

### ChatGPT / Gemini (web) / Grok
These tools are UI-configured only. Workflow:
1. The files in `_agents/` are the source of truth.
2. Open the tool's settings and paste the relevant file's content into Custom Instructions.
3. Re-paste whenever instructions are updated.

---

## When to update these files

Update the relevant agent file(s) — and re-sync to the tool — when:
- A new top-level domain folder is added (e.g. `home-lab/`, `clients/`)
- A new project is added that agents should know about by default
- Machine hostnames or paths change

---

## Key difference: file-based vs UI-based

**Claude Code and Gemini CLI** read instruction files directly from disk and optionally support MCP servers. An agent can update AIKB programmatically via the GitHub MCP server or a local clone. After editing instruction files, commit here and copy to the config location.

**Codex CLI** reads instructions from repo-level `AGENTS.md`. Keep `_agents/codex.md` as source of truth and copy it into each Codex project workspace.

**Cursor** reads instruction files from disk but currently has no MCP-based AIKB write access without additional configuration.

**ChatGPT, Gemini (web), and Grok** are UI-configured only. They cannot read local files. The workflow is:
1. Keep these `_agents/` files as the source of truth.
2. Paste content into the tool's settings UI manually.
3. These tools can read `_index.md` if you paste it at the start of a session.
