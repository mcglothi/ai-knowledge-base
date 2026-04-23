# Nutanix Ops Intelligence — Alert Patterns

**Last Updated:** 2026-04-23
**Source:** Outlook "nutanix alarms" folder — 500 of 2502 emails, Apr 23 – May 29 2025
**Extracted by:** Copilot CLI via COM automation

---

## Cluster Inventory

| Cluster | IPs | UUID | AOS Version | Hardware |
|---|---|---|---|---|
| ntx-dc1-ahv01 | 10.122.125.201–215 (10-node) | 00061ef4-db01-d99a-3baa-7cc2558956c3 | fraser-6.8.1 | NX-8170-G8 |
| ntx-dc1-ahv02 | 10.122.125.206–220 (10-node) | 00061fe7-2b79-7290-70ef-7cc2558955bd | fraser-6.8.1 | NX-8170-G8 |
| ntx-dc1-ahv03 | 10.122.125.221–223 (3-node) | 00063245-c34c-d6b7-00f7-7cc2558d37f5 | fraser-6.8.1 | NX-8170-G8 |
| ntx-dc2-ahv01 | 10.121.125.201–206 (6-node) | 00061fd0-6b78-f66c-00a7-7cc25589554a | fraser-6.8.1 | NX-8170-G9 |
| nutanix.llbean.com (PC) | 10.122.125.200, .230, .231 | c914f09a-72a3-409d-9f9c-1034a18e1b54 | 2024.3.0.1 | — |

**Prism Central:** https://10.122.125.200:9440 (primary), .230:9440, .231:9440

---

## Alert Volume Summary (500-email sample, Apr–May 2025)

| Severity | Count | % |
|---|---|---|
| WARNING | 475 | 95% |
| INFO | 14 | 3% |
| RESOLVED | 6 | 1% |
| CRITICAL | 5 | 1% |

**Unresolved alert backlog (Prism Central):** 554–579 per day (digest Apr 23–28). Backlog not shrinking — growing slightly.

---

## Alert Patterns by Type

### 1. VSS Snapshot Not Supported — A130105 ⚠️ NOISE (70% of all alerts)

- **352 alerts** across 246 unique VMs
- Alert: `VSS snapshot is not supported for the VM '<name>', because VSS software is not installed`
- Cause: VMs running on AHV but alert fires with ESX-centric message — Nutanix KB 7007
- Impact: Crash-consistent snapshots taken instead of app-consistent — functionally fine for Linux VMs
- **Action:** Bulk-suppress in Prism Central. VSS only relevant for Windows VMs needing app-consistent snapshots.
- Top affected clusters: ntx-dc1-ahv01 (286), ntx-dc2-ahv01 (63), ntx-dc1-ahv02 (2), ntx-dc1-ahv03 (1)
- KB: https://portal.nutanix.com/kb/7007

<details>
<summary>Full VSS VM list (246 VMs, sample of top frequency)</summary>

Notable VMs triggering multiple times: gcsds-test-01, mkt-pr-app03/04, sav-prod-01, ilks-prod-001, sec-pr-diag01, zs-appc-cde01–04, hpna-pr-02, splsyslog-gw02, spldeploy01, omni-pr-flw01/app02, zs-pse-prod01–04, by-pr-sre01–04, by-pr-app01/02, ans-pr-exe01, ans-pr-aap01, ecbatch-prod01, mkt-pr-cloud1, egw-pr-app01, TM-TEST-99, ilmt-prod-001, ntx-sw-pc02/03, wms-pr-app01/03, jnkn-pr-agnt01
</details>

---

### 2. CVM Python Service Restarting Frequently — A3037 ⚠️

- **54 alerts** — all ntx-dc1-ahv01, CVM IP 10.122.125.201
- Alert: `One or more cluster services have restarted within 15 minutes in the PCVM/CVM`
- Impact: Cluster performance may degrade; multi-node occurrence = serious
- Cause: Faulty behavior / frequent crashes in a short period
- **Action:** Contact Nutanix support if recurring. KB: https://portal.nutanix.com/kb/2472
- Node: HM234S003578, Block: 23SG5K300044

---

### 3. Flow Control Plane Failed — A200602 ⚠️

- **14 alerts** — ntx-dc1-ahv01
- Alert: `Flow operation failed. Cleanup after reconciliation to AHV host`
- Cause: Microsegmentation service unreachable, or PE cluster unavailable, or Remote Connection from PC failing
- Impact: Flow rules cannot be programmed — microsegmentation gaps
- **Action:** Check PC microsegmentation service, PE acropolis service, AHV microsegmentation module
- Affected AHV host UUID: 5a439e11-80e2-4b1b-b31f-aca7c... (truncated)

---

### 4. Cluster Service Acropolis Restarting — A3034 ⚠️

- **8 alerts** — all ntx-dc1-ahv01
- Dates: Apr 23, Apr 30, May 1 (×2), May 7, May 8, May 28, May 29
- Alert: `Cluster Service ['acropolis'] Restarting Frequently`
- Persistent — recurring across 5+ weeks on same cluster
- **Action:** Open Nutanix support case. Acropolis service instability = hypervisor control plane risk.

---

### 5. NGT Not Reachable — A130168

- **21 alerts** — primarily ntx-dc2-ahv01 (19), ntx-dc1-ahv02 (2)
- Affected VMs (ntx-dc2-ahv01): llb-ctmapppr03/04, llb-adcapppr02, llb-secuia02, pe1db02, llb-appapppr02, llb-ad04, ldap-ad02, pe1app02/04/06, llb-vtxapppr02, llb-aappconn02/04, llb-dfspr02, llb-sitapppr02, llb-exch02, llb-bssapppr02, llb-entca02
- Affected VMs (ntx-dc1-ahv02): ps1ci01, llb-sqlss03
- **Pattern:** Mostly `llb-` prefixed VMs on dc2 — likely Windows VMs with NGT communication issue
- **Action:** Verify NGT service running inside VMs; check Nutanix Guest Tools version compatibility

---

### 6. NGT CD-ROM Not Unmounted — A130334 (INFO)

- **14 alerts** — ntx-dc1-ahv02 (9), ntx-dc1-ahv01 (5)
- VMs: spli-pr-06, spli-pr-04, ntp-pr-01, was-test-102, ps1ci01, pp2ci01, pp2db01, pp2app01/02, ps1app02, ps1db01, mb-pr-app02/media02/web02
- Informational only — NGT ISO left mounted post-install
- **Action:** Eject NGT CD-ROM from affected VMs

---

### 7. Application-Consistent Recovery Point Failed — A130165

- **8 alerts** — ntx-dc1-ahv02 (4), ntx-dc2-ahv01 (4)
- Affected VMs: llb-vendc01, llb-cvcmagpr02, llb-rdsapppr03, llb-flexsqlqa01, llb-exch02, pe1app06, llb-bssapppr02, llb-entca02
- Cause: Quiesce failed or timed out
- Fallback: Crash-consistent snapshot taken
- **Action:** Review guest VM logs; likely NGT/VSS issue inside Windows VMs

---

### 8. CRITICAL — CPU Runway: ntx-dc1-ahv01

- **May 3:** runway = **1 day** (immediate risk)
- **May 7:** runway = 61 days (recovered — something was done)
- Alert A120089: CPU capacity projection
- Cluster ID: 2277713329777417044 (note: different ID than other ntx-dc1-ahv01 alerts — may be a sub-cluster or metric anomaly)
- **Action:** Monitor; runway improved but still finite. Consider capacity add or VM migration.

---

### 9. CRITICAL — CVM Reboots

| Date | CVM IP | Cluster | Node |
|---|---|---|---|
| 2025-05-01 08:21 EDT | 10.121.125.205 | ntx-dc2-ahv01 | HM244S003258 |
| 2025-05-02 03:57 EDT | 10.122.125.205 | ntx-dc1-ahv01 | HM237S004743 |

Both blocks NX-8170-G8/G9. Block ID 24SH5R220147 (also linked to power supply failure below).

---

### 10. CRITICAL — Power Supply Failure: ntx-dc2-ahv01

- **Block:** 23SH5K410303 — Power supply 1 DOWN (State: 0xb)
- Node: HM244S003258, Block: 24SH5R220147, Hardware: NX-8170-G9
- Date: 2025-05-21
- **No power redundancy on affected block**
- **Action:** Physical hardware replacement required. Escalate to datacenter ops / Nutanix hardware support.

---

### 11. Objects FQDN Error

- Alert: `Invalid FQDN ntx-dc1-obj02.llb` — objects store FQDN misconfigured
- Also: `Invalid FQDN nessus.org.` in Resolve (likely stale DNS entry in objects config)
- **Action:** Fix objects store FQDN in Prism Central Objects configuration

---

### 12. License Warning: ntx-dc2-ahv01

- Alert A1086: `License Node/Core Invalid`
- **Action:** Verify license coverage in Nutanix portal; may need license reapplication after hardware changes

---

## Activity Patterns

### Spike Days
- **May 28–29:** 291 alerts (58% of 500-sample) — major event, likely maintenance or outage
- **May 2–4:** 88 alerts — CVM reboots + CPU runway critical

### Hour-of-Day Pattern (UTC)
Peak windows: 23:00–01:00 UTC (6–8 PM ET), 00:00–02:00 UTC
These align with **evening maintenance windows / overnight patching** triggering VSS + NGT alerts.

---

## Recommended Actions (Priority Order)

| Priority | Action | Effort |
|---|---|---|
| 🔴 P1 | Replace failed power supply on ntx-dc2-ahv01 block 23SH5K410303 | Hardware |
| 🔴 P1 | Investigate acropolis service instability on ntx-dc1-ahv01 (8 restarts over 5 weeks) | Nutanix support |
| 🔴 P1 | Investigate CVM Python service restarts on ntx-dc1-ahv01 CVM .201 | Nutanix support |
| 🟠 P2 | Monitor CPU runway on ntx-dc1-ahv01 (was 1-day runway May 3; recovered) | Capacity planning |
| 🟠 P2 | Fix NGT on ntx-dc2-ahv01 VMs (21 unreachable, mostly llb- Windows VMs) | NGT reinstall |
| 🟡 P3 | Suppress VSS Snapshot alerts (A130105) — 70% of alert volume, low signal | Prism Central policy |
| 🟡 P3 | Fix Objects FQDN (ntx-dc1-obj02.llb) | Config fix |
| 🟡 P3 | Remediate license warning on ntx-dc2-ahv01 | Portal |
| 🟢 P4 | Eject NGT CD-ROMs on 14 VMs | Guest VM task |
| 🟢 P4 | Investigate app-consistent recovery failures on 8 VMs | VSS/NGT in guest |

---

## Notes

- Alert backlog of 554–579 unresolved alerts in PC (Apr 23–28 digests) — VSS suppression alone would clear ~70%
- All clusters running AOS fraser-6.8.1 — check for available updates
- ntx-dc1-ahv03 is a 3-node cluster (minimal — watch for quorum risk during maintenance)
- VSS alerts reference ESX in message body despite running AHV — cosmetic Nutanix bug

---

## Raw Export

Outlook JSON export (500 of 2502 emails): `C:\Temp\aikb_nutanix_export.json` (local Windows only)
Full scraper: `C:\Temp\outlook_scrape_folder.ps1` — rerun with `-MaxItems 2502` for full corpus
