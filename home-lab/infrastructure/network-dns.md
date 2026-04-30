---
tags: [dns, ssl, certificates, nginx, pi-hole, tailscale, truenas, proxy-hosts, home.timmcg.net, npm, reverse-proxy, wildcard-cert, udm-pro]
hosts: [truenas, pihole, pihole2, udm-pro]
services: [nginx-proxy-manager, pi-hole, tailscale]
expiry:
  wildcard_cert_home_timmcg_net: "2026-07-13"
last_updated: 2026-04-25
---

# Network & DNS Infrastructure

**Last Updated:** 2026-04-24
**Summary:** Home network uses UDM Pro as gateway with dual Pi-hole DNS for ad-blocking and local resolution under `home.timmcg.net`. Nginx Proxy Manager on TrueNAS handles reverse proxying and SSL.

---

## Overview
- **Gateway:** UDM Pro (10.10.0.1)
- **Primary DNS:** Pi-hole on TrueNAS (10.10.0.2) — web UI: `http://10.10.10.10:20720/` — API: `http://10.10.10.10:20720/api/`
- **Secondary DNS:** Pi-hole on Raspberry Pi (10.10.0.22) — web UI: `http://10.10.0.22/` — API: `http://10.10.0.22/api/`
- **Reverse Proxy:** Nginx Proxy Manager on TrueNAS (10.10.10.10)
- **Remote Access:** Tailscale (Mesh VPN). Primary node runs as a container on TrueNAS. MagicDNS enabled for `home.timmcg.net`.

## DNS Flow
1. UDM Pro DHCP hands out 10.10.0.2 and 10.10.0.22 to clients.
2. Pi-holes handle ad-blocking and local resolution for `home.timmcg.net`.
3. Pi-holes use Conditional Forwarding to UDM Pro for unknown local hostnames.
4. Pi-holes use Cloudflare (1.1.1.1) for upstream resolution.

**⚠️ Warning on Sync:** Primary (`truenas`) and Secondary (`pihole2`) must be updated in tandem. Manual edits to `pihole.toml` on one will not propagate to the other without running the `ansible/ai/update_pihole_dns.yml` playbook.

## Architectural Patterns & Lessons Learned

### The "Mega-IP" Pattern (10.10.10.10)
Most services in the lab share `10.10.10.10`. This IP represents the **Nginx Proxy Manager (NPM)** instance running on TrueNAS.
- **When to use:** For any web-based service requiring SSL termination or Authentik SSO.
- **When NOT to use:** For IoT devices or specialized hardware (like OpenSoak) where background API clients cannot handle Authentik redirects.
- **AI Agent Guidance:** If a service has a dedicated physical host (e.g., 10.10.169.191), verify if its DNS points to the Mega-IP or the Host-IP. If it points to the Mega-IP, it is being proxied through NPM/Authentik.

### Failure Mode: HTML-as-JSON Redirects
When an API-only client (Android widgets, Python scripts) hits a proxied endpoint protected by Authentik, it will receive an HTML login page instead of JSON. 
- **Symptoms:** "JSON Parse Error", "Unexpected Character '<'", or silent refresh failures.
- **Solution:** Bypass the proxy by pointing local DNS directly to the Service Host-IP, or configure an Authentik unauthenticated path (if supported by the service Nginx config).

### Persistent Caching on Android
Android devices (NVIDIA Shield, Pixel) aggressively cache DNS and TCP connections.
- **Action:** After changing local DNS for an Android-based client, you **must** force-stop the application to ensure it drops stale connections and performs a fresh lookup.

## Pi-hole v6 — Config & Sync Strategy
- **Golden Source:** `ansible/ai/files/pihole.toml` (Git repository)
- **Local Config (Primary):** `/mnt/.ix-apps/app_mounts/pihole/config/pihole.toml` on TrueNAS
- **Local Config (Secondary):** `/etc/pihole/pihole.toml` on pihole2
- **Sync Playbook:** `ansible/ai/sync_pihole_source.yml`
- **Automation:** Triggered via GitHub Webhook to Ansible Semaphore API on pushes to the `ansible` repo.

**Workflow for DNS changes:**
1. Edit `ansible/ai/files/pihole.toml` in the `ansible` repository.
2. Commit and push to GitHub.
3. Semaphore automatically runs the sync playbook to update both Pi-holes and reload DNS.

**⚠️ Warning on Manual Edits:** Do not edit `pihole.toml` directly on the Pi-holes or via the Web UI for permanent changes. They will be overwritten by the next Git sync. Use the Web UI only for temporary testing.

## SSL Certificates (NPM)
- **Wildcard cert:** `*.home.timmcg.net` — NPM cert ID 1, expires 2026-07-13
- All proxy hosts use `certificate_id: 1`, `ssl_forced: 1`
- Preferred baseline for browser-facing NPM hosts is `Force SSL` enabled plus `HTTP/2 Support` enabled unless a service has a documented exception.
- Verified 2026-03-07: the active NPM proxy/redirection host set was bulk-aligned to that baseline (`Force SSL` + `HTTP/2`), and the database state was reconciled with the generated nginx config so later UI edits should not silently revert the changes.
- If nginx reloads emit `protocol options redefined` warnings on proxy host files, treat them as configuration-hygiene warnings rather than an automatic rollback signal when `nginx -t` still passes.

### NPM Advanced Config — Authentik Snippet Warning

**Do not `include /data/nginx/custom/authentik_snippet.conf` inside a `location` block.**

The snippet contains a named location (`@goauthentik_proxy_redirect`). Nginx requires named locations at server block level only — nesting one inside a `location { }` causes a fatal config error (`nginx: [emerg] named location "..." can be on the server level only`). When NPM encounters this, it silently skips generating the `.conf` file for that proxy host — the site goes dark with an SSL "unrecognized name" error but NPM's UI still shows the host as "Enabled".

**Correct pattern** for Authentik-protected proxy hosts in `advanced_config`:

```nginx
# --- server-level (outside all location blocks) ---
location @goauthentik_proxy_redirect {
    return 307 https://auth.home.timmcg.net/outpost.goauthentik.io/start?rd=$scheme://$http_host$request_uri;
}

location /outpost.goauthentik.io {
    auth_request off;
    proxy_pass http://10.10.10.10:9000/outpost.goauthentik.io;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Server $host;
    proxy_set_header X-Original-URL $scheme://$http_host$request_uri;
    proxy_set_header Content-Length "";
    proxy_pass_request_body off;
}

# --- inside location / (auth directives only, no include of the snippet) ---
location / {
    proxy_buffers 8 16k;
    proxy_buffer_size 32k;
    auth_request /outpost.goauthentik.io/auth/nginx;
    error_page 401 = @goauthentik_proxy_redirect;
    auth_request_set $auth_cookie $upstream_http_set_cookie;
    add_header Set-Cookie $auth_cookie;
    auth_request_set $authentik_username $upstream_http_x_authentik_username;
    auth_request_set $authentik_groups $upstream_http_x_authentik_groups;
    auth_request_set $authentik_email $upstream_http_x_authentik_email;
    auth_request_set $authentik_name $upstream_http_x_authentik_name;
    proxy_set_header X-authentik-username $authentik_username;
    proxy_set_header X-authentik-groups $authentik_groups;
    proxy_set_header X-authentik-email $authentik_email;
    proxy_set_header X-authentik-name $authentik_name;
    proxy_pass http://<upstream_host>:<port>;
}
```

**Incident:** 2026-04-19 — `ai.home.timmcg.net` (NPM host ID 32) went offline after Gemini added `draw.home.timmcg.net` (host ID 42), which triggered an nginx reload that hit this latent bug in host 32's advanced_config. Fixed by updating host 32 via the NPM API with the corrected inline pattern above.

**Incident:** 2026-04-22 — `ai.home.timmcg.net` browser traffic reported `ERR_TOO_MANY_REDIRECTS`. Root cause was identified as a provider mismatch between the global domain auth and single-application providers.
- **Permanent Solution:** The shared `/data/nginx/custom/authentik_snippet.conf` was updated to use `$http_host` in the `@goauthentik_proxy_redirect` block. This ensures that Nginx always redirects the user to the outpost on the *current* domain, which triggers the correct Authentik provider flow and sets the domain-specific cookie.
- **Automation Fix:** The `ansible/ai/configure_npm_proxy.yml` playbook was updated to explicitly include the shared snippet in `advanced_config`, preventing future automated runs from wiping the authentication configuration.

```nginx
# New robust redirect pattern in shared snippet:
location @goauthentik_proxy_redirect {
    return 307 https://$http_host/outpost.goauthentik.io/start?rd=$scheme://$http_host$request_uri;
}
```

**Diagnosis shortcut:** If a host has `nginx_online: false` in NPM meta and its `.conf` is missing from `/data/nginx/proxy_host/`, check if its `advanced_config` has a named location nested inside a `location { }` block.

## NPM Proxy Hosts — Direct DB Manipulation
- NPM SQLite DB: `/mnt/.ix-apps/app_mounts/nginx-proxy-manager/data/database.sqlite`
- Nginx confs: `/mnt/.ix-apps/app_mounts/nginx-proxy-manager/data/nginx/proxy_host/<id>.conf`
- Logs dir: `/mnt/.ix-apps/app_mounts/nginx-proxy-manager/data/logs/`
- When inserting directly (no UI access), must ALSO:
  1. Write the `.conf` file for the new host ID (copy from existing, update fields)
  2. `touch` and `chown apps:apps` the access/error log files
  3. `sudo docker restart ix-nginx-proxy-manager-npm-1` to reload
- Admin email: timmcg@gmail.com — password in Vaultwarden
- **DB write access:** svc_gemini cannot write directly — use `sudo docker exec ix-nginx-proxy-manager-npm-1 node -e "..."` with knex, or the NPM REST API.

## DNS → NPM → Service Map (all → 10.10.10.10)

| Hostname | NPM ID | Port | Service |
|----------|--------|------|---------|
| plex.home.timmcg.net | — | 32400 | Plex |
| tautulli.home.timmcg.net | — | 30047 | Tautulli |
| jellyfin.home.timmcg.net | — | 30013 | Jellyfin |
| overseerr.home.timmcg.net | — | 30042 | Overseerr |
| sonarr.home.timmcg.net | — | 8989 | Sonarr |
| radarr.home.timmcg.net | — | 7878 | Radarr |
| prowlarr.home.timmcg.net | — | 9696 | Prowlarr |
| sab.home.timmcg.net | — | 30055 | SABnzbd |
| transmission.home.timmcg.net | — | 30096 | Transmission |
| cloud.home.timmcg.net | — | 30027 | Nextcloud |
| nc.home.timmcg.net | 27 | 30027 | Nextcloud (alias) |
| vault.home.timmcg.net | 24 | 30080 | Vaultwarden |
| ansible.home.timmcg.net | 23 | 30052 | Ansible Semaphore |
| memory.home.timmcg.net | 38 | 8077 | AIKB Memory Core |
| idrac.home.timmcg.net | 18 | 443 (https) | iDRAC management |
| grafana.home.timmcg.net | — | 30037 | Grafana |
| prometheus.home.timmcg.net | — | 30028 | Prometheus |
| loki.home.timmcg.net | 26 | 3100 | Grafana Loki (monitoring stack) |
| npm.home.timmcg.net | — | 30020 (admin) | Nginx Proxy Manager |
| portainer.home.timmcg.net | — | 9443 | Portainer |
| dockge.home.timmcg.net | — | 31014 | Dockge |
| nyquist.home.timmcg.net | 39 | 20211 | NetAlertX Security Scanner |
| hermes.home.timmcg.net | 45 | 9119 | Hermes Agent Dashboard (Turing) |
| ops.home.timmcg.net | 49 | 3001 | AI Hub / Ops Console (Turing) |
| shell.home.timmcg.net | 50 | 8085 | OpenShell / Nemoclaw (Turing) |
| fosgail.home.timmcg.net / pdf.home.timmcg.net | 48 | 30090 | Fosgail (Stirling PDF fork, Make Fillable feature) |
| docs.home.timmcg.net | 51 | 18000 | MkDocs + Material (homelab docs site) |
| opensoak.home.timmcg.net | 29 (legacy) | — | Hot Tub Controller (now direct DNS to Pi at 10.10.169.191) |
| opensoak (shortname) | R21 | — | Redirect to FQDN |

## DNS — Direct (no NPM proxy)

| Hostname | IP | Service |
|----------|----|---------| 
| baird.home.timmcg.net | 10.10.199.178 | CECmate office TV CEC controller (ESP32) |
| baird (shortname) | 10.10.199.178 | alias |

> Note: `loki.home.timmcg.net` is assigned to the Grafana Loki monitoring service on TrueNAS (not a physical server — the old loki desktop at 10.10.10.151 is decommissioned).
