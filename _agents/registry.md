# AI Tool Registry

**Purpose:** Capabilities and gotchas for each AI tool in use. Read this when working in a multi-agent setup to understand what each tool can and cannot do.

---

## Tool Comparison

| Tool | AIKB Access | Can Write | MCP Support | Context Limit | Best For |
|------|-------------|-----------|-------------|---------------|----------|
| Claude Code | Local clone or MCP | Yes | Yes | Large | Terminal/code tasks, long sessions |
| Gemini CLI | Local clone or MCP | Yes | Yes | Large | Terminal/code tasks |
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

### Cursor
- Reads User Rules from settings — paste `_agents/cursor.md` there
- Can read local AIKB files via filesystem; cannot push commits without terminal access
- Best for code-focused sessions where you're already in the IDE

### ChatGPT, Gemini (web), Grok
- UI-configured only; no filesystem or MCP access
- Session workflow: paste `_index.md` (or relevant sections) at session start
- At session end: ask for AIKB update suggestions, paste them manually into files
- These tools cannot maintain AIKB independently — human-in-the-loop required

---

## Multi-agent Coordination

When multiple agents are active on the same AIKB:
1. Check `active.md` — if another agent is listed with a recent timestamp, pull before writing
2. Write in small, focused commits to minimize merge conflicts
3. Each agent writes only to files relevant to its current task
