---
tags: [security, monitoring, netalertx, scanning, udm-pro, nyquist]
hosts: [truenas, babbage]
services: [nyquist, netalertx]
last_updated: 2026-03-17
---

# Nyquist (NetAlertX)

**Last Updated:** 2026-03-17
**Summary:** Network security scanner and inventory auditor (NetAlertX). Acts as an active auditor for the home lab, detecting new devices, MAC changes, and port exposures.

---

## Deployment
- **Type:** Docker Container (Dockge Stack on TrueNAS)
- **Host:** babbage (10.10.10.10)
- **Image:** `ghcr.io/netalertx/netalertx:latest`
- **Network Mode:** `host`
- **Port:** 20211
- **URL:** [https://nyquist.home.timmcg.net](https://nyquist.home.timmcg.net)
- **Storage:** `/mnt/Containers/Nyquist/`

## Configuration
- **Scan Subnets:** `10.10.0.0/24 --interface=eno1`, `10.10.10.0/24 --interface=eno1`
- **Timezone:** `America/New_York`
- **DNS Integration:** Pi-hole API import enabled against the primary Pi-hole (`http://10.10.10.10:20720/`)
- **Dashboard URL:** `https://nyquist.home.timmcg.net`

## Live Configuration (2026-03-17 improvement pass)
- **Discovery model:**
  - `ARPSCAN` kept for local L2 segments only.
  - `PIHOLEAPI` enabled in `always_after_scan` mode.
  - `UNIFIAPI` enabled using a UniFi Site Manager integration token for UDM Pro (10.10.0.1).
  - `ICMP`, `NMAP`, `DIGSCAN`, `NSLOOKUP`, `AVAHISCAN`, `NBTSCAN` remain enabled.
- **Noise Reduction:**
  - `NEWDEV_ignored_IPs` set to `172.16.0.0/12` to exclude Docker internal bridge networks.
  - `NEWDEV_ignored_MACs` set to `02:42:ac*` to exclude Docker-generated virtual MACs.
- **Web monitoring enabled:** `WEBMON_RUN='schedule'`
- **DHCP monitoring enabled:** `DHCPSRVS_RUN='schedule'`
- **Timeout tuning:**
  - `ICMP_RUN_TIMEOUT=30` (stabilized gateway flapping alerts)
  - `ARPSCAN_RUN_TIMEOUT=45`
  - `AVAHISCAN_RUN_TIMEOUT=20`
  - `NBTSCAN_RUN_TIMEOUT=20`

## Results After March 17 Reconfiguration
- **Inventory Quality:** UniFi integration successfully imported richer metadata for 33+ devices, including AP-to-client topology and descriptive names (e.g., "Marconi AP1", "Office printer", "Sense Energy Monitor").
- **Alert Stabilization:** Gateway "Disconnected" flapping alerts resolved by increasing ICMP timeout.
- **Noise Filtered:** Docker bridge IPs and virtual MACs are now correctly ignored by the "New Device" detection logic.

## Current Assessment (2026-03-17)
- Nyquist is now a highly reliable source of truth for the home lab inventory.
- Routing-segment visibility is handled via Pi-hole API, while L2 topology and rich metadata are handled via UniFi Site Manager API.
- Container is healthy and persistent configuration is managed via `/mnt/Containers/Nyquist/config/app.conf`.

## Enabled vs Disabled Coverage
- Enabled now: `ARPSCAN`, `ICMP`, `NMAP`, `DIGSCAN`, `NSLOOKUP`, `AVAHISCAN`, `NBTSCAN`, `PIHOLEAPI`, `UNIFIAPI`, `WEBMON`, `DHCPSRVS`
- Still disabled: `SNMPDSC` (not strictly needed given rich UniFi data)

## Container / Compose Gaps
- NetAlertX still prints a capability warning at startup under TrueNAS SCALE even though scans execute successfully and the container is healthy. Treat this as residual platform-specific noise unless behavior regresses.
- Current stack file: `/mnt/.ix-apps/app_mounts/dockge/stacks/nyquist/compose.yaml`
- Current persistent config: `/mnt/Containers/Nyquist/config/app.conf`

## Recommended Completion Plan
1. Persist the ARP flux sysctls through a TrueNAS-native mechanism so they survive reboot without manual reapplication.
2. Review the periodic `WEBMON` results for service health tracking in the Nyquist dashboard.

## Known Good Evidence From This Review
- `unifi_api_import.py` successfully retrieved 6 devices and 27 clients from UDM Pro.
- Device inventory correctly maps "Marconi" AP hierarchy and client parent relationships.
- Manual `ARPSCAN` found 8 local responders across the primary segments.

## NPM Proxy Host
- **ID:** 39
- **Domain:** `nyquist.home.timmcg.net`
- **Forward:** `10.10.10.10:20211`
- **SSL:** Forced, Wildcard Cert ID 1.

## Homepage Shortcut
- **Group:** Infrastructure
- **Widget:** `netalertx` (Status + Device counts)
