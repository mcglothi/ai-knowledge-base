---
tags: [access, quick-reference, ssh, api, urls, credentials, truenas, pihole, grafana, npm, vaultwarden, semaphore, authentik, headscale, portainer]
hosts: [truenas, babbage, farnsworth, pihole, pihole2, opensoak, tesla, feynman]
last_updated: 2026-03-07
---

# Home Lab — Access Quick Reference

**Last Updated:** 2026-03-07
**Summary:** Single-file quick reference for SSH targets, service URLs, and credential locations in Vaultwarden.
**Purpose:** Single-read lookup for URLs, ports, SSH targets, and Vaultwarden credential paths. No hunting across multiple files.

---

## SSH Hosts

| Host | IP | SSH Command | Key (agent use) |
|------|----|-------------|-----------------|
| newton (Workstation) | `newton10g` | `ssh mcglothi@newton10g` | `~/.ssh/id_rsa` |
| newton (Fallback) | `newton` | `ssh mcglothi@newton` | `~/.ssh/id_rsa` |
| TrueNAS (babbage) | `10.10.10.10` | `ssh svc_gemini@10.10.10.10` | `PAT/SSH/svc_gemini` |
| turing (AI Hub) | `10.10.10.50` | `ssh svc_gemini@10.10.10.50` | `PAT/SSH/svc_gemini` |
| farnsworth | `10.10.10.100` | `ssh svc_gemini@10.10.10.100` | `PAT/SSH/svc_gemini` |
| pihole2 (Pi) | `10.10.0.22` | `ssh svc_gemini@10.10.0.22` | `PAT/SSH/svc_gemini` |
| opensoak (Pi) | `10.10.169.191` | `ssh svc_gemini@10.10.169.191` | `PAT/SSH/svc_gemini` |
| Headscale (GCP) | `35.226.60.95` | `gcloud compute ssh headscale --project=inbound-entity-239819 --zone=us-central1-a` | gcloud ADC |

> Agent accounts (`svc_claude`, `svc_gemini`, `svc_codex`) are deployed on `babbage` and `turing` (verified 2026-04-10). Each agent MUST use its own key and account for all SSH actions. Ansible jobs run targeting `svc_ansible` using the dedicated `svc_ansible` key. Primary Pi-hole runs as a TrueNAS container; SSH to its service IP resolves to host context.

---

## Web UIs

| Service | URL | Direct IP:Port | VW Credential |
|---------|-----|----------------|---------------|
| **TrueNAS** | `https://nas.home.timmcg.net` | `https://10.10.10.10` | `PAT/TrueNAS/svc_claude` (API key) |
| **Nginx Proxy Manager** | `https://npm.home.timmcg.net` | `http://10.10.10.10:30020` | `PAT/NPM/svc_claude` |
| **Vaultwarden** | `https://vault.home.timmcg.net` | `http://10.10.10.10:30080` | `PAT/Vaultwarden/Admin` (admin token) |
| **Grafana** | `https://grafana.home.timmcg.net` | `http://10.10.10.10:30037` | `PAT/Grafana/svc_claude` |
| **Prometheus** | `https://prometheus.home.timmcg.net` | `http://10.10.10.10:30028` | — (no auth) |
| **Authentik** | `https://auth.home.timmcg.net` | `http://10.10.10.10` | `PAT/Authentik/svc_claude` |
| **Jellyfin** | `https://jellyfin.home.timmcg.net` | `http://10.10.10.10:30013` | — |
| **Ansible Semaphore** | `https://ansible.home.timmcg.net` | `http://10.10.10.10:30052` | `PAT/Semaphore/svc_claude` |
| **iDRAC** | `https://idrac.home.timmcg.net` | `https://10.10.10.1` | — |
| **Pi-hole 1** (TrueNAS) | — | `http://10.10.10.10:20720/` | `PAT/Pi-hole/App Password Primary` |
| **Pi-hole 2** (Pi) | — | `http://10.10.0.22/` | `PAT/Pi-hole/App Password Secondary` |
| **Portainer** | `https://portainer.home.timmcg.net` | `https://10.10.10.10:9443` | — |
| **Nextcloud** | `https://cloud.home.timmcg.net` | `http://10.10.10.10:30027` | — |
| **Home Assistant** | `https://lovelace.home.timmcg.net` | `http://10.10.10.10:8123` | HA native auth — `PAT/HomeAssistant/Homepage Token` (long-lived API token) |
| **OpenSoak** | `https://opensoak.home.timmcg.net` | `http://10.10.169.191:5173` | Authentik SSO |
| **Headscale** | `https://hs.timmcg.net` | — | — |
| **Nyquist** | `https://nyquist.home.timmcg.net` | `http://10.10.10.10:20211` | — (Token in App Settings) |
| **Homelab Docs** | `https://docs.home.timmcg.net` | `http://10.10.10.10:18000` | Authentik SSO |

---

## APIs

| Service | Endpoint | Auth method | VW Credential |
|---------|----------|-------------|---------------|
| **TrueNAS** | `https://nas.home.timmcg.net/api/v2.0/` | `Authorization: Bearer <token>` | `PAT/TrueNAS/svc_claude` |
| **Nyquist** | `https://nyquist.home.timmcg.net/server/` | `?token=<API_TOKEN>` | — (Token in App Settings) |
| **Pi-hole 1** | `http://10.10.10.10:20720/api/` | POST `/api/auth` `{"password":"..."}` → use `sid` | `PAT/Pi-hole/App Password Primary` |
| **Pi-hole 2** | `http://10.10.0.22/api/` | POST `/api/auth` `{"password":"..."}` → use `sid` | `PAT/Pi-hole/App Password Secondary` |
| **Grafana** | `https://grafana.home.timmcg.net/api/` | `Authorization: Bearer <token>` | `PAT/Grafana/svc_claude` |
| **Authentik** | `https://auth.home.timmcg.net/api/v3/` | `Authorization: Bearer <token>` | `PAT/Authentik/svc_claude` |
| **Jellyfin** | `https://jellyfin.home.timmcg.net` | `http://10.10.10.10:30013` | — |
| **Semaphore** | `https://ansible.home.timmcg.net/api/` | `Authorization: Bearer <token>` | `PAT/Semaphore/svc_claude` |
| **Cloudflare** | `https://api.cloudflare.com/client/v4/` | `X-Auth-Email` + `X-Auth-Key` headers | `PAT/Cloudflare/API Token` |
| **Headscale** | SSH to GCP → `sudo headscale ...` | gcloud SSH | — |

### Pi-hole API auth snippet
```bash
BW_SESSION=$(cat ~/.bw_session)
PH_PASS=$(bw get password "PAT/Pi-hole/App Password Primary" --session "$BW_SESSION")
SID=$(curl -s -X POST http://10.10.10.10:20720/api/auth \
  -H "Content-Type: application/json" \
  -d "{\"password\":\"$PH_PASS\"}" | python3 -c "import sys,json; print(json.load(sys.stdin)['session']['sid'])")
# Use: curl -H "X-FTL-SID: $SID" http://10.10.10.10:20720/api/stats/summary
```

---

## Vaultwarden — Key Item Names

| Item | What it is |
|------|-----------|
| `PAT/SSH/svc_claude` | ed25519 private key for all homelab SSH |
| `PAT/SSH/svc_gemini` | ed25519 private key for all homelab SSH |
| `PAT/SSH/svc_codex` | ed25519 private key for all homelab SSH |
| `PAT/SSH/svc_ansible` | Dedicated ed25519 key for Ansible jobs |
| `PAT/TrueNAS/svc_claude` | TrueNAS API key |
| `PAT/TrueNAS/svc_gemini` | TrueNAS API key |
| `PAT/Grafana/svc_claude` | Grafana admin service token |
| `PAT/Authentik/svc_claude` | Authentik API token |
| `PAT/Semaphore/svc_claude` | Ansible Semaphore user token |
| `PAT/NPM/svc_claude` | NPM admin login (user/pass) |
| `PAT/GCP/svc_claude` | GCP service account JSON |
| `PAT/Cloudflare/API Token` | Global API key (use X-Auth-Key header, not Bearer) |
| `PAT/Vaultwarden/Admin` | Vaultwarden admin token |
| `PAT/Pi-hole/App Password Primary` | Pi-hole 1 + Pi-hole 2 admin password |
| `PAT/Headscale/PreAuth Key (tim)` | Reusable pre-auth key, auto-renewed every 20h |
| `PAT/GitHub/AIKB MCP Token` | GitHub PAT for AIKB MCP server |

---

## Retrieve any credential (one-liner)
```bash
bw get password "PAT/<Service>/<Identity>" --session "$(cat ~/.bw_session)"
```
> If `~/.bw_session` is missing or stale, user must run `bwu` first — agents cannot unlock interactively.

---

## See Also
- [`network-dns.md`](network-dns.md) — full NPM proxy host map, Pi-hole config details
- [`servers.md`](servers.md) — host inventory, svc_ansible sudo setup
- [`../security/service-accounts.md`](../security/service-accounts.md) — full credentials registry

## Notes

- `idrac.home.timmcg.net` is proxied through NPM to `https://10.10.10.1` with `Force SSL` enabled; if the entry breaks, confirm the forward target is the bare host/IP and not a path like `/login.html`.
