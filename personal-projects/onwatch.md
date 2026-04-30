---
tags: [onwatch, distributed-quota, monitoring, agents, golang, bridge]
last_updated: 2026-04-22 (verified)
---

# onWatch
**Last Updated:** 2026-04-22
**Summary:** Free, open-source AI API quota monitoring. Deployed as a distributed "Global Runway" sensor network across the homelab to track token usage and API limits.

## Architecture

**Aggregator Node (Turing)**
- **Role:** Central Dashboard and API Poller.
- **URL:** `https://onwatch.home.timmcg.net` (Proxied via NPM/Authentik)
- **Ingestion:** Reads distributed telemetry files from `AIKB/_runtime/onwatch/*.jsonl` via `~/.onwatch/api-integrations/` symlinks.
- **Credentials:** `admin` / `onwatch-compare-2026` (Note: Authentik auto-login is enabled via patched middleware. NPM proxy host 46 `location /` block passes `X-authentik-username` header — verified working 2026-04-22).
- **Claude Card Fix:** Turing's Anthropic agent gets 429 at 100% quota. A bridge script (`~/code/scripts/sync_anthropic_snapshots.py`) runs every 5 min to populate `anthropic_snapshots` from `api_integration_usage_events`. Cron: `*/5 * * * * python3 ~/code/scripts/sync_anthropic_snapshots.py # ANTHROPIC_SNAPSHOT_SYNC`
- **AIKB Pull Cron:** `*/5 * * * * cd ~/code/AIKB && git pull origin main --quiet # AIKB_PULL` (keeps jsonl files fresh)
- **Symlink Note:** `~/.onwatch/api-integrations/` symlinks must match exact filename case. Newton's file is `Newton.jsonl` (capital N) — symlink must point to capital N path.

**Sensor Nodes (Feynman, Newton, Tesla)**
- **Role:** Local Edge monitoring.
- **Action:** Runs local `onWatch` instance to track CLI sessions (e.g. Claude Code via statusline hooks, Cursor SQLite, browser cookies).
- **Bridge Script:** `~/code/scripts/onwatch-aikb-bridge.py` runs every 5 minutes via cron.
  - Queries local metrics.
  - Generates a quota snapshot event in `AIKB/_runtime/events/<date>.ndjson` for Agent Self-Awareness.
  - Updates machine state in `AIKB/_runtime/onwatch/<hostname>.json`.
  - Appends to machine telemetry stream `AIKB/_runtime/onwatch/<hostname>.jsonl` for Turing ingestion.

## Setup Instructions for New Machines

1. **Install onWatch**:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/onllm-dev/onwatch/main/install.sh > install.sh
   sed -i '' 's/^[[:space:]]*interactive_setup$/#interactive_setup/g' install.sh || sed -i 's/^[[:space:]]*interactive_setup$/#interactive_setup/g' install.sh
   chmod +x install.sh
   mkdir -p ~/.onwatch
   echo -e 'ONWATCH_ADMIN_PASS=your-password\nONWATCH_PORT=9211' > ~/.onwatch/.env
   ./install.sh
   ```
2. **Deploy Bridge Script**:
   Copy `onwatch-aikb-bridge.py` to `~/code/scripts/`
3. **Configure Cron**:
   ```bash
   (crontab -l 2>/dev/null | grep -v onwatch-aikb-bridge.py; echo "*/5 * * * * ~/code/scripts/onwatch-aikb-bridge.py") | crontab -
   ```