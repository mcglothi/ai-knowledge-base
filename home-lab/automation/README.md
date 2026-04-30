---
context: personal-homelab
---
# Automation

**Last Updated:** 2026-02-18
**Summary:** Ansible Semaphore runs scheduled playbooks nightly for container updates, Pi-hole maintenance, and config backups. Service account `svc_ansible` deployed across all core hosts.

---

## Files

| File | Contents |
|------|---------|
| [`semaphore.md`](semaphore.md) | Semaphore instance details, repo, scheduled task list |
| [`playbooks.md`](playbooks.md) | Full playbook catalog with targets and schedules |
| [`rgb-control.md`](rgb-control.md) | Desktop RGB lighting automation |

## Scheduled Tasks (summary)

| Time | Playbook / Task | What it does |
|------|-----------------|-------------|
| 2:00 AM daily | `nightly_update.yml` | Pulls and recreates all Dockge stacks on TrueNAS |
| 3:00 AM daily | `pihole_update.yml` | Updates Pi-hole gravity lists and core/FTL |
| 4:00 AM daily | `backup_configs.yml` | Backs up NPM, Semaphore, Vaultwarden configs to Data pool |
| 3:00 AM Sunday | `opensoak_update.yml` | Updates code, venv, npm deps on the OpenSoak Pi |
| 8:00 AM daily | `rgb-on.timer` | Turns on desktop RGB (restores state) |
| 8:00 PM daily | `rgb-off.timer` | Turns off desktop RGB (saves state) |
