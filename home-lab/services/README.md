---
context: personal-homelab
---
# Services

**Last Updated:** 2026-04-23
**Summary:** Self-hosted applications running on the home lab. All services are containerized (Docker via Dockge on TrueNAS) and fronted by Nginx Proxy Manager with wildcard SSL.

---

## Files

| File | Service | URL | Status |
|------|---------|-----|--------|
| [`vaultwarden.md`](vaultwarden.md) | Vaultwarden (Bitwarden) | vault.home.timmcg.net | ✅ Active |
| [`turing.md`](turing.md) | Turing AI Hub VM (chat-wrapper, ttyd, code-server) | ai / chat / terminal / code.home.timmcg.net | ✅ Active |
| [`aikb-memory-core.md`](aikb-memory-core.md) | AIKB Memory Core runtime extension | memory.home.timmcg.net / :8077 | 🟢 Active |
| [`telegram-ideas-bot.md`](telegram-ideas-bot.md) | Telegram Ideas Bot | Telegram / ideas inbox | 🟢 Active |

---

## Adding a New Service

See [`new-service-checklist.md`](new-service-checklist.md) — covers DNS, NPM, SSL, Vaultwarden, Ansible, Homepage, Authentik, monitoring, and AIKB docs.
