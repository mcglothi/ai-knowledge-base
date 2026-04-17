# AI Tool Registry

**Last Updated:** 2026-04-17 for each AI tool in use. Read this when working in a multi-agent setup to understand what each tool can and cannot do.

---

## Tool Comparison

| Tool | AIKB Access | Can Write | MCP Support | Context Limit | Best For |
|------|-------------|-----------|-------------|---------------|----------|
| Claude Code | Local clone or MCP | Yes | Yes | Large | Terminal/code tasks, long sessions |
| Gemini CLI | Local clone or MCP | Yes | Yes | Large | Terminal/code tasks |
| Codex CLI | Local clone (or MCP if configured) | Yes | Yes | Large | Code edits with repo-scoped instructions |
| OpenCode | Local clone or MCP | Yes | Yes | Large | Terminal/code tasks, multi-provider, local models |
| GitHub Copilot CLI | Local clone or MCP | Yes | Yes | Large | Terminal/code tasks, GitHub-native workflows |
| Cursor | Local clone | Yes (manual) | No (without config) | Large | IDE-integrated coding |
| ChatGPT | Paste only | No (manual) | No | Medium | Ideation, writing, one-off questions |
| Google Gemini | Paste only | No (manual) | No | Large | Research, writing |
| Grok | Paste only | No (manual) | No | Medium | Quick lookups |

---

## Per-tool Notes

### Claude Code
- Reads `~/.claude/CLAUDE.md` automatically at startup
- Supports MCP servers — can read/write AIKB programmatically via `github-aikb` MCP
- Checkpoint commit support built into instructions
- Best tool for long, complex sessions with AIKB updates

### Gemini CLI
- Reads `~/.gemini/GEMINI.md` automatically at startup
- Supports MCP servers
- Similar capability profile to Claude Code

### Codex CLI
- Reads repository-level `AGENTS.md` instructions (project-scoped)
- Can read/write local AIKB files when working in a repo with AIKB access
- Supports MCP tools when configured in the runtime
- Best for repository-specific coding workflows where instructions should travel with the project

### OpenCode
- Terminal TUI with multi-provider support (Anthropic, OpenAI, Google, local Ollama, and any OpenAI-compatible endpoint)
- Does **not** auto-discover a global instruction file — requires explicit `instructions` array in `~/.config/opencode/opencode.json`
- Supports MCP servers configured in `opencode.json` under the `mcp` key
- Multiple agent modes: `build` (default), `plan`, `general`, `explore` — AIKB context applies to all modes
- No native Stop hook; use the shared `aikb-session-stop.sh` wrapper or run it manually
- Project-level `opencode.json` overrides the global config — AIKB instructions may not load inside projects that have their own config unless explicitly included
- `github-aikb` MCP requires `GITHUB_TOKEN` in the `env` block; missing token silently fails

### Cursor
- Reads User Rules from settings — paste `_agents/cursor.md` there
- Can read local AIKB files via filesystem; cannot push commits without terminal access
- Best for code-focused sessions where you're already in the IDE

### ChatGPT, Gemini (web), Grok
- UI-configured only; no filesystem or MCP access
- Session workflow: paste `_index.md` (or relevant sections) at session start
- At session end: ask for AIKB update suggestions, paste them manually into files
- These tools cannot maintain AIKB independently — human-in-the-loop required

### GitHub Copilot CLI
- Reads `~/.copilot/copilot-instructions.md` automatically at startup
- Also reads `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `.github/copilot-instructions.md` when present in a git repo
- Supports MCP servers — can read/write AIKB via `github-aikb` MCP (configured in `~/.copilot/mcp-config.json`)
- No native Stop hook; run `aikb-session-stop.sh` manually before finishing
- Use `/compact` to reduce context; capture to AIKB first with `runtime_cli.py capture`

---

## Multi-agent Coordination

When multiple agents are active on the same AIKB:
1. Check `active.md` — if another agent is listed with a recent timestamp, pull before writing
2. Write in small, focused commits to minimize merge conflicts
3. Each agent writes only to files relevant to its current task
