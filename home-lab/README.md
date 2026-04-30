---
context: personal-homelab
---
# Home Lab

**Last Updated:** 2026-02-20
**Summary:** Personal home infrastructure built around a UDM Pro gateway, TrueNAS as the primary app/storage server, and Ansible Semaphore for automation. All core services are running and managed by nightly automation.

## Container Management Strategy
Two-system approach (decided 2026-02-20):
- **TrueNAS native apps** — catalog apps (Plex, *arr, Nextcloud, NPM, Pi-hole, etc.)
- **Dockge** — custom compose stacks not in catalog (monitoring stack, and planned: vaultwarden, semaphore, unmanic, maintainerr)
- **Portainer** — ⚠️ TO REMOVE — redundant, provides no unique value over TrueNAS + Dockge
- Ad-hoc containers (vaultwarden, semaphore, unmanic, maintainerr) need migrating into Dockge stacks

---

## Subfolders

| Folder | Contents |
|--------|---------|
| [`infrastructure/`](infrastructure/) | Server inventory, network topology, DNS configuration |
| [`services/`](services/) | Self-hosted applications (Vaultwarden, Unmanic, etc.) |
| [`automation/`](automation/) | Ansible Semaphore, playbook catalog, scheduled tasks |
| [`security/`](security/) | Service accounts, SSH keys, access strategy |

## Quick Reference

| System | Address | Role |
|--------|---------|------|
| UDM Pro | 10.10.0.1 | Gateway, DHCP |
| TrueNAS (babbage) | 10.10.10.10 | Primary storage, Docker host, NPM reverse proxy |
| farnsworth | 10.10.10.100 | Secondary/test server |
| loki | 10.10.10.151 | Specialized server |
| Pi-hole (primary) | 10.10.0.2 | DNS (container on TrueNAS) |
| Pi-hole 2 (pihole2) | 10.10.0.22 | Secondary DNS (Raspberry Pi) |
| OpenSoak | 10.10.169.191 | Hot tub controller (Raspberry Pi) |
| Ansible Semaphore | ansible.home.timmcg.net | Automation UI |
| Vaultwarden | vault.home.timmcg.net | Password manager |

## Domain
Local services resolve under `home.timmcg.net` via Pi-hole. SSL handled by wildcard cert `*.home.timmcg.net` through Nginx Proxy Manager on TrueNAS.
