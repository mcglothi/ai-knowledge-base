---
tags: [jellyfin, media-server, truenas, k8s, mpv, sso, authentik]
services: [jellyfin]
last_updated: 2026-02-26
---

# Jellyfin

**Last Updated:** 2026-02-26
**Summary:** Primary media server replacing Plex. Deployed on TrueNAS SCALE (Kubernetes).

---

## Access

| Method | URL / Address | Notes |
|--------|---------------|-------|
| Web UI | `https://jellyfin.home.timmcg.net` | Proxied via NPM |
| Direct (Internal) | `http://10.10.10.10:30013` | Bypass Authentik/NPM |
| Desktop App | `jellyfin-desktop` | AUR package (Qt6) |

## Known Issues & Workarounds

### Login Hang (Authentik Forward Auth)
Native desktop and mobile apps may "hang" or fail to connect when using the FQDN if **Authentik Forward Auth** is enabled on the proxy host. The apps receive an HTML redirect to the SSO login page instead of the expected JSON response from the Jellyfin API.

**Fix:** Use the Direct Internal IP (`http://10.10.10.10:30013`) or disable Forward Auth for the Jellyfin proxy host in NPM.

---

## Client Installation (Arch/feynman)
- **Package:** `jellyfin-desktop` (AUR)
- **Why:** Qt6-based. `jellyfin-media-player` (Qt5) has build issues with `qt5-webengine` on modern Arch.
- **Conflict:** Conflicts with `plex-media-player` over `/usr/resources/qtwebengine_devtools_resources.pak`. Remove Plex before installing.
