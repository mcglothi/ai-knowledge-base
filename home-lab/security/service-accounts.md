---
context: personal-homelab
tags: [svc_ansible, svc_gemini, svc_claude, svc_codex, service-accounts, ssh-keys, sudo, authentik, agents, semaphore, permissions, api-tokens]
hosts: [truenas, babbage, farnsworth, pihole, pihole2, opensoak, hopper]
last_updated: 2026-04-09
---

# Service Account Registry
**Last Updated:** 2026-04-28 (rev 6)
**Summary:** Master inventory of all non-human identities used in the home lab and for AI agents.

## Core Agents

| Identity | Purpose | Status | VW Path | Scope |
|----------|---------|--------|---------|-------|
| `svc_ansible` | Automation | 🟢 Active | `PAT/SSH/svc_ansible` | Full Sudo (Homelab) |
| `svc_gemini` | Gemini CLI | 🟢 Active | `PAT/Authentik/svc_gemini` | Superuser (Authentik) |
| `svc_claude` | Claude Code | 🟢 Active | `PAT/Authentik/svc_claude` | Superuser (Authentik) |
| `svc_codex` | Codex CLI | 🟢 Active | `PAT/Authentik/svc_codex` | Superuser (Authentik) |
| `svc_hermes` | Hermes CLI | 🟡 Partial | `PAT/SSH/svc_hermes` | Homelab SSH + sudo |
| `svc_goose` | Goose Agent | 🟡 Partial | `PAT/SSH/svc_goose` | Homelab SSH + sudo |

---

## 🔐 Credentials Checklist

Use the naming convention `PAT/<Service>/<Identity>` in the **API Keys** folder.

### 1. SSH Access
Dedicated SSH keys for agents to manage OS-level tasks.

| Host Group | Identity | Status | VW Path | Detail |
|------------|----------|--------|---------|--------|
| Homelab (Global) | `svc_gemini` | ✅ Active | `PAT/SSH/svc_gemini` | ed25519 key |
| Homelab (Global) | `svc_claude` | ✅ Active | `PAT/SSH/svc_claude` | ed25519 key |
| Homelab (Global) | `svc_codex` | ✅ Active | `PAT/SSH/svc_codex` | ed25519 key |
| Homelab (Global) | `svc_hermes` | 🟢 Provisioned | `PAT/SSH/svc_hermes` | ed25519 key (Added 2026-04-28) |
| Homelab (Global) | `svc_goose` | 🟢 Provisioned | `PAT/SSH/svc_goose` | ed25519 key (Added 2026-04-28) |

### 2. Infrastructure & Services
API access for service management.

| Service | `svc_gemini` | `svc_claude` | `svc_codex` | `svc_hermes` | `svc_goose` |
|---------|--------------|--------------|-------------|--------------|-------------|
| **Authentik** | ✅ Admin | ✅ Admin | ✅ Admin | ✅ Admin | ✅ Admin |
| **TrueNAS** | ✅ API | ✅ API | 🟡 Pending | 🟡 Pending | 🟡 Pending |
| **Semaphore** | ✅ User | ✅ User | 🟡 Pending | 🟡 Pending | 🟡 Pending |
| **Grafana** | ✅ Admin | ✅ Admin | 🟡 Pending | 🟡 Pending | 🟡 Pending |
| **GCP / Firebase** | ✅ SA | ✅ SA | 🟡 Pending | 🟡 Pending | 🟡 Pending |
| **NPM Admin** | ✅ Login | ✅ Login | 🟡 Pending | 🟡 Pending | 🟡 Pending |

### 🌉 Unified Agent Header (Authentik Bypass)
All agents should use **Basic Authentication** to bypass Forward Auth on protected subdomains (e.g., `mcp.home.timmcg.net`, `ai.home.timmcg.net`).

- **Header:** `Authorization: Basic <base64(agent_username:authentik_token)>`
- **Requirement:** Authentik token must have `intent='app_password'`.
- **Proxy Support:** Use `homelab-sse-stdio-proxy.mjs --auth <base64>` for MCP SSE streams.

---

## 🛠️ User TODO List

These tasks require manual interaction via Web UIs and cannot be auto-provisioned safely by the agents.

- [x] **Pi-hole API access:** Both Pi-holes use the shared admin password in `PAT/Pi-hole/Primary` — verified working against both hosts (2026-02-23). Note: Stale `PAT/Pihole/Agent` and `PAT/Pihole2/Agent` items were deleted (2026-02-24).

---

## 🛠️ Provisioning Log

### 2026-04-09: Provisioned Hopper Service Accounts
- Configured `hopper` (10.10.10.200) with dedicated Unix users for AI agents.
- Created `svc_gemini`, `svc_claude`, and `svc_codex` users.
- Installed their respective SSH keys (verified from `tesla`).
- Granted passwordless sudo to each (`/etc/sudoers.d/svc_...`).
- Updated `svc_ansible` authorized_keys to include all agent keys (`svc_gemini`, `svc_claude`, `svc_codex`) plus the `turing-aikb-sync` key.
- Validated all agent identities can SSH into both their dedicated users and the `svc_ansible` user on `hopper`.

### 2026-03-10: `svc_gemini` SSH drift found on TrueNAS
- Direct test from `tesla`: `ssh -i ~/.ssh/svc_gemini svc_gemini@10.10.10.10 true` returned `Permission denied (publickey,password)`.
- Verified via Ansible on TrueNAS: only `svc_ansible` and `svc_codex` Unix users currently exist; `svc_gemini` is missing entirely.
- Checked all home-directory `authorized_keys` files on TrueNAS: local `svc_gemini` key fingerprint `SHA256:kXdiJQMsGWa6NviU6hNGgokqHolphA+9ZREt6UOcqWg` was not present.
- Vaultwarden item `PAT/SSH/svc_gemini` was then verified live and matched the local key exactly.
- Remediated by creating Unix user `svc_gemini` (UID 3005, GID 3004), installing the matching public key, and granting passwordless sudo to mirror the existing service-account pattern on TrueNAS.
- Validation succeeded: direct SSH login with `~/.ssh/svc_gemini` worked and `sudo -n true` passed on TrueNAS.

### 2026-03-02: Added `svc_codex`
- Created and stored `PAT/SSH/svc_codex` in Vaultwarden.
- Deployed user + SSH key + passwordless sudo on `babbage`, `pihole2`, and `opensoak`.
- Note: Primary Pi-hole is containerized on TrueNAS; SSH to Pi-hole IP lands on TrueNAS host context.

### 2026-02-23: Refactored Registry
- Shifted from "Strategy" to "Registry" format.
- Established `PAT/<Service>/<Identity>` naming convention.
- Provisioned SSH keys, GCP SAs, Semaphore tokens, NPM logins, and VW Admin token.
 logins, and VW Admin token.
