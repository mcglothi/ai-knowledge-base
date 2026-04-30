---
context: personal-homelab
tags: [telegram, ideas, inbox, truenas, dockge, chatops, mobile, launchd-fallback]
hosts: [babbage]
last_updated: 2026-04-23
---

# Telegram Ideas Bot
**Last Updated:** 2026-04-23
**Summary:** Private Telegram capture bot for AIKB. Runs on TrueNAS as a Dockge stack so notes can be captured even when Newton is asleep or traveling.

## Status

🟢 ACTIVE - runtime target is TrueNAS (`babbage`). Newton keeps only the Telegram client and optional admin fallback.

## Purpose

Keep the quick-note path boring:

- Telegram message arrives
- bot writes the note into `ideas/inbox/YYYY-MM-DD/`
- AIKB stays the long-term store
- future: the same service can expose a tiny watch-memo relay endpoint for Pixel Watch capture

## Architecture

- **Client:** Telegram on phone and optionally on Newton
- **Runtime:** Docker container on TrueNAS Dockge
- **Storage:** AIKB repo checkout mounted read/write so `runtime_cli.py idea add` can write directly into the inbox
- **State:** Small bot state file on the service volume

## Compose Stack

Use this on TrueNAS/Dockge:

```yaml
services:
  telegram-ideas-bot:
    image: python:3.13-slim
    container_name: telegram-ideas-bot
    restart: unless-stopped
    init: true
    working_dir: /aikb
    command: ["python3", "_tools/memory-pipeline/telegram_ideas_bot.py"]
    env_file:
      - /mnt/Containers/telegram-ideas-bot/env
    environment:
      AIKB_ROOT: /aikb
      AIKB_TELEGRAM_STATE_DIR: /data/state
      TELEGRAM_NOTE_TAG: telegram
      TELEGRAM_POLL_TIMEOUT: "30"
    volumes:
      - /mnt/VMs/mcglothi/Code/AIKB:/aikb
      - /mnt/Containers/telegram-ideas-bot:/data
```

Recommended host paths:

- AIKB checkout: `/mnt/VMs/mcglothi/Code/AIKB`
- Service data: `/mnt/Containers/telegram-ideas-bot`

## Environment File

Create `/mnt/Containers/telegram-ideas-bot/env` on TrueNAS:

```bash
TELEGRAM_BOT_TOKEN=123456:ABCDEF...
TELEGRAM_ALLOWED_USER_IDS=5852558550
TELEGRAM_NOTE_TAG=telegram
TELEGRAM_POLL_TIMEOUT=30
```

## Setup Flow

1. Create the bot with `@BotFather`.
2. Put the token into the TrueNAS env file.
3. Start the Dockge stack.
4. Send `/whoami` once to confirm the allowlist user id.
5. Send plain text messages or `/note ...` to capture ideas.

## Fallback

The Newton launchd path still exists for testing, but it is no longer the primary runtime.
