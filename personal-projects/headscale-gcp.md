---
context: personal
tags: [headscale, vpn, gcp, tailscale, networking, derp, pixel, tesla, truenas]
status: active
last_updated: 2026-04-03
---

# Headscale on GCP

**Last Updated:** 2026-04-03
**Summary:** Self-hosting Headscale (Tailscale-compatible coordination server) on GCP to bypass corporate/network blocks and maintain private mesh VPN control.

---

## Overview

Tailscale is currently blocked on some target networks. Hosting a private Headscale instance on GCP allows for:
1. **Domain bypassing:** Using `hs.timmcg.net` instead of `tailscale.com`.
2. **DERP Relay:** Using the GCP node as an HTTPS/TLS relay (Port 443) to encapsulate VPN traffic in standard web traffic.
3. **Control:** Full ownership of the coordination server and node registration.

## Access

| Item | Value |
|------|-------|
| **Server URL** | `https://hs.timmcg.net` |
| **Alias** | `headscale.timmcg.net` (same IP, both DNS Only) |
| **GCP Project** | `inbound-entity-239819` (home) |
| **GCP VM** | `headscale`, zone `us-central1-a`, machine `f1-micro` |
| **External IP** | `35.226.60.95` (static, reserved as `headscale-ip`) |
| **SSH** | `gcloud compute ssh headscale --project=inbound-entity-239819 --zone=us-central1-a` |
| **Pre-auth key** | [Stored in Vaultwarden: PAT/Headscale/tim] — reusable, expires 24h from issue. Regenerate: `sudo headscale preauthkeys create --user 1 --reusable --expiration 24h` |
| **Headscale version** | v0.28.0 |
| **User** | `tim` (ID: 1) |

## Current State

- ✅ GCP VM (`f1-micro`, Debian 12) provisioned in `us-central1-a`
- ✅ Static IP `35.226.60.95` reserved
- ✅ Firewall rules: tcp:22,80,443 + udp:3478
- ✅ DNS: `hs.timmcg.net` → `35.226.60.95` (DNS Only)
- ✅ DNS: `headscale.timmcg.net` → `35.226.60.95` (DNS Only, alias)
- ✅ Headscale v0.28.0 installed, service running
- ✅ Let's Encrypt TLS cert issued for `hs.timmcg.net`
- ✅ Embedded DERP server enabled (Port 443, STUN 3478)
- ✅ MagicDNS base domain: `ts.timmcg.net`
- ✅ Split DNS: `home.timmcg.net` → Pi-hole `10.10.0.2` / `10.10.0.22`
- ✅ User `tim` (ID 1) created
- ✅ tesla connected (100.64.0.4) — macOS Tailscale.app; subnet routing ON, split DNS working; see macOS notes
- ✅ pixel (Android) connected (100.64.0.2) — subnet routing ON, split DNS working; see Android notes
- ⬜ feynman (skipped — desktop, no need)
- ✅ truenas-scale connected (100.64.0.3) — subnet 10.10.0.0/16 + exit node approved

## Key Details

| Component | Value |
|-----------|-------|
| GCP Machine | `f1-micro` (Debian 12, always-free tier) |
| Port 443/tcp | TLS / Headscale API + DERP relay |
| Port 80/tcp | ACME HTTP-01 challenge (Let's Encrypt) |
| Port 3478/udp | STUN (NAT hole-punching) |
| Storage | SQLite at `/var/lib/headscale/db.sqlite` |
| Config | `/etc/headscale/config.yaml` |
| Cert cache | `/var/lib/headscale/cache` |
| Service | `sudo systemctl [start|stop|restart|status] headscale` |
| Logs | `sudo journalctl -u headscale -f` |

## Connecting Clients

Existing Tailscale clients work — no different app needed. Minimum client version: **v1.74**.

```bash
# On each client (mac: use Homebrew tailscale, not App Store)
sudo tailscale logout
sudo tailscale up --login-server https://hs.timmcg.net --auth-key <key-from-VW>
```

For TrueNAS container: exec into the Tailscale jail/container and run the same commands.

To approve a node after `tailscale up` (if not using pre-auth key):
```bash
gcloud compute ssh headscale --project=inbound-entity-239819 --zone=us-central1-a
sudo headscale nodes register --user 1 --key <nodekey>
```

## Gotchas & Pitfalls

- **Client Migration:** Moving clients requires `tailscale logout` first. Existing Tailscale configurations need to be cleared to avoid conflict with tailscale.com.
- **Mac App Store Tailscale:** Restricts custom login servers. Use the Homebrew version (`brew install tailscale`) on mac.
- **macOS Homebrew Quirk:** Subnet routes (`--accept-routes`) and DNS (`--accept-dns`) may not automatically inject into the system routing table/resolver. You may need to manually add routes: `sudo route add -net 10.10.0.0/16 -interface utun4`.
- **Search Domain Conflict:** If `home.timmcg.net` is in your Wi-Fi search domains, macOS will bypass the `/etc/resolver/home.timmcg.net` file. Remove it: `sudo networksetup -setsearchdomains Wi-Fi empty`.
- **Minimum client version:** v1.74 — older clients will be rejected.
- **Cloudflare Proxy:** MUST be set to "DNS Only" (gray cloud). Headscale handles its own TLS. Proxied mode breaks DERP WebSockets.
- **Pre-auth keys expire:** 24h from creation. Generate a new one when needed (see Access table above).
- **`--user` flag:** Takes a numeric ID in v0.28.0, not a username. User `tim` = ID `1`.
- **MagicDNS base_domain:** `ts.timmcg.net` — nodes will be addressable as `<hostname>.ts.timmcg.net`.

## Outstanding Tasks

- [x] Connect tesla (Homebrew tailscale, system LaunchDaemon — `sudo brew services start tailscale`)
- [ ] Investigate missing Tailscale icon in macOS menu bar on tesla (Headscale connection active, but UI element missing)
- [x] Connect Pixel Android — subnet routing ON, DNS working
- [N/A] feynman — desktop, no need
- [x] Connect TrueNAS Tailscale container (`ix-tailscale-tailscale-1`) — SSH to 10.10.10.10, `sudo docker exec ix-tailscale-tailscale-1 tailscale up --login-server=https://hs.timmcg.net --auth-key=<key> --accept-routes --accept-dns=false --advertise-exit-node --advertise-routes=10.10.0.0/16 --hostname=truenas-scale`

**Setup complete.** All nodes connected, DNS working, subnet routes approved.

## DNS Notes

`*.home.timmcg.net` is Pi-hole only (not in public DNS). Split DNS pushes `home.timmcg.net` → `10.10.0.2` (Pi-hole primary) / `10.10.0.22` (Pi-hole secondary) to all Headscale clients.

Clients must also have **subnet routing enabled** to reach `10.10.0.2` via the VPN:
- Android/iOS: Tailscale Settings → **Subnet routing → ON** (opens a sub-screen "Subnet routes" → enable "Use Tailscale subnets")
- macOS/Linux: `tailscale up --accept-routes`

**Android DNS note:** The `ping` command in ADB shell does NOT use the Tailscale VPN DNS stack — it will fail to resolve `*.home.timmcg.net`. App-level DNS (browser, curl, etc.) routes correctly through split DNS. Confirmed: `nas.home.timmcg.net` loads TrueNAS login page in browser over VPN.

**Android DNS settings UI note:** The `home.timmcg.net` split DNS route does not appear in Tailscale → Settings → DNS settings on Android (only arpa reverse DNS routes are listed), but the split DNS IS being applied at the app level. This is a display-only gap in the Android UI.

## Android Connection Notes

The 7-tap logo trick does NOT work on Tailscale Android 1.94.x. The custom server option is hidden in a menu:

1. Open Tailscale → Settings → Accounts → tap **⋮ menu** (top-right)
2. Tap **"Use an alternate server"**
3. Enter `https://hs.timmcg.net`
4. Tap **Add account** — browser opens to Headscale registration page showing a `headscale nodes register` command
5. On the server: `sudo headscale nodes register --key <nodekey> --user tim`

**ADB approach (if needed):** Connect via wireless ADB, use `adb shell input` to navigate to the menu. Node registered as `localhost` by default — rename with `sudo headscale nodes rename --identifier <id> <name>`.
