---
context: personal-homelab
tags: [home-assistant, homeassistant, zwave, z-wave, zigbee, hubz, husbzb-1, smart-home, babbage, truenas, docker, dockge, lovelace, zwave-js-ui, zwavejs, authentik, sso]
hosts: [babbage]
last_updated: 2026-04-29
---

# Home Assistant

**Last Updated:** 2026-04-29
**Summary:** Deployment and operational details for Home Assistant, including USB radio mapping, Z-Wave setup, and Authentik SSO integration.

## Overview
Home Assistant Container (Docker) running on babbage (TrueNAS 24.10.2.2). Managed via Dockge.

- **Web UI (proxied):** https://lovelace.home.timmcg.net
- **Web UI (direct):** http://10.10.10.10:8123
- **Config dataset:** `Containers/HomeAssistant` → `/mnt/Containers/HomeAssistant`
- **Compose stack:** `/mnt/.ix-apps/app_mounts/dockge/stacks/homeassistant/compose.yaml`
- **Image:** `ghcr.io/home-assistant/home-assistant:stable`
- **DNS name:** `lovelace` — Ada Lovelace, first programmer and automation pioneer

## Z-Wave / Zigbee USB Device

**GoControl HUSBZB-1** — Silicon Labs CP210x combo Z-Wave + Zigbee USB stick.

| Interface | Host device | Container device | Protocol | Stable by-id path |
|-----------|-------------|------------------|----------|-------------------|
| if00 | `/dev/ttyUSB0` | `/dev/ttyUSB0` | **Z-Wave** | `usb-Silicon_Labs_HubZ_Smart_Home_Controller_81300404-if00-port0` |
| if01 | `/dev/ttyUSB1` | `/dev/ttyUSB1` | Zigbee | `usb-Silicon_Labs_HubZ_Smart_Home_Controller_81300404-if01-port0` |

- Serial: `81300404`
- Driver: `cp210x`
- Permissions: `crw-rw---- root dialout (GID 20)`
- Container uses `group_add: ["20"]` (dialout) — no privileged mode needed

## Compose File

```yaml
services:
  homeassistant:
    image: ghcr.io/home-assistant/home-assistant:stable
    container_name: homeassistant
    restart: unless-stopped
    network_mode: host
    privileged: false
    group_add:
      - "20"  # dialout — access to /dev/ttyUSB* without privileged mode
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0  # HUSBZB-1 Z-Wave (Silicon Labs HubZ if00)
      - /dev/ttyUSB1:/dev/ttyUSB1  # HUSBZB-1 Zigbee (Silicon Labs HubZ if01)
    volumes:
      - /mnt/Containers/HomeAssistant:/config
    environment:
      - TZ=America/Los_Angeles
```

## Reverse Proxy Configuration

NPM proxy host id=31. `lovelace.home.timmcg.net` → `http://10.10.10.10:8123`.
- SSL: wildcard cert (npm-1 / `*.home.timmcg.net`)
- WebSocket upgrade: **enabled** (required — HA uses websockets heavily)
- HTTP/2: enabled
- SSL forced: yes
- Advanced config: `include /data/nginx/custom/authentik_snippet.conf;`

**Critical — HA must trust the NPM proxy.** NPM forwards from Docker network `172.16.3.2`. Without proxy trust config, HA returns `400 Bad Request`. The following is in `/mnt/Containers/HomeAssistant/configuration.yaml`:

```yaml
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 172.16.0.0/12   # Docker network (NPM forwards from 172.16.3.2)
    - 127.0.0.1
    - 10.10.10.10
```

## Authentik SSO Integration (Added 2026-04-29)

`lovelace.home.timmcg.net` is fully gated by Authentik via NPM forward auth. After Authentik login, HA auto-logs in as Tim with no second prompt.

**Architecture:**
- NPM snippet (`authentik_snippet.conf`) gates all browser requests via `auth_request`
- Authentik uses the Home Lab Global provider (pk=23, `forward_domain`, cookie `.home.timmcg.net`)
- HA `trusted_networks` + `trusted_users` auto-login when request comes from LAN/NPM range
- WebSocket traffic passes through unimpeded (Authentik cookie valid by time WS connects)

**Authentik app:** slug=`lovelace`, group=`Home Automation`, provider=None (portal shortcut; enforcement is at NPM layer)

**HA configuration.yaml — full auth section:**

```yaml
homeassistant:
  external_url: https://lovelace.home.timmcg.net
  auth_providers:
    - type: trusted_networks
      trusted_networks:
        - 172.16.0.0/12   # NPM Docker bridge (proxy source IP)
        - 10.10.0.0/16    # Home LAN
        - 127.0.0.1
      trusted_users:
        172.16.0.0/12:
          - 489dd5aeee9f497990dbfe5a1c58d1d1
        10.10.0.0/16:
          - 489dd5aeee9f497990dbfe5a1c58d1d1
      allow_bypass_login: true
    - type: homeassistant
```

**HA user:** Tim / ID `489dd5aeee9f497990dbfe5a1c58d1d1` / credential username `mcglothi`

**Companion app:** Use direct URL `http://10.10.10.10:8123` (bypasses NPM/Authentik, uses HA long-lived token auth). Do NOT use the FQDN for the companion app.

### Lessons Learned — Authentik SSO

- **`trusted_users` requires no-dash hex UUID** — HA's `cv.uuid4_hex` validator checks `result.hex == value`, so hyphenated format (`489dd5ae-ee9f-4979-90db-fe5a1c58d1d1`) fails even though Python's `uuid.UUID()` accepts it. Must use raw hex: `489dd5aeee9f497990dbfe5a1c58d1d1`
- **`trusted_networks` uses real client IP via X-Forwarded-For** — NPM forwards the browser's IP, not its own. Must include the actual LAN range (`10.10.0.0/16`), not just NPM's Docker IP, to cover all home devices
- **`external_url` required** — Without it, HA's auth callback validation fails with "Invalid redirect URI" because HA can't validate the redirect matches its own URL
- **`auth_request` does NOT apply to WebSocket upgrades** — Authentik cookie is set before WS connects (page load triggers auth), so HA WS works fine with the snippet in place
- **`trusted_users` UUID error cascades to `http:` config** — When `homeassistant:` section fails voluptuous validation, HA falls back to defaults including for `trusted_proxies`, causing "Received X-Forwarded-For from untrusted proxy" errors

## Known Issues

### mDNS / Zeroconf — avahi conflict (RESOLVED)
`avahi-daemon` on the TrueNAS host was configured with `disallow-other-stacks=yes`, blocking HA from binding to port 5353. This caused a cascade: HA's DNS resolver depends on zeroconf, so when zeroconf failed, all HTTP client sessions inside HA broke — resulting in **"Failed to save: Unknown command"** during onboarding.

**Fix applied:** Set `disallow-other-stacks=no` in `/etc/avahi/avahi-daemon.conf`. avahi-daemon stopped during the reload; HA now holds port 5353. If avahi restarts in the future, both should coexist with the corrected config.

**Key lesson:** The zeroconf failure is NOT cosmetic in HA — it cascades to break internal HTTP sessions, which breaks WebSocket API commands (including onboarding save). Always fix avahi coexistence before attempting HA onboarding on a TrueNAS host.

## Z-Wave JS UI

HA Container has no add-on store. Z-Wave is handled by a separate **Z-Wave JS UI** Dockge stack that exposes a WebSocket server for HA to connect to.

- **Web UI:** `http://10.10.10.10:8091`
- **HA WebSocket URL:** `ws://localhost:3001`
- **Config dataset:** `Containers/ZwaveJS` → `/mnt/Containers/ZwaveJS`
- **Compose stack:** `/mnt/.ix-apps/app_mounts/dockge/stacks/zwavejs/compose.yaml`

```yaml
services:
  zwave-js-ui:
    image: zwavejs/zwave-js-ui:latest
    container_name: zwave-js-ui
    restart: unless-stopped
    network_mode: host
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0
    volumes:
      - /mnt/Containers/ZwaveJS:/usr/src/app/store
    environment:
      - TZ=America/Los_Angeles
      - ZWAVEJS_EXTERNAL_CONFIG=/usr/src/app/store/.config-db
```

**Critical settings** (`/mnt/Containers/ZwaveJS/settings.json` → `zwave` section):
- `serverEnabled: true` — must be explicitly enabled; defaults to `false`
- `serverPort: 3001` — **NOT 3000**. Port 3000 is occupied by Homepage (`ix-homepage-homepage-1`), which also uses `network_mode: host`. Using 3001 avoids the conflict.

To edit settings: `sudo python3` with `json.load/dump` on the file (owned by root), then `sudo docker restart zwave-js-ui`.

## Setting Up Z-Wave in HA

1. Deploy Z-Wave JS UI stack (see above) and confirm port 3001 is listening: `sudo ss -tlnp | grep 3001`
2. In HA: **Settings → Devices & Services → Add Integration → Z-Wave**
3. When prompted for WebSocket URL, enter: `ws://localhost:3001`
4. HA connects to Z-Wave JS UI and discovers all paired devices

For Zigbee (optional — the HUSBZB-1 supports both):
- Add **ZHA** integration and point it at `/dev/ttyUSB1`
- Or deploy **Zigbee2MQTT** as a separate Dockge stack

## Homepage Widget

The Homepage service card is in place at `home.timmcg.net` under the **Home Automation** group.
The HA widget requires a long-lived access token (generated post-onboarding):

1. HA → Profile → Long-Lived Access Tokens → Create Token
2. Edit `/mnt/Containers/Homepage/services.yaml` — uncomment the widget block and paste the token

```yaml
        widget:
          type: homeassistant
          url: http://10.10.10.10:8123
          key: <long-lived-access-token>
```

## Lessons Learned from Deployment

### Pi-hole v6 custom DNS API
- Endpoint changed from `/api/customdns` → `/api/config/dns/hosts` (config PATCH API)
- Auth: `POST /api/auth {"password": "..."}` → returns `sid` in `session.sid`
- Use `X-FTL-SID` header (not `Authorization: Bearer`)
- PATCH body must wrap in `{"config": {...}}` — not just `{"dns": {...}}`
- Shell special characters in passwords (e.g. `!`) break `curl -d` — always use Python for Pi-hole API calls
- Pi-hole v6 PATCH replaces the entire `hosts` array — read first, append, then write back

### NPM API
- Admin UI port: 30020 (mapped from container port 81). Proxy ports: 80/443.
- Correct API base: `http://10.10.10.10:30020` (not port 443)
- Proxy host endpoint: **`/api/nginx/proxy-hosts`** (NOT `/api/proxy-hosts`)
- Direct SQLite writes are NOT picked up by NPM's in-memory state — must use the API
- NPM JWT format: RS256, payload must include `iss:"api"`, `attrs:{"id": <user_id>}`, `scope:["user"]`
- Private key is at `/mnt/.ix-apps/app_mounts/nginx-proxy-manager/data/keys.json` → `key` field
- Mint JWT via Python `cryptography` library + PKCS1v15 + SHA256
- WebSocket upgrade (`allow_websocket_upgrade: true`) is required for Home Assistant

### HA Reverse Proxy
- HA returns `400 Bad Request` when accessed via a reverse proxy without trusted_proxies config
- NPM Docker network is `172.16.3.2` — add `172.16.0.0/12` to trusted_proxies in `configuration.yaml`
- Config file is at `/mnt/Containers/HomeAssistant/configuration.yaml`
- Restart HA after editing: `sudo docker restart homeassistant`
- Config file is owned by a container user — need `sudo tee -a` to append from the host

### Z-Wave JS UI — WS server disabled by default
- HA Container has no add-on store; Z-Wave JS UI must be deployed as a separate Dockge stack
- `serverEnabled` in `zwave` section of `settings.json` defaults to `false` — the WebSocket server HA needs will not start
- Port 3000 (default `serverPort`) is occupied by Homepage (`ix-homepage-homepage-1`), which also uses `network_mode: host` — change to 3001
- After editing settings.json, `sudo docker restart zwave-js-ui` is required to pick up the changes
- Verify with `sudo ss -tlnp | grep 3001` before attempting HA connection
- HA integration URL: `ws://localhost:3001` (both containers in host network mode, so localhost works)

### Bitwarden CLI (`bw`) — resolved on tesla (2026-03-01)
- Node.js TCP connections to 10.10.x.x now work — verified with `net.createConnection` to LAN host
- Previous EHOSTUNREACH issue resolved (root cause unknown, may have cleared with a system update or Tailscale change)
- `bw` CLI can now reach `vault.home.timmcg.net` programmatically
