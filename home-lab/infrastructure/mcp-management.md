---
context: personal-homelab
tags: [mcp, infrastructure, home-lab, architecture, automation, mcp-hub, custom-built]
last_updated: 2026-04-28
---

# Centralized MCP Management (Command Center)

**Summary:** We have migrated from individual agent-based MCP configurations to a centralized **MCP Command Center**. This provides a unified dashboard and an API gateway for all AI agents (Claude, Codex, Hermes, Gemini) to interact with the homelab environment via a polished, production-grade service.

> **This is a fully custom/self-built project.** There is no upstream open-source repo for the Command Center itself. Do not look for external documentation — this AIKB file is the source of truth. It uses the Anthropic MCP standard protocol but the hub, dashboard, registry, and SSE proxy are all internal builds.

## Architecture
- **Host:** Babbage (TrueNAS SCALE)
- **Deployment:** Docker Compose (`/mnt/Containers/MCPHub/compose.yaml`)
- **Components:**
    - **Frontend:** `mcp-dashboard` (Nginx) serving a custom visual registry.
    - **Backend:** `mcp-hub` (Node.js) multiplexing tools into a single SSE stream.
- **Identity:** SSL via wildcard cert; DNS via primary and secondary Pi-holes.
- **Security:** 
    - **UI (`/`):** Secured via Authentik Forward Auth (Home Lab Global).
    - **API (`/mcp`):** Configured with Authentik Path-Bypass for programmatic agent access.
- **Configuration:** 
    - **Servers:** `/mnt/Containers/MCPHub/mcp.json5` on Babbage.
    - **Registry Data:** `AIKB/home-lab/infrastructure/homelab-registry.json`.

## Endpoints
- **Web UI:** `https://mcp.home.timmcg.net`
- **Agent API:** `https://mcp.home.timmcg.net/mcp`

## Managed MCP Servers

### Core Tools
- **excalidraw:** Collaborative whiteboard management.
- **chrome-devtools:** Browser interaction and inspection.
- **playwright:** Automated web browser control.
- **fetch:** Web content extraction.
- **multicli:** Orchestration of multiple AI model families.

### AIKB & Infrastructure
- **github-aikb:** Version control and file management for AIKB.
- **docker:** Container lifecycle management on Babbage.
- **pihole:** DNS management and network monitoring.
- **home-assistant:** control of IoT devices and sensors.

## Living Lab Pipeline (DaC)
The Command Center features a **Live Architecture Blueprint**.
- **Source of Truth:** `AIKB/home-lab/infrastructure/living-atlas.yaml`
- **Compiler:** `AIKB/_tools/atlas-sync.py` (Reads YAML, generates separate hardware and logical D2 views, renders via D2 CLI with `--sketch` theme, and emits curated `.excalidraw` scenes for presentation).
- **Outputs:**
  - `homelab-architecture.svg` — hardware/deployment overview (kept as the legacy dashboard path)
  - `homelab-logical.svg` — logical service and tool-flow view
- **Local artifacts:** `home-lab/infrastructure/homelab-hardware.d2`, `home-lab/infrastructure/homelab-logical.d2`, `home-lab/infrastructure/homelab-hardware.excalidraw`, `home-lab/infrastructure/homelab-logical.excalidraw`
- **Publishing:** Pushed automatically to the MCP Command Center Dashboard via `scp`. Agents run this sync script to refresh both views whenever they change the homelab layout.
- **Coverage:** The atlas now includes the core network, TrueNAS, Turing, Hopper, both main workstations, secondary Pi-hole, OpenSoak, and embedded CEC controller surfaces.
- **Relationship to Excalidraw:** Use the generated D2/SVG blueprints for continuously updated ops documentation; use the generated `.excalidraw` scenes (opened in `draw.home.timmcg.net`) for presentation-friendly architecture boards and light hand-polish.

## Agent Sync Status

| Agent | Config Path | Status |
|-------|-------------|--------|
| Claude | `~/.claude/settings.json` | ✅ Synced (Prod) |
| Codex | `~/.codex/config.toml` | ✅ Synced (Prod) |
| Hermes | `~/.hermes/config.yaml` | ✅ Synced (Prod) — stdio proxy (same as Codex) |
| Gemini | `~/.gemini/settings.json` | ✅ Synced (Prod) |

## Dashboard Integration
- **AI Hub:** Native "Orchestrator" view added to Operator Console with live status pill and embedded Command Center.
- **Homepage:** Listed under the "AI" section for easy discovery.

## Operational Runbooks

### Adding a New Tool
1. Edit `/mnt/Containers/MCPHub/mcp.json5` on Babbage.
2. Update the visual registry at `AIKB/home-lab/infrastructure/homelab-registry.json` and sync it to `/mnt/Containers/MCPHub/www/index.html` (if applicable).
3. The Hub will hot-reload; all agents will see the new tool instantly.

### Troubleshooting
- **Check Logs:** `docker logs mcp-hub` or `docker logs mcp-dashboard`.
- **Verify Resolution:** `nslookup mcp.home.timmcg.net` should return `10.10.10.10`.
- **Verify API:** `curl https://mcp.home.timmcg.net/mcp` should return an SSE stream.

#### Hermes / Codex: `homelab` MCP fails (`Cannot POST /mcp` / `Session terminated`)

**Symptom (Codex CLI startup):**
- `MCP client for homelab failed to start ... Unexpected content type ... Cannot POST /mcp`

**Symptom (Hermes CLI startup):**
- `MCP server 'homelab' failed initial connection after 3 attempts` / `Session terminated`

**Root cause:**
- The homelab Command Center endpoint at `https://mcp.home.timmcg.net/mcp` is an **SSE transport** MCP endpoint (HTTP `GET` returns `text/event-stream` and provides a per-session `/messages?...` POST endpoint).
- Codex currently treats `url = ...` MCP servers as **streamable HTTP** and attempts to `POST /mcp` for initialization, which the SSE endpoint does not support.

**Fix (local stdio proxy — shared by Codex and Hermes):**
1. Add a local proxy script at `~/.codex/mcp/homelab-sse-stdio-proxy.mjs` that:
   - `GET`s the SSE stream, reads the emitted `event: endpoint` path
   - `POST`s JSON-RPC messages to that endpoint
   - forwards MCP JSON-RPC between stdin/stdout and the remote hub
2. Configure each agent to use the proxy via stdio instead of `url`:
   - **Codex** (`~/.codex/config.toml`):
     ```toml
     [mcp_servers.homelab]
     command = "node"
     args = ["~/.codex/mcp/homelab-sse-stdio-proxy.mjs", "--url", "https://mcp.home.timmcg.net/mcp"]
     ```
   - **Hermes** (`~/.hermes/config.yaml`):
     ```yaml
     mcp_servers:
       homelab:
         command: node
         args:
           - /Users/mcglothi/.codex/mcp/homelab-sse-stdio-proxy.mjs
           - --url
           - https://mcp.home.timmcg.net/mcp
     ```

**Verification:**
- `curl -sS -D - -o /dev/null https://mcp.home.timmcg.net/mcp` should include `content-type: text/event-stream`.
- Proxy smoketest (expects `initialize` response JSON):
  - `printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}' | node ~/.codex/mcp/homelab-sse-stdio-proxy.mjs --url https://mcp.home.timmcg.net/mcp`

---

## Pending Development Tasks

| Task | Notes |
|------|-------|
| Make tool cards dynamic | Currently static HTML. Goal: query the `mcp-hub` API at runtime to render the registry live, so adding a tool to `mcp.json5` auto-updates the dashboard without editing `index.html`. |
| Move diagram off dashboard | The homelab diagram currently lives on the MCP dashboard. Should be relocated to a dedicated documentation page. See **Documentation & Diagrams** section below. |

---

## Documentation & Diagrams

The homelab architecture diagram is currently served as part of the MCP dashboard (`mcp.home.timmcg.net`). This couples infra docs to the MCP service and makes them harder to find/update independently.

### Recommendation: Move diagrams to a dedicated docs site

**Preferred stack: [MkDocs + Material theme](https://squidfunk.github.io/mkdocs-material/)**
- Markdown files in a git repo (fits existing AIKB workflow)
- Built-in [Mermaid](https://mermaid.js.org/) support for diagram-as-code
- Self-hosted static site, Authentik-protectable via NPM forward auth
- Dark mode, search, versioning — low operational overhead

**Diagram format: Mermaid or D2**
- The Living Lab Pipeline already generates D2 and SVG artifacts — these can be embedded in MkDocs pages directly
- Mermaid is a good choice for simpler topology/flow diagrams that change with the lab

**Alternative considered: Netbox**
- Best-in-class for IPAM + inventory + topology, but heavier (Postgres + Redis)
- Worth revisiting if IPAM tracking becomes a pain point

**What to migrate:**
- Homelab architecture diagram (hardware + logical SVGs from `atlas-sync.py`)
- Any other diagrams currently embedded in the MCP dashboard UI
