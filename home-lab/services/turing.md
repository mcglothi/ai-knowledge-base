---
context: personal-homelab
tags: [turing, ai-hub, ttyd, code-server, claude-code, gemini-cli, docker, dockge, kvm, vm, truenas, terminal, web-terminal, vscode, ansible, ai, local-llm, chat-wrapper, operator-console, mobile-chat, hermes, mcpo, openshell]
hosts: [turing, truenas]
last_updated: 2026-04-28
---

# Turing — AI Hub VM

**Last Updated:** 2026-04-27
**Summary:** Build and operations record for the Turing AI Hub VM and its hosted AI tooling surfaces.
**Host:** turing (KVM VM on babbage/TrueNAS SCALE)
**IP:** 10.10.10.50 (static)
**OS:** Debian 13 (Trixie)

---

## Overview

Dedicated VM for AI tooling, orchestration, and agent services. Following the Phase 2 migration, Turing is now the primary host for all agent-related UIs and bridges, allowing Hopper to remain inference-only.

---

## Services

| Service | URL | Direct | Port |
|---------|-----|--------|------|
| AI Hub (operator-console) | https://ai.home.timmcg.net | http://10.10.10.50:3001 | 3001 |
| Open WebUI (Hopper Backend) | https://chat.home.timmcg.net | http://10.10.10.50:3002 | 3002 |
| Hermes Dashboard | https://hermes.home.timmcg.net | http://10.10.10.50:9119 | 9119 |
| ttyd (web terminal) | https://terminal.home.timmcg.net | http://10.10.10.50:7681 | 7681 |
| code-server (VS Code) | https://code.home.timmcg.net | http://10.10.10.50:8080 | 8080 |
| AI Portal (static) | https://ai.home.timmcg.net (index) | http://10.10.10.50:8090 | 8090 |
| Ops Console | https://ops.home.timmcg.net | http://10.10.10.50:3001 | 3001 |
| OpenShell (Nemoclaw) | https://shell.home.timmcg.net | http://10.10.10.50:8085 | 8085 |
| MCPO Bridge (Memory) | — | http://10.10.10.50:8102 | 8102 |
| MCPO Bridge (GitHub) | — | http://10.10.10.50:8101 | 8101 |
| Dockge (turing stacks) | — | http://10.10.10.50:31015 | 31015 |

All public URLs proxied through NPM on babbage (10.10.10.10).

---

## Architecture (Post-Phase 2)

```
Phone / Browser
      ↓ HTTPS
NPM (babbage:10.10.10.10)
      ↓ HTTP (internal)
turing (10.10.10.50)
  ├── open-webui  :3002  — Main chat UI (Backend: Hopper:8012)
  ├── hermes      :9119  — Hermes Agent Dashboard + Gateway
  ├── mcpo-bridges :8101 — GitHub and Memory MCP bridges
  ├── openshell   :8085  — Nemoclaw execution cluster
  ├── ttyd        :7681  — bash with claude + gemini CLIs
  ├── code-server :8080  — VS Code + Claude Code extension
  ├── operator-console :3001 — AI Hub main site / Ops Console
  └── Dockge       :31015 — manages Docker stacks
```

---

## Container Data

All persistent data on turing at `/opt/containers/`:
```
/opt/containers/
├── dockge/
├── open-webui/      # Chat history, users, tools
├── hermes/data/     # Hermes memories, config, sessions
├── mcpo-bridges/    # Bridge scripts and envs
├── openshell/       # Sandbox cluster data
├── ai-portal/       # Static portal files
├── ttyd/
└── code-server/
```

---

## Deployment History

- **2026-04-27:** **Phase 2 Migration Complete.** 
  - Migrated Hermes Agent and MCPO bridges from Hopper.
  - Deployed Open WebUI, OpenShell, and Ops Console.
  - Added unified AI Portal for service navigation.
- **2026-04-28:** **ttyd custom frontend deployed.**
  - Replaced stock ttyd UI with a custom `index.html` at `/opt/containers/ttyd-index.html` (mounted into container).
  - Added floating settings panel: font family, font size, line height, cursor style, 8 color themes (Zinc/Dracula/Nord/One Dark/Gruvbox/Monokai/Sol Dark/Light). All settings persist to `localStorage`.
  - Updated compose command: `ttyd --base-path / -W -I /opt/containers/ttyd-index.html bash`
  - Uses xterm.js 5.3.0 + fit/web-links addons from CDN. Implements ttyd WebSocket protocol directly.
- **2026-03-03:** Initial VM bring-up and ttyd/code-server deployment.
