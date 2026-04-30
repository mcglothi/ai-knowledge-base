# AIKB Drift Detection Policy

## Overview

AIKB drift detection runs on Hopper (10.10.10.200) every 6 hours via systemd timer.
It checks all known machines for uncommitted, unpushed, or unpulled changes in their
AIKB clones.

## Network Topology from Hopper's Perspective

| Host    | IP           | Connectivity     | Notes                          |
|---------|--------------|------------------|--------------------------------|
| hopper  | localhost    | ✅ Reachable     | Always-on, 10G LAN             |
| feynman | 10.10.145.26 | ❌ Unreachable   | Different subnet from Hopper   |
| tesla   | 10.10.190.57 | ⚠️ WiFi only    | May be offline if device off   |
| newton  | 10.10.0.254  | ⚠️ WiFi only    | Laptop, variable connectivity  |

## Drift Detection Script

**Location:** `_tools/drift-check.py`
**Runs via:** `aikb-drift-check.timer` (systemd, every 6h)
**Output:** `_runtime/drift-report-{date}.json`

### What it checks per host:
1. **Uncommitted changes** — `git status --porcelain | wc -l`
2. **Unpushed commits** — `git log --oneline origin/main..HEAD`
3. **Unpulled commits** — `git log --oneline HEAD..origin/main`

### Handling unreachable hosts:
- Script continues checking other hosts if one is unreachable
- Unreachable hosts are marked with `ERROR: SSH unreachable`
- Feynman is known to be unreachable from Hopper (different subnet)

## Health Check Script

**Location:** `_tools/health-check.py`
**Runs via:** `combined-health-check.sh` (called by drift check service)
**Output:** `_runtime/health-report-{date}.json`

### What it checks per host:
1. **Reachability** — SSH connection test
2. **System uptime** — `uptime -p`
3. **Disk usage** — `df -h /`
4. **Memory usage** — `free -h | grep Mem`
5. **AIKB repo status** — uncommitted file count

## Combined Runner

**Location:** `_tools/combined-health-check.sh`
**Runs via:** `aikb-drift-check.service` (systemd oneshot)

Executes both drift detection and health check in sequence.
Logs output to systemd journal for easy debugging.

## Migration Notes

- **Newton cron job** `home-lab-daily-health` paused 2026-04-19
- **Hopper systemd timer** enabled 2026-04-19
- All scheduled tasks now run on Hopper (always-on, stable connectivity)

## Future Improvements

1. Add Feynman reachability via VPN or subnet routing
2. Add alerting when drift detected (notify user)
3. Extend health checks to include service status (Docker, Ollama, etc.)
4. Add historical trend tracking for disk/memory usage
