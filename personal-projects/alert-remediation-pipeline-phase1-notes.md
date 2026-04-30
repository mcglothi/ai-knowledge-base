---
context: personal
---
# Phase 1 — Discovery Notes

**Date:** 2026-04-20
**Host:** babbage (10.10.10.10)

## Monitoring Containers Found

| Container | Image | Network | Internal Hostname | External Port (babbage) |
|-----------|-------|---------|-------------------|------------------------|
| `ix-grafana-grafana-1` | grafana/grafana:13.0.1 | `ix-grafana_default` (172.16.19.x) | `grafana`, `ix-grafana-grafana-1` | 30037 |
| `ix-prometheus-prometheus-1` | prom/prometheus:v3.9.1 | `ix-prometheus_default` (172.16.2.x) | `prometheus`, `ix-prometheus-prometheus-1` | 30028 |
| `alertmanager` | prom/alertmanager:latest | `monitoring_default` (172.16.25.x) | `alertmanager` | 9093 |
| `loki` | grafana/loki:latest | `monitoring_default` (172.16.25.x) | `loki` | 3100 |
| `promtail` | grafana/promtail:latest | (same as loki) | — | 9080 |

## Key Findings

1. **Alertmanager is already running** — standalone Docker container on `monitoring_default` network, NOT a TrueNAS app. This is good — we can use it as-is or reconfigure it.

2. **Loki + Alertmanager share `monitoring_default` network** — Event Router can reach both by container name.

3. **Grafana and Prometheus are on separate TrueNAS app networks** (`ix-grafana_default` and `ix-prometheus_default`). They CANNOT reach Alertmanager by container name — different Docker networks.

4. **Grafana external port is 30037** (not 3000 as the plan assumed).

5. **Prometheus external port is 30028** (not 9090).

6. **node_exporter is running and healthy** on all 5 targets: babbage, hopper, farnsworth, pihole2, opensoak.

7. **DNS `babbage.home.timmcg.net` resolves to 0.0.0.0 from Newton** — local network DNS not reachable remotely. Use IP `10.10.10.10` for remote access.

## Blockers Flagged (per plan instructions)

- [ ] **Grafana ↔ Alertmanager network isolation**: Grafana (`ix-grafana_default`) and Alertmanager (`monitoring_default`) are on DIFFERENT Docker networks. Grafana cannot reach `alertmanager:9093` by container name. Options:
  - Connect Grafana's network to the monitoring network (may not be possible with TrueNAS apps)
  - Use IP `10.10.10.10:9093` as the Alertmanager URL in Grafana contact point
  - Move Alertmanager into `ix-grafana_default` network (requires recreating the container)
  - Use Grafana API to configure contact point with `http://10.10.10.10:9093`

- [ ] **Alertmanager already exists** — need to check its current config before overwriting. It may already be configured with routes we don't want to break.

- [ ] **Grafana admin password** — need to confirm Vaultwarden entry name. Plan says `homelab/grafana-admin`.

- [ ] **`hermes webhook subscribe --help`** — need to run on Newton to get exact flags.

- [ ] **Hermes binary path** — need `which hermes` on Newton.
