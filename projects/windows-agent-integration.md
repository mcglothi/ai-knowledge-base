# Windows Agent Integration

**Last Updated:** 2026-04-16
**Summary:** Improvement project to make AIKB usable from Windows-based AI apps, starting with Claude Desktop and a remote MCP architecture that can also support ChatGPT.

---

## Overview

This project captures the work needed to make AIKB available inside Windows AI applications instead of assuming a terminal-first macOS/Linux workflow.

The current best path is to treat this as a cross-client integration effort rather than a one-off Windows install guide. Claude Desktop on Windows is the lowest-friction target today. ChatGPT support likely depends on a remote MCP or app deployment. Microsoft Copilot Studio appears to require a separate connector or API integration rather than a drop-in MCP setup.

**Primary goal:** Make AIKB accessible in mainstream Windows AI surfaces without requiring the Codex CLI.
**Initial focus:** Claude Desktop for Windows, then shared remote MCP infrastructure.
**Secondary targets:** ChatGPT Windows app, Microsoft Copilot Studio, and future Gemini desktop support if Google ships a Windows app.

---

## Current State

- ✅ Research completed on current desktop app support as of 2026-04-16
- ✅ Claude Desktop for Windows confirmed as the easiest current target
- ✅ ChatGPT Windows app confirmed, with custom MCP/app workflows centered on remote integrations
- ✅ Copilot Studio identified as a separate integration path, not a direct Claude/OpenAI-style local MCP client
- ⚠️ No shared AIKB remote MCP service exists yet
- ⚠️ No Windows packaging or onboarding flow exists for Claude Desktop extensions
- ⚠️ Gemini has an official macOS app, but no official Windows Gemini desktop app was confirmed during this research pass

---

## Platform Notes

### Claude Desktop (Windows)

- Strongest near-term fit for AIKB on Windows
- Supports local MCP / desktop extensions on Windows
- Also supports remote MCP connectors
- Best candidate for an initial AIKB desktop integration

### ChatGPT (Windows)

- Windows desktop app exists
- Current custom app / MCP workflow is remote-first rather than local desktop-extension-first
- Best served by a shared remote AIKB MCP service rather than per-machine local wiring

### Microsoft Copilot Studio

- Best thought of as a separate product integration
- Supports agents, connectors, APIs, and Windows computer-use automation
- Likely requires exposing AIKB through an API, connector, or knowledge source rather than directly reusing Claude-style local MCP setup

### Google Gemini

- Official native Gemini desktop app exists for macOS
- No official Windows Gemini desktop app was confirmed as of 2026-04-16
- Windows support may arrive later through a native app or continued Chrome-based integration

---

## Proposed Roadmap

1. Define the minimum useful AIKB tool surface for external clients
2. Build AIKB as a remote MCP service with read-focused tools first
3. Add Claude Desktop Windows support via local extension or MCP bundle where local machine access is needed
4. Connect the remote AIKB service to ChatGPT through developer mode / custom app flows
5. Evaluate whether Copilot Studio should use the same backend through an API wrapper or a separate connector layer

---

## Open Questions

- Which AIKB capabilities should be exposed externally first: search, fetch, recent sessions, project index, or write-back tools?
- Should write/update actions be excluded from the first remote MCP release for safety?
- Should Claude Desktop get a local-only extension for private machine context in addition to the shared remote MCP service?
- Is Copilot Studio important enough to justify a first-class connector, or should it wait until the remote MCP/API layer is stable?
- If Google releases a Windows Gemini desktop app, can the same remote MCP/API backend be reused there?

---

## Outstanding Tasks

- [ ] Define AIKB external tool contract for desktop clients
- [ ] Decide which capabilities are safe for remote read-only exposure
- [ ] Prototype a remote AIKB MCP server
- [ ] Prototype Claude Desktop Windows installation flow
- [ ] Validate ChatGPT compatibility against the remote MCP prototype
- [ ] Decide whether Copilot Studio should be in scope for phase 1 or later

---

## References

- Claude Desktop install and extension docs
- Claude local MCP / desktop extension docs
- Claude remote MCP connector docs
- ChatGPT Windows desktop app docs
- OpenAI developer mode / MCP app docs
- Microsoft Copilot Studio overview and computer-use docs
- Google Gemini macOS desktop app announcement
