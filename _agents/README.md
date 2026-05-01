# Agent Instruction Files
**Last Updated:** 2026-05-01

These files are the *bridges* between AIKB and different AI tools. They tell each tool:

- where your AIKB lives
- how to read it efficiently
- how to write back updates
- what conventions to follow at session start and end

## Primary AIKB lane

AIKB is primarily designed for agentic tools that can:
- load persistent instruction files
- read and search the AIKB repo
- participate in session lifecycle workflows
- run hooks or supporting automation

Examples:
- Claude Code
- Gemini CLI
- Codex CLI
- GitHub Copilot
- OpenCode
- Cursor

These tools can use AIKB the way it is intended: as a shared, durable, cross-session memory layer.

## Future-agent lane

If you add a new agent later — for example Goose, Hermes, or OpenClaw — point it at the AIKB repo and have it configure itself appropriately. The docs and existing agent instruction files are meant to be readable enough that a capable agent can determine:

- which instruction file format it should mirror
- how AIKB wake-up and closeout work
- where search and runtime tools live
- how to participate in the lifecycle without special handholding

## Search Before Asking
A core AIKB behavior for all agents:

- search AIKB before asking the operator to repeat context
- use `aikb_search`, `_index.md`, `_state.yaml`, and relevant domain files first
- ask the operator only when information is missing, stale, or ambiguous

Without this rule, the agent feels unaware of the memory system it already has.

## When to update these files
Update agent instruction files when:

- your local path changes
- you rename the repo
- you adopt new AIKB lifecycle conventions
- a tool gains better support for hooks, MCP, or local file access
- the public template improves its shared guidance

Use `./sync-agents.sh` to propagate updated instruction files into project repos or supported global locations.

## Key difference: file-based vs UI-based integration
Some tools support file-backed instructions directly. Others expect instructions to be pasted into a settings UI.

### File-based
Examples:
- Claude Code
- Gemini CLI
- Codex CLI
- GitHub Copilot

These are the best fit for AIKB because the instruction files can evolve with the repo and be updated through sync workflows.

### UI-based
Examples:
- Cursor user rules
- OpenCode configuration surfaces that point to local instruction content

These can still work well, but they may require more manual setup.

## Goal
The goal is not to support every possible chatbot equally. The goal is to make AIKB excellent for agentic developer tools that can actually participate in shared memory, retrieval, and session lifecycle.
