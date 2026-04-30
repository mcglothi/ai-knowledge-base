---
context: llbean-work
---
# ESGUnix Ops Intelligence — Email-Derived

**Last Updated:** 2026-04-23
**Source:** Outlook email corpus, keyword=esgunix, Apr 23 – May 11 2025 (200 emails)
**Extracted by:** Copilot CLI via COM automation

---

## AAP Job Reliability Matrix (Apr–May 2025)

| Job Name | Runs | Errors | Success | Error Rate | Playbook |
|---|---|---|---|---|---|
| ESGUnix - RHEL ConfigMgmt (Base) | 26 | 24 | 2 | **92%** ⚠️ | ESGUNIX_RHEL_ConfigMgmt_Base.yml |
| ESGUnix - Patch/Install Targeted Packages | 9 | 5 | 4 | **55%** ⚠️ | PATCH_TARGETED_ONLY.yml |
| ESGUnix - Patch Middleware - wmq-prod-102 (Full/Reboot) | 2 | 2 | 0 | **100%** ⚠️ | PATCH_FULL_WMQ.yml |
| ESGUnix - Patch Middleware - wmq-prod-105 (Full/Reboot) | 2 | 2 | 0 | **100%** ⚠️ | PATCH_FULL_WMQ.yml |
| ESGUnix - Patch Middleware - wmq-prod-104/105/106 (Full/Reboot) | 2 | 2 | 0 | **100%** ⚠️ | — |
| ESGUnix - Patch WMS-PR (Full/Reboot) | 1 | 1 | 0 | 100% | PATCH_FULL_WMS_PR.yml |
| ESGUnix - Patch Creative-MB-PR (Full/Reboot) | 1 | 1 | 0 | 100% | PATCH_FULL_MEDIABANK.yml |
| ESGUnix - Patch DBA-ETL-PR-02 (Full/Reboot) | 1 | 1 | 0 | 100% | PATCH_FULL_ALL_RHEL.yml |
| ESGUnix - Patch Infrastructure-Unix-Test (Security) | 1 | 1 | 0 | 100% | PATCH_SEC_ALL_RHEL.yml |
| ESGUnix - Patch Middleware-wmq-preprod-102 (Security) | 2 | 1 | 1 | 50% | PATCH_SEC_WMQ.yml |
| ESGUnix - Patch Infrastructure-netapps-nft-hpna-tea (Security) | 1 | 1 | 0 | 100% | PATCH_SEC_ALL_RHEL.yml |
| ESGUnix - Patch Security-diag01-tftp01 (Security) | 1 | 1 | 0 | 100% | PATCH_SEC_ALL_RHEL.yml |
| ESGUnix - Patch WMS-DV (Security) | 1 | 1 | 0 | 100% | PATCH_SEC_WMS_DV_ALL_SERVERS.yml |

Healthy (0% error rate, sampled): ECOMM-PR-MIDS, DBA-ETL-PR-01, Middleware-WAS-101/102-PR, WASDM-PR, Middleware-PROD-3/4, wmb-prod-006, Infrastructure-CTM/ntp-pr, Datastage-PR1-1, Marketing-PR, JDA-AP/SCPO (all envs), Saviynt-Non-Prod, Mediabank (Appstop/Appstart both DV/PR), Infrastructure-Splunk-PR.

---

## Critical Issues

### 1. RHEL ConfigMgmt (Base) — 92% failure rate
- Job: `ESGUNIX_RHEL_ConfigMgmt_Base.yml`
- Inventory: Linux - All Servers
- Credential: `svc-anisble_SSHKey_ESGUnix_2025_1` (note: typo in credential name — "anisble")
- Ran daily at ~08:00 UTC; most runs 3–3.5 hours then failed
- Root cause not captured in email bodies (no specific error text forwarded)
- **Action needed:** Review AAP job output for actual task failures; suspect host connectivity, Centrify, or role idempotency issues

### 2. WMQ Production Patching — 100% failure
- Affected: wmq-prod-102, wmq-prod-105, wmq-prod-104/105/106
- TOC-reported error on wmq-preprod-102: `async task failed` (msg truncated in email)
- INC1154654 raised for wmq-prod-102 Comvault Backup Issues (related?)
- Javier Cedeño investigating

### 3. RHEL7 ELS Repository Failure — netapps/hpna-tea
- INC1156979 — job 456469 failed
- Root cause: `rhel-7-server-els-rpms` repo unavailable at satcap.llbean.com
- URL: `https://satcap.llbean.com/pulp/content/Default_Organization/Library/content/els/...`
- Fix options: disable repo temporarily (`yum --disablerepo=rhel-7-server-els-rpms`), or reconfigure baseurl
- Reference: https://access.redhat.com/articles/1320623

---

## Incidents (Apr–May 2025)

| Incident | Date | Systems | Status |
|---|---|---|---|
| INC1154654 | 2025-04-27 | wmq-prod-102 (Comvault Backup/Patching) | Open at capture time |
| INC1154655 | 2025-04-27 | Creative-MB-PR patching failure | Open at capture time |
| INC1156979 | 2025-05-11 | netapps-nft-hpna-tea RHEL7 ELS repo failure | Open at capture time |

---

## New Servers Added (Apr–May 2025)

| Hostname | IP | Datacenter | Added To |
|---|---|---|---|
| gcsds-test-01 | — | — | Unix patching (same schedule as ds-test*), OmniCenter monitoring — DMND0025768 |
| hpna-pr-02 | 10.120.245.35 | SWDC / 10.120.245.0 | Unix patching (same as hpna-pr-01), OmniCenter monitoring |

hpna-pr-02 specs: 6 vCPU, 32 GB RAM

---

## Notable Human Threads

### Splunk Servers Hung (2025-04-23)
- Reported by Mark Mulligan; affected: spli-pr-01, spli-pr-04, spli-pr-06
- spli-pr-06: stale NFS mount at `/opt/splunk/var/lib/splunk_cold`
- spli-pr-04: Centrify down, SSH unavailable
- spli-pr-01: rebooted, still hung
- Hank Uhl reset VMs
- Underlying issue: Splunk indexers hitting OOM — Mark rebooting multiple servers/hour
- Outcome: Hank offered to investigate available cluster memory for Splunk memory add

### AAP + Thycotic Integration (2025-05-02)
- Ben Hoisington (IS Architect) following up with Mark Mulligan on adding Thycotic vault credentials to AAP job templates
- Mark: discussed with Ansible rep, rep "looking into it"
- Status: **In progress / pending Ansible rep response** — no resolution by May 2025

### Beumer RHEL Vulnerabilities (2025-04-29)
- Servers: bmr-pr-app02, shp-pr-csc02 (OFC sorters)
- bmr-pr-app02: patched CHG0253045, confirmed by Javier
- shp-pr-csc02: Tenable findings persist; CyberSecurity reviewing (credential scanning issue suspected)
- Both servers on security-only patch schedule — Javier flagged this leaves many packages behind
- Maintenance window available until 4pm, restart required (alerts OFC Maintenance group due to sorter impact)
- Contact: Scott Mallar (OFC application side)

### RHEL7 EOL / Tenable Findings (2025-04-28)
- Manhattan servers: Tenable RHEL7 EOS findings will be **recast until Feb 2026** per Michael Mohr (Cybersecurity)
- Context: Company bought ELS (Extended Life Cycle Support) — Carolyn Davis-Mayo raised why patching still failing if ELS purchased
- Root cause: ELS repo issues at satcap (see INC1156979 above)
- Key people: Michael Mohr (Lead Cybersecurity Analyst), Rhonda Hamel, Tammy Curtis, Javier Cedeño, Daniel Fe[nandez?]

### RHEL9 Automation v1.0 Complete
- From Hank Uhl meeting notes share (2025-05-08): "RHEL9 automation (Tim) is now complete as v1.0"
- Meeting notes doc: Unix_Meeting_Notes_20250508 on SharePoint (ESGUnix meetings site)
- Note: v1.0 complete but refinement ongoing

### opr00274 Abend in PROD
- Subject line only captured; body not available in corpus
- Referenced in human threads list — investigate separately if needed

### Oracle Hardware for Nutanix
- Multi-party thread about Oracle hardware; context: potentially repurposing Oracle HW for Nutanix cluster
- Body not fully captured

### Decommission GitHub Servers DMND0025720
- Demand ticket for decomming GitHub servers

### Red Zone AD Groups by Server / ESXi Server List
- Thread sharing AD group-to-server mapping for Red Zone
- Useful for access control / inventory work

---

## Key Contacts (derived from email corpus)

| Name | Role | Email |
|---|---|---|
| Javier Cedeño | Systems Engineer (ESGUnix, TOC liaison) | jcedeno@llbean.com |
| Hank Uhl | Sr. Systems Engineer | huhl@llbean.com |
| Nathan Hoy | — | nhoy@llbean.com |
| Mark Mulligan | Systems Engineer (Splunk) | MMulligan@llbean.com |
| Ben Hoisington | IS Architect, Infrastructure | bhoisington@llbean.com |
| Scott Mallar | OFC application side (Beumer/sorters) | smallar@llbean.com |
| Ethan Hemphill | — (CC on Beumer thread) | ehemphill@llbean.com |
| Michael Mohr | Lead Cybersecurity Analyst | mmohr@llbean.com |
| Carolyn Davis-Mayo | — (RHEL7 ELS thread) | — |
| Ron Lussier | — (HPNA server thread) | Rlussier@llbean.com |
| Technical Operations Center | TOC (Costa Rica) | technicalopscenter@llbean.com |
| Berny Vargas | TOC Sr. / new server adds | bvargasgar@llbean.com |
| Jonathan Jimenez | TOC Computer Operations Associate | — |
| Alex Wolf | — | — |

---

## AAP Infrastructure Reference

- AAP URL: https://ans-pr-aap01/#/jobs/playbook/<job_id>
- Satellite/capsule: satcap.llbean.com
- Service account: `svc-anisble_SSHKey_ESGUnix_2025_1` (note typo)
- Primary inventory: `Linux - All Servers`
- Primary project: `ESGUnix_ConfigMgmt`

---

## Raw Export

Outlook JSON export (200 emails): `C:\Temp\aikb_email_export.json` (local Windows only — not committed)
Scraper script: `C:\Temp\outlook_scrape.ps1`
