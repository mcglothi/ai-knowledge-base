---
tags: [chatops, telegram, home-assistant, on-the-go, mobile, wear-os, pixel-fold, pixel-watch, ai-agents, automation]
status: in progress
last_updated: 2026-04-23
---

# ChatOps On-The-Go
**Last Updated:** 2026-04-23
**Summary:** Mobile/wearable ChatOps interface to interact with home-lab AI agents (Codex, Claude Code, Gemini CLI) and the AIKB memory pipeline while away from the workstation.

---

## Vision
Enable seamless interaction with the AI assistant ecosystem from a Pixel 10 Pro Fold and Pixel Watch 4. This bridge allows for status checks, note-taking (ideas/todos), and simple task execution via voice (Watch) or text (Phone) without needing a terminal.

## Core Use Cases
- **Voice-to-Note (Watch):** Quickly dictate an idea or todo that is immediately ingested into the AIKB `ideas/inbox/` pipeline.
- **Status Queries (Watch/Phone):** Ask "Gemini: what is the status of the backup job?" or "Claude: summarize today's progress."
- **Task Execution (Phone):** Trigger predefined Ansible playbooks or simple shell commands via a chat interface.
- **Proactive Alerts:** Receive notifications from home-lab monitoring (Prometheus/Grafana) or agent-triggered events directly in the chat.

For the concrete watch memo build, see [`pixel-watch-voice-memo.md`](pixel-watch-voice-memo.md).

## Proposed Architectures

### Option A: Telegram Bot (Recommended)
- **Interface:** Native Telegram app on Android (Fold) and Wear OS (Watch).
- **Backend:** Private long-poll bot in `_tools/memory-pipeline/telegram_ideas_bot.py`, deployed on TrueNAS as a Dockge stack.
- **Security:** Bot can auto-enroll the first private chat or lock to an allowlist via Telegram user IDs.
- **Routing:** Plain text and `/note ...` both call `runtime_cli.py idea add`.
- **Pros:** Excellent Wear OS app with voice-to-text, minimal setup, and a direct path into AIKB.

### Option B: Home Assistant Assist
- **Interface:** Home Assistant Companion App (Android/Wear OS).
- **Backend:** Custom HA intents + Shell Command integrations.
- **Routing:** HA `assist` pipeline routes voice/text to scripts that SSH into the target workstation to run CLI agents.
- **Pros:** Unified with existing smart home infrastructure, local-first (if using Nabu Casa or Cloudflare Tunnel).

## Implementation Plan (Telegram Bot)

### 1. Backend Setup
- Create a new Telegram bot via `@BotFather`.
- Store the `TELEGRAM_BOT_TOKEN` in Vaultwarden (`PAT/Telegram/ChatOpsBot`).
- Deploy the bot on TrueNAS using the Dockge stack in `home-lab/services/telegram-ideas-bot.md`.
- Keep Telegram Desktop on Newton as the local client/admin fallback.

### 2. Integration Logic
- **Note Ingestion:** Use `subprocess` to call `python3 AIKB/_tools/memory-pipeline/runtime_cli.py idea add`.
- **Agent Execution:** Keep that as a later phase once note capture is stable.
- **Vaultwarden Access:** Not required for note capture. Add only if we later expand the bot to orchestrate other agents.

### 3. Wear OS Optimization
- Configure the Telegram Wear OS app for quick access (complications or tiles).
- Test voice-to-text dictation for note-taking.

## Next Actions
- [x] Create Telegram Bot and save credentials to Vaultwarden.
- [x] Prototype a simple Python script to handle note capture.
- [x] Route note capture into `python3 AIKB/_tools/memory-pipeline/runtime_cli.py idea add`.
- [ ] Deploy the Telegram ideas bot on TrueNAS Dockge.
- [ ] Test the prototype from the Pixel Watch 4 using voice dictation.
- [ ] Tighten user filtering with an allowlist once the Telegram user id is known.
