---
context: personal-homelab
tags: [ansible, playbooks, automation, truenas, pi-hole, backups, opensoak, nightly-update, midclt, dockge, containers, pihole-sync, turing, chat-wrapper, ai]
hosts: [truenas, pihole, pihole2, opensoak, turing]
last_updated: 2026-03-03
---

# Automation Playbook Catalog
**Last Updated:** 2026-03-03
**Summary:** Catalog of Ansible playbooks, schedules, and usage notes for home-lab and AI infrastructure automation.

## Repository: [ansible](https://github.com/mcglothi/ansible)

| Playbook | Target | Schedule | Description |
| :--- | :--- | :--- | :--- |
| `nightly_update.yml` | TrueNAS | 2:00 AM | Updates Dockge stacks (sequential pull+up, skip semaphore) AND upgrades all TrueNAS native apps via midclt. |
| `pihole_update.yml` | TrueNAS + Infrastructure | 3:00 AM | Updates gravity on both Pi-holes; syncs local DNS hosts from primary to secondary. |
| `backup_configs.yml` | TrueNAS | 4:00 AM | Backs up NPM, Semaphore, and Vaultwarden DBs to Data pool. |
| `opensoak_update.yml` | OpenSoak (Pi) | Sun 3:00 AM | Pulls code, updates venv/npm, restarts services. |
| `bootstrap_svc_account.yml` | Home | Manual | Deploys the `svc_ansible` user to new hosts. |
| `ai/deploy_chat_wrapper.yml` | turing | Manual | Deploys AI Hub (chat-wrapper) as a systemd service on port 3000 with terminal proxy support. |
| `ai/update_pihole_dns.yml` | TrueNAS + pihole2 | Manual | Adds/maintains turing AI DNS entries on both Pi-holes (ai.home primary, chat.home alias). |
| `ai/configure_npm_proxy.yml` | localhost (NPM API) | Manual | Creates NPM proxy hosts for turing AI services (ai.home -> turing:3000 plus terminal/code/chat). |

## Notes

### ai/configure_npm_proxy.yml
- Playbook now behaves as an upsert, not just create-only.
- Existing proxy hosts are updated to match declared targets/ports (important for cutovers like `ai.home` from `:8080` to `:3000`).
- Requires `vault_npm_user` and `vault_npm_password` in execution context (Semaphore env vars or explicit `-e`).

### nightly_update.yml
- **Play 1 (truenas):** Finds all stacks under `/mnt/.ix-apps/app_mounts/dockge/stacks`, runs `docker compose pull && up -d` sequentially (NOT async — TrueNAS SCALE SSH blocks exec() needed for Ansible async, returns ENOSYS/rc=38).
- Semaphore stack is explicitly SKIPPED — updating it would restart Semaphore mid-playbook, killing the run.
- The `nginx` directory has a bogus docker-compose.yml (contains a `docker run` command, not YAML) — ignore_errors handles it.
- **Play 2 (truenas):** Queries `midclt call app.query` for apps with `upgrade_available=true`, upgrades each via `midclt call app.upgrade`, polls for RUNNING state (6min timeout per app).
- **Semaphore issue:** `SEMAPHORE_ACCESS_KEY_ENCRYPTION` must be set to a fixed value in docker-compose.yml, otherwise Semaphore regenerates a random key on each restart, breaking stored credentials. Fixed key: see compose file on truenas at `/mnt/.ix-apps/app_mounts/dockge/stacks/semaphore/docker-compose.yml`.

### pihole_update.yml
- **Play 1 (truenas):** Runs `docker exec ix-pihole-pihole-1 pihole -g` to update primary gravity. Extracts `hosts` array from `/mnt/.ix-apps/app_mounts/pihole/config/pihole.toml` and registers as a fact.
- **Play 2 (infrastructure):** Runs `pihole -g` and `pihole -up` on secondary (Raspberry Pi). Syncs hosts from primary into `/etc/pihole/pihole.toml` via Python regex replace, then `pihole reloaddns`.
- Both Pi-holes use v6 `pihole.toml` format (not custom.list).
