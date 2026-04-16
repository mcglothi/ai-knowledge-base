# L.L. Bean — Infrastructure Engineering

**Last Updated:** 2026-04-16
**Summary:** Platform stack, team structure, and automation context for Tim McGlothin's work at L.L. Bean. Read this before diving into any LLBean Ansible or infra work.

---

## Team

**Team:** ESG Unix (Enterprise Systems Group — Unix)
**Role:** Unix Engineer
**Scope:** Core Unix/Linux infrastructure automation, VM lifecycle, patching, compliance hardening, and cross-team automation support

Other teams Tim's code supports: DBA, Distribution/WMS, EDW (Enterprise Data Warehouse), E-commerce, Marketing/Creative, Finance

---

## Platform Stack

### Virtualization
| Platform | Status | Notes |
|----------|--------|-------|
| **Nutanix AHV** (Prism Central) | Active — primary | Migrated from VMware. API endpoint: `nutanix.llbean.com` |
| VMware vCenter | Legacy — phased out | Still referenced in some older tooling |

**Nutanix clusters:**
- `ntx-dc1-ahv01` — Stonewood datacenter (SWDC / DC1)
- `ntx-dc2-ahv01` — Brunswick datacenter (BLDC / DC2)

### Automation
| Tool | Purpose |
|------|---------|
| **Ansible Automation Platform (AAP)** | Production automation — all playbooks run via AAP workflows |
| **GitHub** | Source control for all Ansible repos |
| **ansible-builder + Podman** | Custom Execution Environment builds |
| **Event-Driven Ansible (EDA)** | Rulebooks exist in ESGUnix repo (emerging use) |

**AAP automation hub:** `ans-pr-hub01.llbean.com`

### Operating Systems
| OS | Version | Status |
|----|---------|--------|
| RHEL | 8, 9 | Primary — all new builds |
| RHEL | 7 | Legacy — in-place upgrades to RHEL 8 done via `UTILITY_RHEL7_RHEL8_*` |
| AIX | — | Secondary — `aix` role handles patching |
| Windows Server | — | Supported via separate repo (`APP_Ansible_Prod_Windows`) |

### Identity & Access
| System | Purpose |
|--------|---------|
| **Centrify** | AD join for Unix/Linux servers — domain `llbean.com` |
| **Active Directory** | Core identity — `llbean.com` domain |
| Service account | `svc-ansible` — Ansible remote user for all automation |

### DNS / IPAM
| System | Purpose |
|--------|---------|
| **Infoblox** | DNS, DHCP, IPAM — API endpoint: `llb-gm-dns.llbean.com` |

### Endpoint Security
| Tool | Purpose |
|------|---------|
| **CrowdStrike Falcon** | EDR/XDR — deployed on all Linux hosts |
| **BlackBerry BES Client** | Endpoint security |
| **Nessus Agent** | Vulnerability scanning |

### Lifecycle / Config Management
| Tool | Purpose |
|------|---------|
| **Red Hat Satellite** | RHEL subscription management, patch repositories, client registration |

### Backup
| Tool | Purpose |
|------|---------|
| **CommVault** | Enterprise backup — covers DV/QA/PR environments across both DCs |

### Job Scheduling
| Tool | Purpose |
|------|---------|
| **CA Control-M (CTM)** | Enterprise job scheduling — Java runtime via Azul Zulu |

### Monitoring
| Tool | Purpose |
|------|---------|
| **Prometheus** | Metrics collection — node exporters on all hosts |
| **Grafana** | Dashboards |

### Notification
| System | Value |
|--------|-------|
| SMTP | `mymail.llbean.com:25` |

---

## Datacenters & Environments

### Datacenters
| Name | Alias | Notes |
|------|-------|-------|
| Stonewood | SWDC, DC1 | Primary |
| Brunswick | BLDC, DC2 | Secondary |
| OFC | OFC, DC3 | Office |

### Environments
| Abbreviation | Full Name |
|--------------|-----------|
| DV | Development |
| QA | Quality Assurance |
| ST | Staging |
| PR | Production |

---

## Ansible Repo Structure

**Primary repo:** `APP_Ansible_Prod_ESGUnix` (`~/code/APP_Ansible_Prod_ESGUnix/`)

### Playbook Naming Prefixes
| Prefix | Purpose |
|--------|---------|
| `PATCH_FULL_*` | Full patching (all packages) |
| `PATCH_SEC_*` | Security-only patching |
| `VMDEPLOY_*` | VM provisioning workflow (numbered 00–90 phases) |
| `VMDECOM_*` | VM decommission workflow |
| `ESGUNIX_*` | Base config management, CIS hardening |
| `RHEL_*` | RHEL agent/tool deployment |
| `REPORTS_*` | Inventory and compliance reporting |
| `UTILITY_*` | One-off maintenance operations |
| `DEPLOY_*` | Infrastructure deployment (Satellite, Prometheus) |

### VM Lifecycle Workflow (VMDEPLOY)
1. `VarMapping` — survey input → cluster/subnet/security group mappings
2. `CreateVM` — Nutanix AHV via cloud-init
3. `Infoblox` — DNS/DHCP registration
4. `WaitForSSH` — connectivity gate
5. `ConfigMgmt_Base` — RHEL hardening, base packages
6. `Satellite` — subscription registration
7. `BESClient_Setup` — BlackBerry endpoint security
8. `Crowdstrike` — Falcon agent
9. `NessusAgent` — vulnerability scanning
10. `Patch` — initial patching
11. `InventoryAdd` — add to AAP inventory
12. `SendEmail` — notification

### Key Roles
| Role | Purpose |
|------|---------|
| `rhel` | RHEL patching (full, security-only, space checks, maintenance windows) |
| `aix` | AIX patching |
| `centrify` | AD domain join and management |
| `rhel_configmgmt_base` | Core RHEL hardening (kernel params, postfix, root password, SSH) |
| `RHEL8-CIS-3.2.2` | CIS Level 1/2 hardening for RHEL 8 |
| `RHEL9-CIS-Devel-v1.0.0` | CIS Level 1/2 hardening for RHEL 9 |
| `commvault` | Backup integration |
| `promgraf` | Prometheus + Grafana deployment |
| `ctm` | Control-M condition management |

### org/ Team Structure
| Directory | Team / Domain |
|-----------|--------------|
| `org/esgunix/` | Core Unix infra (25 tasks: base packages, identity, hardening, repos, NTP, etc.) |
| `org/esgunix_apps/` | Satellite client, Oracle audit |
| `org/esgunix_reports/` | Java, Oracle, CrowdStrike, subscription manager reports |
| `org/dba/` | DBA — Oracle prerequisites, cron |
| `org/distribution/` | WMS (Warehouse Management), APK, GRY app start/stop |
| `org/edw/` | EDW — DB2 lifecycle, TSA HA, NFS, 90-day password changes |
| `org/ecomm/` | E-commerce — NFS, CrowdStrike static routes |
| `org/marketing/` | Marketing/Creative |
| `org/k8s/` | Kubernetes (emerging) |

---

## Variable Conventions

| Prefix | Scope |
|--------|-------|
| `cli_` | CLI variables passed via `-e` |
| `g_` | Global playbook-level variables |
| 3+ char role prefix | Role variables (e.g. `mur_` for `made_up_role`) |

Vault-encrypted secrets: `group_vars/vault.yml`

---

## Known Gotchas

- **Binary assets:** never overwrite in-place — always use a new filename and update the reference (GitHub CDN caches by URL)
- **Execution Environments:** if a playbook fails with missing Python modules, rebuild the EE — dependencies are baked in at build time
- **Brocade SAN sessions:** if SAN automation fails with session errors, use `mgmtapp --show` and `mgmtapp --terminate <sessionid>` to clear idle sessions (ref: Dell KB 000186005)
- **Production runs via AAP only:** don't run production playbooks from CLI; always use Tower/AAP workflows
- **Satellite vs Foreman:** old hosts may still be registered to Foreman — use `UTILITY_Foreman_Client_Migrate_to_Satellite.yml` to migrate

---

## AAP Workflow IDs (for reference)

| Workflow | ID |
|----------|----|
| ESX UCS Build | 1053 |
| ESX Rollback | 1077 |
| ESX Shared Storage | 1160 |
| VM Build | 1098 |
| VM Decom | 1100 |
