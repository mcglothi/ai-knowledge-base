---
context: personal-homelab
tags: [ansible, semaphore, automation, truenas, svc_ansible, scheduled-tasks, github, backups, nightly, pihole, dockge, containers]
hosts: [truenas]
services: [ansible-semaphore]
last_updated: 2026-03-07
---

# Ansible Semaphore

**Last Updated:** 2026-03-07
**Summary:** Ansible Semaphore UI at ansible.home.timmcg.net manages automation for 14 home lab devices. Runs 4 scheduled playbooks nightly/weekly. Backed by GitHub repo `mcglothi/ansible`.

---

## Instance Info
- **URL:** https://ansible.home.timmcg.net
- **Project:** Home Infrastructure (ID 3)
- **Inventory:** Home Network (14 devices)
- **Service Account:** `svc_ansible` (Deployed to core infra with passwordless sudo)

## Repository
- **URL:** https://github.com/mcglothi/ansible.git
- **Auth:** GitHub PAT stored in Semaphore Key Store.
- **API Verification (2026-03-07):** Semaphore API returned Project `1` (`Home Infrastructure`) and Repository `1` (`GitHub Ansible`) successfully, which confirms backend connectivity even when the UI appears stale or incomplete.

## Scheduled Tasks
1. **Nightly Container Update:** 2:00 AM (pulls/recreates all Dockge stacks)
2. **Pi-hole Update:** 3:00 AM (gravity -g and core updates)
3. **Config Backup:** 4:00 AM (Backs up NPM, Semaphore, and Vaultwarden to /mnt/Data/Config/backups)
4. **Weekly OpenSoak Update:** 3:00 AM Sundays (Updates code and dependencies on the Pi)
