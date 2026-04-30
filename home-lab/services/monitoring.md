---
tags: [prometheus, grafana, loki, promtail, truenas, monitoring, metrics, cadvisor, node-exporter, homepage, dashboards, exportarr, sonarr, radarr, prowlarr, blackbox-exporter, pihole-exporter, farnsworth, pihole2, opensoak, alertmanager, discord, zfs, alerting, rules, sense, energy, power, hopper, nvidia, gpu, ai]
hosts: [truenas, babbage, farnsworth, pihole2, opensoak, sense, hopper]
services: [prometheus, grafana, loki, promtail, node-exporter, cadvisor, homepage, blackbox-exporter, pihole-exporter, alertmanager, sense-exporter, nvidia-textfile-collector]
last_updated: 2026-04-13
---

# Home Lab Monitoring Stack

**Last Updated:** 2026-04-13
**Summary:** End-to-end monitoring, logging, and alerting topology for home-lab hosts and services.
**Host:** babbage (TrueNAS SCALE, 10.10.10.10)

---

## Architecture

```
node-exporter (babbage)    ┐
node-exporter (farnsworth) │
node-exporter (pihole2)    ├─→ Prometheus ←─ cadvisor
node-exporter (opensoak)   │       ↕              ↕
exportarr-*                ┘     Grafana ←── Loki
pihole-exporter (x2)       ┐       ↑
blackbox-exporter (HTTP)   ├──────→┘
blackbox-exporter (ICMP)   ┘
sense-exporter ────────────────→ Prometheus (Sense cloud WS → local metrics)
Docker logs → promtail → Loki
```

**Total scrape targets: 28 confirmed UP (2026-02-22) + sense-exporter (added 2026-02-24)**

---

## Services

### Prometheus (TrueNAS App)
- **Container:** `ix-prometheus-prometheus-1`
- **Port:** 30028 (host) → internal
- **URL:** https://prometheus.home.timmcg.net
- **Config:** `/mnt/.ix-apps/app_mounts/prometheus/config/prometheus.yml`
- **Rules:** `/mnt/.ix-apps/app_mounts/prometheus/config/rules.yml` (11 alert rules, 6 groups)
- **Retention:** 30d, 10GB max (patched in rendered compose — re-apply after app update)
- **Config reload:** `docker kill --signal=SIGHUP ix-prometheus-prometheus-1`

### Alertmanager (Dockge — monitoring stack)
- **Container:** `alertmanager`
- **Port:** 9093
- **Config:** `/mnt/Containers/Alertmanager/alertmanager.yml`
- **Notification:** Discord webhook → [Stored in Vaultwarden: PAT/Discord/Alertmanager Webhook]
- **Routes:** All alerts → Discord; Watchdog → null (silenced)
- **Inhibition:** Critical suppresses Warning on same instance
- **Local source:** `~/code/homelab-monitoring/alertmanager/alertmanager.yml`

#### Alert Rules (11 rules, 6 groups)
| Group | Rules |
|-------|-------|
| homelab_availability | ServiceDown, HostUnreachable, ScrapeFailed |
| homelab_capacity | DiskFillingSoon (predict_linear 4d), DiskSpaceHigh (<15% free) |
| homelab_ssl | SSLCertExpiringSoon (<30d), SSLCertExpiringCritical (<7d) |
| homelab_truenas | ZFSPoolDegraded (non-online pool state) |
| homelab_opensoak | HotTubTempHigh (>105°F), HotTubTempLow (<90°F w/ heater on) |
| homelab_watchdog | Watchdog (dead man's switch — always firing, silenced) |

### Grafana (TrueNAS App)
- **Container:** `ix-grafana-grafana-1`
- **Port:** 30037
- **URL:** https://grafana.home.timmcg.net
- **SSO:** Native OIDC via Authentik
  - Login: "Sign in with Authentik" button
  - RBAC: Authentik "authentik Admins" group → Grafana "Admin" role
- **HTML panels enabled:** `GF_PANELS_DISABLE_SANITIZE_HTML=true` patched into rendered compose (2026-02-24)
- **Authentik SSO (generic_oauth):** env vars patched into rendered compose (2026-04-13)
  - `GF_AUTH_GENERIC_OAUTH_ENABLED=true`, `AUTO_LOGIN=true`, client_id/secret from Authentik provider pk=41
  - Auto-login redirects straight to Authentik — bypass via `https://grafana.home.timmcg.net/login?disableAutoLogin`
  - Rendered compose: `/mnt/.ix-apps/app_configs/grafana/versions/1.4.1/templates/rendered/docker-compose.yaml`
  - **Re-apply both patches after every Grafana app update** — find new rendered path under `/mnt/.ix-apps/app_configs/grafana/versions/*/templates/rendered/`
  - Restart: `docker compose -p ix-grafana -f <rendered_compose> up -d`
- **Datasources:**
  - Prometheus: uid `bfdudmv591on4a`, url `http://10.10.10.10:30028`
  - Loki: uid `cfdue7u51pce8b`, url `http://10.10.10.10:3100`
- **Custom dashboards (2026-02-22):**
  - `HOMELAB::CMD` — uid `homelab-cmd-001` — full overview, all hosts, service health, trends
  - `NETWORK::STATUS` — uid `network-status-001` — Pi-hole DNS, ICMP pings, HTTP probes, SSL certs
- **Community dashboards:**
  - Node Exporter Full: ID 1860
  - Cadvisor Exporter: ID 14282
  - Sonarr v3: ID 12530

## Hopper AI Monitoring (2026-04-13)

### node_exporter on hopper
- Binary: `/usr/local/bin/node_exporter` (v1.8.2, linux/arm64)
- Unit: `/etc/systemd/system/node_exporter.service`
- Port 9100, with `--collector.textfile.directory=/var/lib/node_exporter/textfile_collector`
- **GB10 unified memory**: tracked via `node_memory_MemTotal_bytes` / `node_memory_MemAvailable_bytes` — correct. Do NOT use GPU VRAM queries (returns "Not Supported" on GB10).

### nvidia-smi textfile collector
- Script: `/usr/local/bin/nvidia-textfile-collector.sh`
- Timer: `/etc/systemd/system/nvidia-textfile-collector.timer` (every 15s)
- Output: `/var/lib/node_exporter/textfile_collector/nvidia_gpu.prom`
- Metrics: `nvidia_gpu_utilization_percent`, `nvidia_gpu_memory_bandwidth_utilization_percent`, `nvidia_gpu_temperature_celsius`, `nvidia_gpu_power_draw_watts`
- Note: `nvidia_gpu_memory_bandwidth_utilization_percent` is memory *bus* utilization, not allocation — allocation is in `node_memory_*`.

### HOPPER::AI Grafana Dashboard
- UID: `hopper-ai-001`
- URL: `https://grafana.home.timmcg.net/d/hopper-ai-001`
- Sections: Unified Memory, GPU Compute, System (CPU/Load)

## Dashboards (Highly Polished Suite)

A new consistent, Matrix-green themed suite has been deployed:

| Dashboard | UID | Description |
|-----------|-----|-------------|
| **`OPERATOR::CONSOLE`** | `operator-console-001` | ★ Showcase dashboard — Matrix-green retro aesthetic, state timeline, heatmap, histogram, relay matrix, geomap. Built 2026-02-24. Local: `grafana/operator-console.json` |
| **`CYBER::CMD`** | `cyber-cmd-001` | Executive overview, service mesh status, cluster load pulse, and live logs. |
| **`OPENSOAK::VISUALIZER`** | `opensoak-vis-001` | Dedicated hot tub dashboard with water temp gauges and actuator matrix. |
| **`HOT TUB // WEATHER`** | `hot-tub-weather-001` | Retro-styled dashboard for spa and outdoor temp (04086). |
| **`SENSE::POWER`** | `sense-power-001` | Sense energy monitor — home consumption, solar, per-device breakdown. Local: `grafana/sense-power.json` |
| **`INFRASTRUCTURE`** | `rYdddlPWk` | Node Exporter Full — detailed OS metrics for all nodes. |
| **`CONTAINERS`** | `pMEd7m0Mz` | cAdvisor — detailed Docker container performance. |
| **`PI-HOLE`** | `Pi-hole-Exporter` | DNS and ad-blocking statistics. |

---

## ⚡ Sense Energy Monitor

- **Device IP:** `10.10.136.229` (WiFi, monitored via ICMP blackbox)
- **Data source:** Sense cloud WebSocket API (`clientrt.sense.com`) — NOT a local API
- **Exporter:** `sense-exporter` Docker container (custom Python, built from `~/code/homelab-monitoring/sense-exporter/`)
- **Port:** 9801
- **Credentials:** [Stored in Vaultwarden: PAT/Sense/Email], [Stored in Vaultwarden: PAT/Sense/Password]
- **Env vars:** `SENSE_EMAIL`, `SENSE_PASSWORD` (passed via Dockge stack env)

### Metrics exposed
| Metric | Description |
|--------|-------------|
| `sense_active_power_watts` | Total home consumption (W) |
| `sense_solar_power_watts` | Solar generation (W) — 0 if no solar |
| `sense_net_power_watts` | Net grid draw: positive = consuming, negative = exporting |
| `sense_grid_frequency_hz` | AC grid frequency |
| `sense_grid_voltage_l1_volts` | Leg 1 voltage |
| `sense_grid_voltage_l2_volts` | Leg 2 voltage |
| `sense_device_power_watts{device_name}` | Per-device consumption for active devices |
| `sense_up` | 1 = WebSocket connected, 0 = offline |

### Dashboard
- **`SENSE::POWER`** — uid `sense-power-001` — gauges, solar, net grid, per-device bar chart, history
- Local: `grafana/sense-power.json`

### Verification snapshot (2026-03-17)
- Exporter is live at `http://10.10.10.10:9801/metrics`; `sense_up = 1`
- Prometheus target `up{job="sense"}` returned `1` from `http://10.10.10.10:30028`
- Live sample during verification: `sense_active_power_watts = 1231.9`, `sense_device_power_watts{device_name="Always On"} = 938`
- Prometheus history confirmed this is not a transient spike:
  - `avg_over_time(sense_device_power_watts{device_name="Always On"}[24h]) = 939.0`
  - `avg_over_time(sense_device_power_watts{device_name="Always On"}[7d]) = 965.9`
  - `avg_over_time(sense_device_power_watts{device_name="Always On"}[30d]) = 1086.0`
  - `min_over_time(sense_active_power_watts[24h]) = 933.7`
- Conclusion: the documented `sense-exporter -> Prometheus -> Grafana` path is healthy; the current issue is an unusually high real baseline load, not a broken telemetry path.

### Deployment notes
1. Store credentials in Vaultwarden: `PAT/Sense/Email` and `PAT/Sense/Password`
2. Set env vars in Dockge stack before deploy: `SENSE_EMAIL=...`, `SENSE_PASSWORD=...`
3. Build: `docker compose build sense-exporter` (or Dockge handles it)
4. The exporter reconnects automatically on WebSocket drops — no restart needed
5. Sense device IP is in ICMP blackbox ping targets (alerts if it goes offline)

---

## 🛠️ App Instrumentation (OpenSoak)

The OpenSoak backend has been instrumented with the `prometheus_client` library to provide live application metrics.

- **Metrics Endpoint:** `http://10.10.169.191:8000/metrics`
- **Custom Metrics:**
  - `hottub_temperature_fahrenheit`: Current water temperature.
  - `hottub_hi_limit_fahrenheit`: Current hi-limit sensor reading.
  - `hottub_relay_state`: Boolean state (1/0) per component (heater, circ_pump, jet_pump, light, ozone).

---

### Monitoring Stack (Dockge)
- **Stack path:** `/mnt/.ix-apps/app_mounts/dockge/stacks/monitoring/compose.yaml`
- **Local copy:** `~/code/homelab-monitoring/compose-monitoring-updated.yaml`
- **Managed via:** http://dockge.home.timmcg.net (or http://10.10.10.10:31014)

#### node-exporter (babbage)
- Image: `prom/node-exporter:latest`
- Port: 9100 (host network)
- Selective collectors: cpu, meminfo, filesystem, netdev, loadavg, diskstats, uname, time, thermal_zone, **zfs** (added 2026-02-24)
- ZFS metrics exposed: `node_zfs_arc_size`, `node_zfs_zpool_state{state,zpool}` for all 5 pools (Containers, Data, Share, VMs, boot-pool)
- Note: `--collector.drivetemperature` not available in this build — disk temps require smartmon exporter (TODO)

#### node-exporter (farnsworth — 10.10.10.100)
- Deployed via Docker container (same image, host network)
- Port 9100 — UP

#### node-exporter (pihole2 — 10.10.0.22)
- Deployed 2026-02-22 via `docker run --network host`
- Port 9100 — UP

#### node-exporter (opensoak — 10.10.169.191)
- Deployed 2026-02-22 as systemd binary service
- Binary: `/usr/local/bin/node_exporter` (v1.8.2, linux/arm64)
- Unit: `/etc/systemd/system/node_exporter.service`
- Port 9100 — UP

#### cadvisor
- Image: `gcr.io/cadvisor/cadvisor:latest`
- Port: 8090 → 8080
- Scrapes Docker container metrics
- On 2026-03-12, observed `cadvisor` consuming very high CPU on `babbage` while spamming `failed to collect filesystem stats` errors for stale Docker `overlay2` paths under `/mnt/.ix-apps/docker/...`.
- Symptom pattern on TrueNAS SCALE: high load average with CPU mostly idle, multiple `zfs list` processes stuck in `D` state, and `cadvisor` burning CPU while walking container filesystem metadata.
- Recommended compose hardening for TrueNAS: add `--docker_only=true`, slow housekeeping with `--housekeeping_interval=30s`, and disable filesystem-heavy metrics with `--disable_metrics=disk,diskIO` unless per-container filesystem metrics are explicitly needed.
- Deployed on 2026-03-12 to `/mnt/.ix-apps/app_mounts/dockge/stacks/monitoring/compose.yaml`, then recreated only the `cadvisor` container. Post-change verification showed `cadvisor` drop from ~2800% CPU to ~1% CPU, `/metrics` remained reachable, and the old stale-`overlay2` filesystem-stat spam stopped.

#### blackbox-exporter (NEW 2026-02-22)
- Image: `prom/blackbox-exporter:latest`
- Port: 9115
- Config: `/mnt/Containers/Blackbox/blackbox.yaml`
- Local copy: `~/code/homelab-monitoring/blackbox.yaml`
- cap_add: NET_RAW (for ICMP probes)
- Modules: http_2xx, http_2xx_insecure, tcp_connect, icmp
- Probes:
  - HTTP: 12 services (all .home.timmcg.net services)
  - ICMP: 5 hosts (UDM Pro, babbage, farnsworth, pihole2, opensoak)

#### pihole-exporter-primary (NEW 2026-02-22)
- Image: `ekofr/pihole-exporter:latest`
- Port: 9617
- Target: `10.10.10.10:20720` (Pi-hole v6 web port — NOT port 80 which is NPM)
- Auth: `PIHOLE_PASSWORD` env var (NOT PIHOLE_API_TOKEN — that sends empty password)
- Password: [Stored in Vaultwarden: PAT/Pi-hole/App Password Primary]
- **Status: UP, producing metrics (v1.2.0) ✓**
- Note: Pi-hole v6 webserver on port 20720 (not default 80); NPM occupies port 80 on TrueNAS

#### pihole-exporter-secondary (NEW 2026-02-22)
- Image: `ekofr/pihole-exporter:latest`
- Port: 9618
- Target: `10.10.0.22:80` (Pi-hole on Raspberry Pi — default port 80, no NPM in front)
- Auth: `PIHOLE_PASSWORD` env var
- Password: [Stored in Vaultwarden: PAT/Pi-hole/App Password Secondary]
- **Status: UP, producing metrics (v1.2.0) ✓**

#### exportarr-sonarr
- Image: `ghcr.io/onedr0p/exportarr:latest`
- Port: 9707 | URL: http://10.10.10.10:8989
- API Key: [Stored in Vaultwarden: Sonarr API Key]

#### exportarr-radarr
- Port: 9708 | URL: http://10.10.10.10:7878
- API Key: [Stored in Vaultwarden: Radarr API Key]

#### exportarr-prowlarr
- Port: 9710 | URL: http://10.10.10.10:9696
- API Key: [Stored in Vaultwarden: Prowlarr API Key]

#### Loki
- Image: `grafana/loki:latest`
- Port: 3100
- Config: `/mnt/Containers/Loki/loki-config.yaml`
- Storage: `/mnt/Containers/Loki/`
- Retention: 30d
- **URL:** https://loki.home.timmcg.net (NPM proxy host ID 26)

#### Promtail
- Image: `grafana/promtail:latest`
- Port: 9080
- Config: `/mnt/Containers/Promtail/promtail-config.yaml`
- Docker service discovery via `/var/run/docker.sock`
- Pushes to `http://10.10.10.10:3100/loki/api/v1/push`
- Labels: job (container name), container, compose_project, compose_service, image

---

## Prometheus Scrape Targets

All 28 confirmed UP (2026-02-22):
```
node         → babbage (10.10.10.10:9100)
node         → farnsworth (10.10.10.100:9100)
node         → pihole2 (10.10.0.22:9100)
node         → opensoak (10.10.169.191:9100)
node         → hopper (10.10.10.200:9100)     ← added 2026-04-13
nvidia_gpu   → hopper (10.10.10.200:9100)     ← textfile collector; GB10 compute/temp/power
cadvisor     → babbage (10.10.10.10:8090)
prometheus   → babbage (localhost:30028)
sonarr       → babbage (10.10.10.10:9707)
radarr       → babbage (10.10.10.10:9708)
prowlarr     → babbage (10.10.10.10:9710)
pihole       → pihole-primary (10.10.10.10:9617)
pihole       → pihole-secondary (10.10.10.10:9618)
blackbox_http  → 12 HTTPS endpoints (proxied via 10.10.10.10:9115)
blackbox_icmp  → 6 hosts (proxied via 10.10.10.10:9115) — incl. Sense at 10.10.136.229
sense          → sense-exporter (10.10.10.10:9801)
```

---

## Local Source Files

All configs maintained at `~/code/homelab-monitoring/` on tesla:
- `compose-monitoring-updated.yaml` — monitoring Dockge stack
- `blackbox.yaml` — blackbox probe modules
- `prometheus-updated.yml` — full scrape config
- `playbooks/deploy-node-exporter.yml` — Ansible for remote node-exporter
- `grafana/homelab-command-center.json` — HOMELAB::CMD dashboard
- `grafana/network-intelligence.json` — NETWORK::STATUS dashboard
- `grafana/sense-power.json` — SENSE::POWER dashboard
- `sense-exporter/sense_exporter.py` — Sense → Prometheus exporter
- `sense-exporter/Dockerfile` — container build
- `sense-exporter/requirements.txt` — Python deps
- `deploy.sh` — end-to-end deployment script

---

## Pending / TODO

- [x] Finalize Pi-hole password rotation (Resolved 2026-04-11)
- [ ] Investigate the Sense `Always On` baseline now that the telemetry path is verified.
  - Verification on 2026-03-17 confirmed the exporter, Prometheus scrape target, and dashboard path are healthy.
  - Current baseline is materially high: roughly `0.94 kW` over 24h and `1.09 kW` over 30d for `Always On`.
  - First suspects to rule out are continuous HVAC/heat-strip behavior, hot-tub circulation/heating overlap, water-heating/recirculation loads, dehumidification, and lab/AV gear that Sense has not separated cleanly from `Always On` / `Other`.

---

## Homepage Dashboard

Config files at `/mnt/Containers/Homepage/` (backed up to `mcglothi/homelab-homepage`):
- `services.yaml` — 4 groups: Media, Infrastructure, Projects, Calendar
- `settings.yaml` — color: zinc, theme: dark, headerStyle: clean, single page (no tabs)
- `custom.css` — dark retro hacker aesthetic, nearly black background with radial gradient, matrix-green text (updated 2026-02-27)
- `widgets.yaml` — greeting, datetime, search, openmeteo (Topsham, ME), resources

**Key lesson:** Homepage widget URLs must use direct `http://IP:port` — NPM hostnames cause
`ERR_FR_REDIRECTION_FAILURE` because NPM redirects HTTP → HTTPS and Homepage can't follow.

**Key lesson:** scp won't overwrite files on TrueNAS (apps:docker ownership).
Use: `ssh host "sudo tee /path/file > /dev/null" << 'EOF' ... EOF`

**Key lesson — `docker restart` does NOT pick up a rebuilt image (2026-02-25):**
After rebuilding a custom image (`docker build -t name:local`), `docker restart <container>` keeps running the old image. Must use:
```bash
docker compose -p <stack> up -d --force-recreate <service>
```
This was hit during sense-exporter development — metrics appeared stale/wrong until force-recreated.

**Key lesson — Geomap dots not appearing (fixed 2026-02-24):**
Two bugs combined to prevent markers from rendering:
1. **Wrong location mode:** The layer was set to `mode: "lookup"` which expects a place name (e.g. "Dublin") for gazetteer lookup, not a lat/lon string. Fix: set to `mode: "coords"` with explicit `latitude`/`longitude` field references.
2. **No coordinate labels on Prometheus metrics:** The `global_ping` job used a flat `targets` list with no labels. `LabelsToFields` had nothing to extract. Fix: split `static_configs` into one entry per target, each with `latitude`, `longitude`, and `location` labels. These flow through the relabeling pipeline untouched.

After the fix, the pipeline is: `probe_duration_seconds{job="global_ping"}` (table, instant) → `convertFieldType` (lat/lon string→number) → `filterFieldsByName` → Geomap layer (coords mode).

Local files: `~/code/homelab-monitoring/prometheus-updated.yml` (Prometheus config) and `~/code/homelab-monitoring/grafana/cyber-cmd.json` (CYBER::CMD dashboard).

---

## UI Refinement Log (2026-02-27)

### Task: application dashboard (home.timmcg.net) refinements
- **Aesthetic:** Dark retro hacker theme, very dark grey (#0c0c0c) background with CRT scanlines and flicker.
- **Layout Evolution:**
    - Tried "Flexible Flow" (tiles grow horizontally to fit text), but reverted to a rigid grid for better visual balance.
    - Final Grid: Strictly capped at 4 columns per row via `settings.yaml` and CSS.
    - Tile Height: Locked to 180px with Targeting Corner Brackets (L-shapes) that glow on hover.
    - Calendar: Fully "un-trapped" — made transparent, full-width, and expanded to 850px height to sit directly on the background.
- **Versioning:** Implemented a scrollable footer (non-floating) with build version and UTC timestamp for cache verification.
- **Current Build:** v1.2.5

### Task: timmcg.net landing page refinements
- **Text Layering:** Fixed z-index conflict where scanlines appeared through text; text is now solid green and layered on top.
- **Versioning:** Added v1.0.4 footer with timestamp.
