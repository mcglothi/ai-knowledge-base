---
context: personal
tags: [opensoak, raspberry-pi, fastapi, vite, hot-tub, authentik, npm, nginx, home.timmcg.net, python, ssh, systemd]
hosts: [opensoak]
last_updated: 2026-04-12
---

# OpenSoak Architecture
**Last Updated:** 2026-04-12
**Summary:** Architecture and operations reference for the OpenSoak Raspberry Pi hot tub controller stack.

## Environment Requirements
All development and administration happens **on the Pi via SSH** — no local toolchain needed.
- SSH access to `10.10.169.191` (must be on home network or VPN)
- SSH key: `[Stored in Vaultwarden: OpenSoak Pi SSH Key]`
- Works from any machine with SSH access

## Overview
OpenSoak is a hot tub controller consisting of a FastAPI backend and a Vite frontend.

## Documentation Status

- **README refresh (2026-04-12):** Updated the GitHub README to better reflect the current product surface area, including explicit mentions of vacation scheduling, electric cost analysis, thermal efficiency analytics, weather-aware dashboards, and admin observability. Replaced the older README screenshots with fresher captures of the current `User`, `Admin`, `Viewer`, and mobile admin UI.

## Features (Implemented)

- **5-Hour Hourly Forecast (2026-03-06):**
  - **Hourly Detail:** Replaced the 3-day view with 5 hourly slots starting from "NOW".
  - **Smart Time Labels:** Each slot is labeled with the specific hour (e.g. "9 PM", "10 PM").
  - **Corrected Logic:** Fixed Java import error and ensured the weather parser skips past old hourly data to always show current/upcoming hours.
  - **Density:** Maintained high visibility for the Hot Tub data while providing more granular environmental info.

## Safety Status Semantics

- **`OK`** means the system safety state is healthy: sensors are within limits, flow conditions look valid, and no active equipment fault has latched the controller.
- **`CRITICAL: HI-LIMIT FAULT`** means the water temperature or high-limit sensor exceeded the emergency threshold and the system shut down heating immediately.
- **`STOP: NO FLOW DETECTED`** means the circulation path did not show expected flow while the pump/heater logic expected water movement, so the system locked out to protect equipment.
- **`STOP: MASTER SHUTDOWN`** means an administrator deliberately forced the system into a stopped state.
- **`Error: ...`** means backend/control logic hit a software or integration fault severe enough to surface as an operator-visible status instead of normal runtime telemetry.

## Product Backlog (2026-03-07)

- **Desktop weather expansion:** Add weather radar/satellite modules beneath the forecast area on desktop layouts and restore the hourly forecast directly under the 7-day forecast.
- **Mobile-first priority layout:** On smaller screens, prioritize current temp, time remaining, stop schedule (if active), heater status, jets, and light controls. Hide `Soak Now` while a schedule is actively running to avoid conflicting controls.
- **Thermal efficiency analytics:** Add a histogram view and monthly cost forecast based on current schedules plus available weather data, using monthly averages when forecast coverage is incomplete. Refresh this view whenever forecast data or schedules change.
- **Cool-down telemetry:** Track how quickly the tub cools when the heater is off so future efficiency and scheduling recommendations have a real decay baseline.
- **Schedule detail fidelity:** Include the configured target temperature in saved soak schedules and let admins set the at-rest temperature explicitly.
- **Weather-aware scheduling:** Show a warning when an upcoming scheduled session overlaps with inclement weather, and optionally deep-link forecast tiles to a configurable external weather view.
- **Admin observability:** Add an admin-mode tail-log view so live troubleshooting does not require SSH for common checks.
- **Control safety rules:** Keep target temperature read-only when no soak session is active, and add guarded controls for high-limit safety settings above 110 F.
- **Session controls:** Add a visible Stop action in both user and admin modes to end the active soak or quick-heat session cleanly.
- **Simulation/UI correctness:** Fix simulation status mismatches such as the circulation pump appearing off during an active soak.
- **Layout polish:** Fix timer overlap issues, make the hero graphic/cards semi-transparent instead of hiding the graphic, and keep touch targets comfortable on mobile.

## Infrastructure
- **Host:** Raspberry Pi (10.10.169.191)
- **OS:** Debian 12 (Bookworm)
- **Location:** `/opt/opensoak`
- **Services:** 
  - `opensoak.service` (Backend, Port 8000)
  - `opensoak-frontend.service` (Frontend, Port 5173)
- **Web Server:** Local Nginx handling SSL termination on port 443.

## Dependency Security Notes

- **Axios supply-chain triage (2026-03-31):** Local `~/code` scan found Axios only in `opensoak/frontend`. The manifest declares `axios@^1.13.5`, the checked-in lockfile resolves to `axios@1.13.5`, and the installed tree on tesla also resolves to `1.13.5`.
- **Compromised npm releases not present:** No local manifests, lockfiles, or installed `node_modules` trees contained the short-lived compromised releases `axios@1.14.1` or `axios@0.30.4`, and no `plain-crypto-js` artifact was found under `~/code`.
- **Exploitability note:** The February 2026 Axios DoS advisory (`GHSA-43fc-jf86-j433` / `CVE-2026-25639`) affects applications that pass attacker-controlled parsed JSON into Axios config objects. The OpenSoak frontend uses Axios with explicit URL/header objects and does not use the risky `JSON.parse(...) -> axios config` pattern.

## DNS & SSL
- **FQDN:** `opensoak.home.timmcg.net` -> 10.10.169.191 (direct to the Pi as of 2026-03-07; bypasses NPM for this service)
- **SSO:** Protected by Authentik Forward Auth.
- **SSL:** Service now terminates SSL on the Pi directly for the primary FQDN path; the older NPM wildcard-cert path remains relevant for historical troubleshooting notes.
- **Pi-local resolution:** OpenSoak Pi handles its own SSL for direct access via IP if needed.


## Known Hardware Issues

- **⚠️ Undervoltage (active):** Pi 4 PSU is underpowered. `vcgencmd get_throttled` returns `0x50005` — CPU is currently throttled. Replace with a 5V/3A USB-C supply. See [`home-lab/hardware.md`](../home-lab/hardware.md).

## Troubleshooting

### DNS Shortname Redirect (Implemented 2026-02-21)
- **Problem:** Short names (e.g., `http://opensoak/`) resolve but cause SSL errors because the wildcard cert doesn't match the bare hostname.
- **Solution:** Added a Redirection Host (ID 21) in NPM to catch `http://opensoak` and redirect to `https://opensoak.home.timmcg.net`.
- **Status:** ✅ Redirect works as expected.

### Authentik "Invalid Client ID" (Resolved 2026-02-23)
- **Problem:** Both the shortname redirect and direct FQDN access triggered an Authentik error: `The client identifier (client_id) is missing or invalid.`
- **Root Cause:** Host matching conflict in Authentik. 18 proxy providers with identical `external_host` (`https://auth.home.timmcg.net`) caused the outpost to match the wrong application. The stale `client_id` belonged to a deleted provider still cached in the outpost.
- **Fix:** Consolidated all 18 proxy providers into a single **"Home Lab Global"** provider using `forward_domain` mode. All subdomains now share a single session and provider mapping.
- **Status:** ✅ RESOLVED. Access to `opensoak.home.timmcg.net` verified via simulated auth requests.

### Web Frontend Stuck on Dark Blue Background (Resolved 2026-02-27)
- **Problem:** Frontend loads the background but stays stuck, showing only dark blue. Console (theoretical) would show JSON parse errors.
- **Root Cause:** NPM proxies directly to Vite (port 5173). Vite was not configured to proxy `/api` to the backend (port 8000), so it served the app shell (HTML) for API requests.
- **Fix:** Added proxy configuration to `vite.config.js` to route `/api` to port 8000.
- **Status:** ✅ RESOLVED. Verified JSON response on port 5173.

### Android TV & Widget Connectivity / CORS (Resolved 2026-02-24, Updated 2026-03-31)
- **Problem:** Shield TV app and widget showing "Waiting for backend" or failing to update.
- **Root Cause 1:** Local DNS resolution on the Pi (`10.10.169.191`) for `opensoak.home.timmcg.net` resolved to itself instead of the NPM proxy (`10.10.10.10`).
- **Root Cause 2:** Nginx on the Pi was redirecting port 80 to 443. The Android WebView (Capacitor) was blocking these requests due to CORS and/or SSL trust issues when hitting the Pi directly.
- **Root Cause 3:** The Android widget was crashing due to a missing `weather_code` key in the hourly forecast API response.
- **Root Cause 4 (Incident 2026-03-31):** Pi-hole DNS records for `opensoak.home.timmcg.net` and `opensoak` were stale on both primary and secondary resolvers, pointing back to the NPM proxy (10.10.10.10). NPM had Authentik Forward Auth enabled, causing background widget fetches to be redirected to a login page (HTML) which the widget could not parse as JSON.
- **Fix 1:** Updated Pi's Nginx to serve `/api` directly on port 80 (bypassing HTTPS redirect for local clients).
- **Fix 2:** Added robust Nginx-level CORS headers mirroring the incoming `Origin` and allowing credentials.
- **Fix 3:** Added `weather_code` to the Open-Meteo API parameters in `status.py`.
- **Fix 4 (2026-03-31):** Reconciled Pi-hole DNS records on both primary (`truenas`) and secondary (`pihole2`) to point directly to the Pi's local IP (`10.10.169.191`). Force-stopped the Shield app to clear its DNS/connection cache.
- **Status:** ✅ RESOLVED. TV app and widget are fully functional and bypassing Authentik/NPM for local traffic.

## Proxy & Redirect Logic (Fix 2026-02-21)
OpenSoak was prone to a 'Double Redirect Loop' because NPM was proxying to port 80 on the Pi, which then redirected to HTTPS, confusing the browser (especially Firefox).
- **Current Configuration:** NPM proxies directly to the dev servers bypassing Pi Nginx.
  - **Frontend:** Port 5173
  - **API:** Port 8000

## Responsiveness Fix (2026-02-24)
- **Problem:** Android widget only updates when clicked or every 15-30 minutes (system limit).
- **Solution:** Installed `adb` on the OpenSoak Pi and deployed a background service (`opensoak-widget-refresher.service`) that broadcasts a refresh intent to the Shield (`10.10.174.255`) every 60 seconds.
- **Service path:** `/etc/systemd/system/opensoak-widget-refresher.service`
- **Script path:** `/opt/opensoak/scripts/refresh_widget.sh`
