# AIKB Context Guide

**Last Updated:** 2026-04-30
**Purpose:** Disambiguate personal homelab content from LLBean work content for agents and the user.
This AIKB spans multiple distinct environments. Content is accurate within its own context — do not
apply homelab hostnames, credentials, or tooling to LLBean work, or vice versa.

---

## Directory → Context Mapping

| Directory | Context | Description |
|-----------|---------|-------------|
| `work/` | `llbean-work` | LLBean infrastructure, Ansible automation, VM lifecycle, Zscaler |
| `home-lab/` | `personal-homelab` | Personal TrueNAS cluster, self-hosted services, homelab network |
| `personal/` | `personal` | Goals, identity, preferences, dev environments, TELOS |
| `personal-projects/` | `personal` | Personal coding projects (OpenSoak, Kyloch, Cliparr, etc.) |
| `side-gigs/` | `personal` | APF, AI Services consulting |
| `projects/` | `shared` | Cross-cutting tooling (AIKB graph), personal design projects |
| `ideas/` | `personal` | Quick-capture inbox |

---

## Credential Sources by Context

### LLBean Work (`llbean-work`)
- **Primary:** Delinea Secret Server — `tss secret --secret <id> --field <field>`
  - Vault map: `personal/vaults/delinea.yaml` (name → ID lookup)
- **Fallback:** Ask user
- **NOT applicable:** Bitwarden/Vaultwarden (personal homelab service — does not exist in the LLBean environment)

### Personal Homelab (`personal-homelab`)
- **Primary:** Vaultwarden (self-hosted Bitwarden) — `vault.home.timmcg.net`
  - CLI: `bw get password "PAT/<Service>/<Identity>" --session "$(cat ~/.bw_session)"`
  - Alias: `bwu` to unlock, then above pattern
- **Fallback:** Delinea → ask user
- **Safety:** Never `bw unlock` or `bw status` without `--session`; agents cannot unlock interactively

---

## Infrastructure Signals

### LLBean (`llbean-work`)
| Signal | Examples |
|--------|---------|
| Hostnames | `*.llbean.com`, `inf-dv-*`, `inf-pr-*`, `ans-pr-hub01.llbean.com` |
| Networks | Stonewood (SWDC/DC1), Brunswick (BLDC/DC2), OFC (DC3) |
| Tools | Ansible AAP/Tower, Nutanix, vCenter, Infoblox, Brocade, Palo Alto, F5, Satellite, CrowdStrike |
| GitHub org | `tmcglothin_llbean` |
| Service account | `svc-ansible` |

### Personal Homelab (`personal-homelab`)
| Signal | Examples |
|--------|---------|
| Hostnames | `*.home.timmcg.net`, `*.timmcg.net`, `10.10.10.*` |
| Servers | TrueNAS (Babbage, `10.10.10.10`), Hopper GB10 (`10.10.10.200`), Turing VM (`10.10.10.50`) |
| Tools | Vaultwarden, Authentik, Ansible Semaphore, Pi-hole, Nginx Proxy Manager, Grafana/Prometheus |
| GitHub org | `mcglothi` |
| Service account | `svc_ansible`, `svc_claude`, `svc_gemini` |

---

## Agents: Context-Switching Rules

1. **If working in a LLBean work repo** (e.g., `APP_Ansible_Prod_*`, `APP_Zscaler_*`):
   - Use `llbean-work` context
   - Credentials via Delinea only
   - Do not reference `home-lab/` infrastructure

2. **If working in personal/homelab repos** (e.g., `mcglothi/ansible`, `homelab-*`):
   - Use `personal-homelab` context
   - Credentials via Vaultwarden (Bitwarden CLI)
   - Do not reference LLBean internal hostnames

3. **If working in AIKB itself** (this repo):
   - Both contexts may be relevant — check the `context:` frontmatter on any file before acting
   - Infrastructure references are always scoped to their file's context

---

## File-Level Context Tag

Most AIKB files carry a `context:` field in their YAML frontmatter:

```yaml
---
context: personal-homelab   # or: llbean-work | personal | shared
---
```

When in doubt, check the file's `context:` tag or its parent directory.
