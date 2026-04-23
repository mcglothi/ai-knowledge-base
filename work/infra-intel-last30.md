# Infrastructure Intelligence — Last 30 Days

**Last Updated:** 2026-04-23
**Source:** Outlook Inbox + Sent Items, Mar 24 – Apr 23, 2026 (460 signal emails of 668)
**Extracted by:** Copilot CLI via COM automation

---

## AAP Job Reliability — Current State (Mar–Apr 2026)

### Significantly Improved vs 2025
- **RHEL ConfigMgmt (Base):** Was 92% failure rate in Apr 2025 — **now 0% (2/2 success)**. Fixed.
- Credential name corrected: now `svc-ansible_SSHKey_ESGUnix` (was typo `svc-anisble_...`)
- AAP URL changed: `https://ans-pr-aap01/execution/jobs/playbook/<id>` (was `/#/jobs/playbook/`)

### Current Failing Jobs (Apr 2026)

| Job | Runs | ERR | Rate | Pattern |
|---|---|---|---|---|
| ESGUnix - Patch DBA-SHD_01-PR (Full/Reboot) | 5 | 4 | 80% | shd-pr-ora06 |
| ESGUnix - Patch Saviynt-Non-Prod (Full/Reboot) | 3 | 3 | 100% | — |
| ESGUnix - Patch Middleware-wmq-preprod-102 (Full/Reboot) | 3 | 3 | 100% | — |
| ESGUnix - Patch DBA-TAB_01/02-PR (Full/Reboot) | 3 | 3 | 100% | tab-pr-api01 |
| ESGUnix - Patch DBA-SHD_PAIR1-PR (Full/Reboot) | 4 | 3 | 75% | shd-pr-ora06 |
| ESGUnix - Patch DBA-SHD_PAIR2-PR (Full/Reboot) | 3 | 3 | 100% | — |
| ESGUnix - Patch DBA-ETL-PR-02 (Full/Reboot) | 3 | 3 | 100% | — |
| ESGUnix - Patch Datastage-Sandbox-DV (Full/Reboot) | 2 | 2 | 100% | — |
| ESGUnix - Patch DBA-SHD_PAIR1-DV (Full/Reboot) | 2 | 2 | 100% | — |
| ESGUnix - Patch Datastage-TEST-1 (Full/Reboot) | 3 | 2 | 66% | — |
| ESGUnix - Patch Infrastructure-netapps-nft-hpna-tea (Full/Reboot) | 2 | 2 | 100% | — |
| ESGUnix - Patch DBA-RMN-PR (Full/Reboot) | 2 | 2 | 100% | — |
| ESGUnix - Patch Middleware-QA-PF-ST-Odd (Full/Reboot) | 2 | 2 | 100% | — |
| ESGUnix - Patch Infrastructure-edxl-PR (Full/Reboot) | 2 | 2 | 100% | — |
| ESGUnix - Patch Creative-MB-DV-QA (Full/Reboot) | 2 | 2 | 100% | — |
| ESGUnix - Patch UCD-PROD (Full/Reboot) | 2 | 2 | 100% | — |
| ESGUnix - Patch Mediabank DV QA - Appstart Only | 3 | 2 | 66% | — |

**TOC-escalated DBA errors (Apr 22):**
- `INC: shd-pr-ora06` — Patching failure in both PROD SHD_01-PR and SHD_PAIR1-PR jobs
- `INC: tab-pr-api01` — Patching failure on DBA-TAB_01/02-PR (ans00142/ans00144/ans00144)
- Contact: Javier Cedeño investigating; escalated to Tim

**Healthy (0% error, all succeeding):** All Middleware-WAS/WASDM/PROD/wmb, JDA-AP/SCPO (all envs), Mediabank PR, EDW-DV/QA/PR, ECOMM (PR/QA), WMS-PR/DV/QA, Zscaler, Saviynt Prod, Infrastructure all-PR, DBA-ETL-PR-01 — full production patching largely healthy.

---

## Nutanix — Active Issues

### Case 02505157 — CVM Missing After BIOS Upgrade (RESOLVED)
- **Status:** RESOLVED Mar 30–31
- **Root cause:** Intel/Silicom/Supermicro 7xx Series NIC — LCM upgrade puts host in Phoenix, bonds with disconnected NICs caused network failure during upgrade
- **KB:** https://portal.nutanix.com/kb/19576
- **Fix:** Disable bond NICs without cables connected before LCM upgrade; run host-by-host `disable-vlan-offload`
- **Cluster affected:** ntx-dc2-ahv01 (LCM upgrade via Javier/Steven Foxe)
- **Nutanix engineers:** Vivekanand Koya, Sakib Ahmed (APAC), Angela Nelson, fuhai.wei

### ntx-dc2-ahv01 — Full Upgrade Complete
- Date: **Apr 1, 2026** (~12.5 hrs runtime)
- Completed by: Chris Montgomery
- Status: All software/firmware upgraded **excluding NIC FW** (deferred due to above NIC bug)
- **NIC FW upgrade still pending** — must apply KB 19576 workaround first

### Post-Upgrade Alert Spam — ntx-dc1-ahv01
- Tim reported alerts/errors spamming after 1-node cluster upgrade
- David Snyder (Nutanix SE) suggested re-running LCM inventory to clear
- Status: **Still spamming after inventory re-run** (Apr 1) — unresolved

### Nutanix SAML Certificate — Microsoft Entra ID (RESOLVED)
- Expired SAML cert for Nutanix app in Entra ID — flagged Mar 26
- Jason Mills → Henry Corrales (ESGIntel/IAM) → renewed Apr 9
- Contact chain: jkmills@llbean.com → hcorrales@llbean.com → IAM Team

### Nutanix Biweekly Sync
- L.L. Bean & Nutanix biweekly sync — standing meeting (Apr 1, Apr 10 attendances confirmed)

---

## Splunk Fleet — Apr 13 Mass Unreachable Event ⚠️

Ansible RHEL ConfigMgmt ran Apr 12–13 and found entire Splunk fleet unreachable:

**~35+ Splunk hosts unreachable on Apr 13:**
- **Forwarders (splf-):** splf-pr-01/03/04/06/08–13
- **Indexers (spli-):** spli-pr-01/02/03/05/06/08–13/15–25
- **Workers (splw-):** splw-pr-02/04/07/08/10/11/12/13, splws-pr-01
- **Other:** spld-pr-02, splsyslog-gw01/05, splwww03

**Likely cause:** Planned patching window or Splunk service maintenance. ConfigMgmt saw all as unreachable simultaneously — suggests controlled outage not individual failures.

**WMS fleet unreachable Apr 14:** wms-pr-app01–04/web01/02, wms-qa-app01–04/web01/02 — patching-related

**Zscaler fleet unreachable Apr 20:** zs-appc-bz2/6/8/11/12/14/16, zs-appc-cde01/02/04, zs-appc-prod02/04/06/08/10/14/16/18/20/22, zs-lss-app2 — patching-related

**Other intermittent unreachable hosts (this month):**
- ecwcmq01 (Apr 1–2) — also has disk space alert ITS-8066
- llb-pmtdbt01 (Apr 8)
- llb-vtxsqlpr02 (Apr 3)
- sec-scan-ta15 (Apr 10)
- jnkn-pr-cjoc01 (Apr 22)
- san-mgmt-scg02 (Mar 25)

---

## Infrastructure Events & Changes

### hpna-pr-02 — Ansible Inventory FQDN Mismatch
- William Dillon (Network Services) reported: `hpna-pr-02` in inventory, `hpna-pr-02.llbean.com` not present
- Error: `FAILED! => {"changed": true, "cmd": "ssh -oStrictHostKeyChecking=no svc-ansible..."}`
- **Fix needed:** Add FQDN `hpna-pr-02.llbean.com` to Ansible inventory
- Contact: wdillon@llbean.com (office 207-552-5479)

### /boot Space on Oracle Servers
- Hank asked Berny Vargas (TOC) to check all remaining Oracle DB servers for /boot space
- Berny confirmed today (Apr 23): will check and fix
- **Action:** TOC handling; follow up if not resolved by end of week

### SWDC Rack 5N — Ready for New Servers
- Today (Apr 23): Asif Siddiqi cleared Rack 5N at Stonewood
- Network team finalizing cabling, server team can start racking
- Contact: tdoucette1@llbean.com (Network Services Manager), msiddiqi@llbean.com

### East/West Visibility VMs (ESG-553) — Pending
- Aaron Smiley (asmiley@llbean.com) requested 2 lightweight VMs for automated infrastructure inspection
- Subnets: SWDC 10.122.245.0/24, BLDC 10.121.245.0/24
- Tim said to put in JSM — Aaron submitted ESG-553 (Mar 31)
- **Status: Still outstanding as of Apr 22 (Aaron followed up)**

### MediaBank DEV — Slow Downloads
- Reported Apr 17 by Cody Wall (cwall@llbean.com): slower than expected download speeds
- Tim CC'd as server admin; Aissen Contreras requested JSM ticket
- **Status:** Ticket requested, likely open

### Ansible PROD Patching — Complete
- CHG-2693: Ansible PROD environment patched Apr 15 at 10am
- Completed by Javier Cedeño

---

## Major Incidents

### ITS-6825 — Ecom Payment Failures (RESOLVED)
- Date: Mar 30, 07:30 – 12:35 ET
- Scope: Payment calls from Ecom were failing
- Domain Manager: Aaron Scifres
- MIM: Jose Ulate
- Jira: https://llbean.atlassian.net/browse/ITS-7977

### ITS-8066 — ecwcmq01 Disk Space Critical (OPEN→ASSIGNED TO TIM)
- OmniCenter alert: ecwcmq01 root partition approaching threshold
- Assigned to Tim McGlothin (Apr 1)
- **Check current status**

### ITS-8209 — Control-M ans00134 ENDED NOTOK QA (ASSIGNED TO TIM)
- Control-M job ans00134 abend code 99 in QA
- Assigned to Tim McGlothin (Apr 6)
- **Check current status**

---

## Platform & Tooling Changes

### ServiceNow → JSM (Complete)
- ServiceNow decommissioned **Mar 30, 2026**
- Historical data: SNOWFort (internal L.L.Bean tool)
- All new ticketing: JSM (Jira Service Management)
- Reference: Sue Oliver (stoliver@llbean.com)

### Jenkins — Upgraded (Complete)
- Upgraded to **Jenkins 2.492.1** (Mar 27–28)
- Included: plugin updates, Java runtime updates, Nexus/dependency validation
- Performed by: Luis Rodríguez
- Monitor for: pipeline step regressions, notification changes, deployment integrations

### MongoDB QA → Atlas (Complete)
- Migration date: **Apr 9, 2026** (8am–noon)
- Order Services QA collection on MongoDB Atlas
- New connection string required for QA — see: https://llbean.atlassian.net/wiki/spaces/OCAO/pages/4849500224
- Contact: Deborah Bria (dbriao@llbean.com, Senior PM)

### GitHub Copilot — Active
- Tim granted access **Mar 31, 2026** via llbeaninc org
- Fine-grained PAT and OAuth app added same day

### Power Shutdown — HQ/CRC/Double L
- Occurred: **Apr 10, 2026** (all day, intermittent)
- Central Maine Power system testing
- Network/printing impacted at HQ; file servers/M365/Jira/SAP remained available

---

## Project Watchtower — OmniCenter Replacement

- Confluence page shared by Jason Mills: "Project Watchtower: Evaluating AI-Enhanced Open-Source Observability Stack as a Replacement for OmniCenter"
- https://llbean.atlassian.net/wiki/x/TACcWgE
- Tim noted at session start: objective to assess open-source observability stack
- Netreo also being evaluated — Mark Mulligan forwarded OVA deployment instructions from eval-support@netreo.com (Mar 30)
- **Both Project Watchtower and Netreo are live evaluations happening in parallel**

---

## Ongoing / Long-Running Threads

### Linux Access & Privilege Management
- Optiv (Roger Laplante, roger.laplante@optiv.com, 617-921-7241) coordinating with Hank Uhl
- Topic: Linux access and privilege management solutions
- Active thread as of Apr 17–20

### LL Bean CV Project — CDW
- CDW contacts: Art Haldeman (arthur.haldeman@cdw.com), Rajesh Iyer, Jason Hoang
- L.L.Bean contacts: Steven Foxe (sfoxe@llbean.com), Jason Mills
- Touchpoint scheduled: **Apr 29, 2026 at 11am**
- Project type: "CV" (possibly Converged/Compute/Customer-facing infrastructure — details in CDW meeting)

### Ansible AAP + Thycotic/CyberArk (from BeyondTrust context)
- Ben Hoisington was following up on vault credential integration with AAP
- BeyondTrust webinar traffic in inbox suggests this is still being evaluated
- No resolution email seen in last 30 days

---

## Certificate Management (AppViewX)

- AppViewX sending weekly expiry warnings to ESGintel@llbean.com
- Frequency: ~weekly alerts (Mar 26, 30, Apr 2, 6, 9, 13, 16, 20)
- **Pattern: Certificates expiring on a rolling basis — active cert churn**
- Nutanix SAML cert in Entra renewed Apr 9 (out-of-band, not AppViewX)
- If seeing recurring AppViewX alerts, verify auto-renewal workflow is functioning

---

## Dell AIOps Status
- Daily digests consistently showing: **"Your systems are all in great health! 0 new issues"**
- No cybersecurity misconfigurations detected
- Dell AIOps monitoring appears stable for covered systems

---

## Team Context

- **Hank Uhl:** PTO Mar 26–30, Apr 13–22 (out for stretches this month)
- **Javier Cedeño:** OOO personal Mar 30 – Apr 7 (Costa Rica holidays), back and active
- **David Bernier:** Family bereavement (brother Gregg passed suddenly, ~Mar 25)
- **On-call:** Tim on Unix Server schedule rotation (Jira notified of start/end)
- **Staffing:** Network Security Architect role open — Tim on interview panel

---

## Key Action Items (as of Apr 23)

| Priority | Item | Owner | Status |
|---|---|---|---|
| 🔴 | Investigate DBA-SHD/TAB-PR patch failures (shd-pr-ora06, tab-pr-api01) | Tim/Javier | TOC-escalated Apr 22 |
| 🔴 | Fix ntx-dc1-ahv01 post-upgrade alert spam | Tim/David Snyder | Open |
| 🔴 | NIC FW upgrade on ntx-dc2-ahv01 (apply KB 19576 first) | Chris/Javier | Deferred |
| 🟠 | ITS-8066 — ecwcmq01 disk space | Tim | Assigned |
| 🟠 | ITS-8209 — Control-M ans00134 abend | Tim | Assigned |
| 🟠 | Fix hpna-pr-02 FQDN in Ansible inventory | Tim | Pending |
| 🟠 | East/West visibility VMs (ESG-553) | Tim | Pending since Mar 31 |
| 🟡 | MediaBank DEV slow downloads | Tim | JSM ticket requested |
| 🟡 | /boot space Oracle servers | Berny (TOC) | In progress (Apr 23) |
| 🟡 | CDW CV Project touchpoint | Steven Foxe | Apr 29 |
| 🟢 | Nutanix biweekly sync | Tim | Standing meeting |

---

## Infrastructure URLs

| System | URL |
|---|---|
| AAP (Ansible) | https://ans-pr-aap01/ |
| Prism Central | https://10.122.125.200:9440 |
| Splunk | https://splw-pr-03.llbean.com:8000 |
| Jira | https://llbean.atlassian.net/browse/ |
| Satellite/Capsule | satcap.llbean.com |
| Nutanix portal | https://portal.nutanix.com |

---

## Raw Export

`C:\Temp\aikb_last30.json` — 824 emails, 460 signal, local Windows only
`C:\Temp\outlook_last30.ps1` — scraper script (rerun with `-DaysBack 30`)
