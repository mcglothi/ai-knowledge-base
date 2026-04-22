# Agent Instructions

**Last Updated:** 2026-04-21
**Summary:** Per-agent instruction files for every AI tool in use. Each file contains the exact text to configure that tool, plus setup steps. The files in this directory are the source of truth — when new projects are added, update the relevant file here AND sync to the tool's UI or config location.

---

## Files in this directory

### Shared infrastructure

| File | Purpose |
|------|---------|
| [`registry.md`](registry.md) | One entry per AI tool — capabilities, access mode, gotchas. Read this before working alongside another tool. |
| [`active.md`](active.md) | Live session presence plus repo/scope claims. Agents register at start, clear at end, and should re-check it when unexpected repo dirt appears. |

### Per-tool instructions

| File | Tool | Config mechanism |
|------|------|-----------------|
| [`claude-code.md`](claude-code.md) | Claude Code CLI | `~/.claude/CLAUDE.md` (auto-loaded) |
| [`gemini-cli.md`](gemini-cli.md) | Gemini CLI | `~/.gemini/GEMINI.md` (auto-loaded) |
| [`codex.md`](codex.md) | Codex CLI | `AGENTS.md` in repo root (project-scoped) |
| [`copilot.md`](copilot.md) | GitHub Copilot | `.github/copilot-instructions.md` in repo root |
| [`opencode.md`](opencode.md) | OpenCode TUI/CLI | `~/.config/opencode/opencode.json` → `instructions` array (explicit path) |
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

Optional session-end automation:
See [`../docs/stop-hook-setup.md`](../docs/stop-hook-setup.md) to wire `aikb-session-stop.sh` into `~/.claude/settings.json`.

### Gemini CLI
```bash
cp /path/to/your/AIKB/_agents/gemini-cli.md ~/.gemini/GEMINI.md
```

Optional session-end automation:
See [`../docs/stop-hook-setup.md`](../docs/stop-hook-setup.md) to wire the same Stop hook into `~/.gemini/settings.json`.

### Codex CLI
```bash
cp /path/to/your/AIKB/_agents/codex.md /path/to/your/project/AGENTS.md
```

`install.sh` does not copy the Codex file automatically because Codex instructions are project-scoped. Copy it into each repository where you want AIKB-enabled Codex sessions.

Bulk helper:
```bash
./sync-agents.sh /path/to/project [/path/to/project...]
```

### GitHub Copilot
```bash
./sync-agents.sh --agent copilot /path/to/project
```

This writes `.github/copilot-instructions.md`, which GitHub Copilot uses as repository instructions. To refresh every maintained agent source in another AIKB/template checkout and write project-native Codex/Copilot files, run:
```bash
./sync-agents.sh --all /path/to/AIKB-or-template
```

To refresh local file-backed tool configs:
```bash
./sync-agents.sh --all --global
```

Optional session-end workaround:
Source `_tools/memory-pipeline/codex-wrapper.sh` from your shell config, or run `aikb-session-stop.sh` manually at session end. See [`../docs/stop-hook-setup.md`](../docs/stop-hook-setup.md).

### OpenCode

OpenCode does not auto-discover a global instruction file. You must explicitly add your AIKB instructions file to the `instructions` array in `~/.config/opencode/opencode.json`.

```bash
# If opencode.json already exists — add the instructions key:
# Open ~/.config/opencode/opencode.json and add (or merge):
# "instructions": ["/path/to/your/AIKB/_agents/opencode.md"]

# If you have jq installed, you can do it non-interactively:
AIKB_PATH="/path/to/your/AIKB"
CONFIG="$HOME/.config/opencode/opencode.json"
jq --arg p "$AIKB_PATH/_agents/opencode.md" \
  'if .instructions then .instructions += [$p] else .instructions = [$p] end' \
  "$CONFIG" > "$CONFIG.tmp" && mv "$CONFIG.tmp" "$CONFIG"

# No file copy needed — OpenCode loads the AIKB file directly from its path.
```

`install.sh` handles this automatically when OpenCode is detected and `jq` is available.

Also add your `GITHUB_TOKEN` to the `github-aikb` MCP env block so the MCP server can authenticate:
```json
"mcp": {
  "github-aikb": {
    "type": "local",
    "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
    "enabled": true,
    "env": { "GITHUB_TOKEN": "your-token-here" }
  }
}
```

See [`../docs/mcp-setup.md`](../docs/mcp-setup.md) for full MCP setup instructions.

Optional session-end stop hook (same pattern as Codex):
```bash
# Add to ~/.zshrc — runs aikb-session-stop.sh after every opencode session
source /path/to/your/AIKB/_tools/memory-pipeline/opencode-wrapper.sh
```
Or run `aikb-session-stop.sh` manually at session end. See [`../docs/stop-hook-setup.md`](../docs/stop-hook-setup.md).

**Important:** A project-level `opencode.json` overrides the global config. If you open OpenCode inside a project that has its own `opencode.json`, verify that AIKB instructions are also referenced there (or add a local `instructions` entry).

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
- `python3 _tools/memory-pipeline/runtime_cli.py template-sync --auto-check` reports framework updates from the public template

---

## Key difference: file-based vs UI-based

**Claude Code and Gemini CLI** read instruction files directly from disk and optionally support MCP servers. An agent can update AIKB programmatically via the GitHub MCP server or a local clone. After editing instruction files, commit here and copy to the config location.

**Codex CLI** reads instructions from repo-level `AGENTS.md`. Keep `_agents/codex.md` as source of truth and copy it into each Codex project workspace.

**GitHub Copilot** reads repository custom instructions from `.github/copilot-instructions.md`. Keep `_agents/copilot.md` as source of truth and sync it into each repository where Copilot should receive AIKB-aware context.

**OpenCode** does not auto-discover a global instruction file. The `instructions` array in `~/.config/opencode/opencode.json` must explicitly list file paths. Point it directly at `_agents/opencode.md` — no copy step needed. Note: a project-level `opencode.json` overrides the global one, so verify AIKB instructions are referenced in each project context you care about.

**Cursor** reads instruction files from disk but currently has no MCP-based AIKB write access without additional configuration.

**ChatGPT, Gemini (web), and Grok** are UI-configured only. They cannot read local files. The workflow is:
1. Keep these `_agents/` files as the source of truth.
2. Paste content into the tool's settings UI manually.
3. These tools can read `_index.md` if you paste it at the start of a session.
