---
context: personal-homelab
tags: [authentik, sso, oauth, oidc, forward-auth, truenas, identity, nginx, proxy-auth, svc_claude, svc_gemini, postgres, redis, dockge]
hosts: [truenas]
services: [authentik, postgres, redis]
last_updated: 2026-04-22
---

# Authentik (SSO)

**Last Updated:** 2026-04-28
**Summary:** Central Identity Provider (IdP) for the home lab. Handles Single Sign-On (SSO) and Forward Auth for services.

---

## Deployment
- **Type:** Docker Container (Dockge Stack on TrueNAS)
- **Host:** 10.10.10.10
- **Internal Ports:** 9000 (HTTP), 9443 (HTTPS)
- **External URL:** https://auth.home.timmcg.net (planned)
- **Storage:** /mnt/Containers/authentik

## Configuration
- **Database:** Postgres 16 (in stack)
- **Cache:** Redis (in stack)
- **Secret Key:** [Stored in Vaultwarden: `AUTHENTIK_SECRET_KEY`]
- **Database Password:** [Stored in Vaultwarden: `POSTGRES_PASSWORD` under Authentik item]

## Integration Strategy
1. **Forward Auth:** Use NPM to challenge requests against Authentik before allowing access to internal services (OpenSoak, NPM Admin, etc.).
2. **OIDC/SAML:** Native integration for apps that support it (Nextcloud, Grafana).
3. **RADIUS (UDM Pro):** (Planned) Use an Authentik RADIUS Outpost to provide SSO for UDM Pro management, VPN, and WPA2-Enterprise Wi-Fi.

## Initial Setup
- **Initial Setup URL:** http://10.10.10.10:9000/if/flow/initial-setup/
- **Admin User:** akadmin

## Configured Applications (as of 2026-04-13)

32 total apps in Authentik portal. Protection model:
- **OIDC (native):** Grafana, Nextcloud, TrueNAS — Authentik handles login directly
- **Forward Auth (Home Lab Global, pk=23):** All other services — NPM `authentik_snippet.conf` + domain cookie `.home.timmcg.net`
- **Forward Single (AI Hub, pk=45):** ai.home.timmcg.net — per-service forward auth (allows unauthenticated API/WS paths)
- **Portal shortcuts only (no auth):** unifi.home.timmcg.net — UDM Pro has its own auth; adding forward auth would break it

### NPM Forward Auth Coverage
| Service | Protected | Mode |
|---------|-----------|------|
| ai.home | ✅ | forward_single (pk=45) |
| grafana | ✅ | OIDC (pk=41) |
| nextcloud / nc | ✅ | OIDC (pk=42) |
| truenas / nas | ✅ | OIDC (pk=43) |
| portainer | ✅ | forward_domain (added 2026-04-13) |
| prometheus | ✅ | forward_domain (added 2026-04-13) |
| pihole | ✅ | forward_domain (added 2026-04-13) |
| llm | ✅ | forward_domain (added 2026-04-13) |
| loki | ✅ | forward_domain (added 2026-04-13) |
| dockge, sonarr, radarr, prowlarr, sabnzbd, nzbget, overseerr, transmission, tautulli, unmanic, maintainerr, jellyfin, opensoak, vault, ansible, npm, cloud, chat, code, memory, sessions, terminal, homelab-docs | ✅ | forward_domain |
| plex | ❌ | Plex own auth — forward auth breaks native clients |
| lovelace (Home Assistant) | ❌ | HA own auth — forward auth breaks HA |
| idrac | ❌ | iDRAC own auth |
| unifi | ❌ | UDM Pro own auth — portal shortcut only |

### TrueNAS SCALE — Native OIDC (Added 2026-02-24) — ⚠️ IN PROGRESS
- **Problem:** TrueNAS was behind Forward Auth but still required local login.
- **Solution:** Configured dedicated OAuth2/OIDC provider in Authentik.
- **Configuration:**
  - **Discovery URL:** `https://auth.home.timmcg.net/application/o/truenas/.well-known/openid-configuration`
  - **Client ID:** `UzptlFUNozt11rhZYvhUMQ6rJHJrFrr6gbGaZgDL`
  - **Client Secret:** `[Stored in Vaultwarden: PAT/TrueNAS/OIDC]`
  - **Redirect URI:** `https://nas.home.timmcg.net/ui/sessions/signin/`
- **Mapping:** Authentik `preferred_username` must match a local TrueNAS user for automatic login.
- **NPM Note:** Forward Auth can be removed from the `nas.home.timmcg.net` proxy host to avoid double-challenges, as TrueNAS will now redirect to Authentik natively.

## 🛠️ Resolution Log

### Terminal App — policy_engine_mode Fixed (2026-04-28)
- **Symptom:** `terminal.home.timmcg.net` showed "Request has been denied. Flow does not apply to current user." for all users.
- **Root cause:** Terminal application in Authentik had `policy_engine_mode: any` with 0 policy bindings. In `any` mode, no policy can pass → everyone denied. Other apps (Dockge, Portainer) with the same config predate a behavior change; Terminal was created later and hit the stricter evaluation.
- **Fix:** Changed Terminal app `policy_engine_mode` from `any` → `all` directly in DB (API PATCH returned null). With `all` mode and 0 bindings, the empty set vacuously passes → all authenticated users allowed.
  ```sql
  UPDATE authentik_policies_policybindingmodel
  SET policy_engine_mode = 'all'
  WHERE pbm_uuid = (SELECT policybindingmodel_ptr_id FROM authentik_core_application WHERE slug = 'terminal');
  ```
- **Lesson:** When creating new forward-auth-only applications in Authentik with no explicit policies, set `policy_engine_mode: all` or add a group binding.

### Login Page Autofocus → Bitwarden Overlay (2026-04-28)
- **Symptom:** On the Authentik login page, the browser autofill/Bitwarden overlay appeared over the OAuth provider buttons (Google/GitHub), requiring a click-off before using OAuth.
- **Root cause:** Bitwarden browser extension shows its inline autofill overlay when any username/password field receives focus (including autofocus from Authentik's web component). This is Bitwarden behavior, not browser native autofill.
- **Fix:** Added Authentik's domain to Bitwarden → Settings → Autofill → **Excluded Domains**. Bitwarden no longer shows the overlay on the login page.
- **Custom template (side effect):** A custom `if/flow.html` was deployed to `/mnt/Containers/authentik/custom-templates/if/flow.html` during investigation. It adds a `focusin`-based blur script to dismiss autofocus. This is harmless and left in place.
  ```javascript
  // Blurs auto-focused input before user interacts, preventing autofill overlay
  document.addEventListener('focusin', function(e) {
    if (!interacted) { e.target.blur(); }
  }, { once: true });
  ```

### AI Hub Forward-Auth Redirect Loop Mitigated (2026-04-22)
`ai.home.timmcg.net` was reported by the operator as failing with `ERR_TOO_MANY_REDIRECTS`. Direct checks showed the Turing app was healthy, and a fresh no-cookie HTTPS request reached the Authentik login flow normally, but NPM logs for proxy host 32 showed repeated 307 redirects for browser traffic.

Root cause risk: the shared NPM `authentik_snippet.conf` defined `/outpost.goauthentik.io` but did not explicitly disable `auth_request` inside that outpost location. That can cause the embedded outpost auth endpoint to be protected by the same forward-auth gate it is supposed to satisfy.

Live mitigation applied on TrueNAS:
- Backed up `/data/nginx/custom/authentik_snippet.conf`.
- Added `auth_request off;` inside `location /outpost.goauthentik.io`.
- Validated with `nginx -t`.
- Reloaded NPM by sending `HUP` to `ix-nginx-proxy-manager-npm-1`.

Validation:
- `/outpost.goauthentik.io/auth/nginx` on `ai.home.timmcg.net` is reachable through NPM.
- A fresh unauthenticated `https://ai.home.timmcg.net/` request redirects to Authentik and lands on the login page without exhausting redirects.
- If an already-authenticated browser still loops, clear the `authentik_proxy_*` / Authentik session cookies for `home.timmcg.net` and `auth.home.timmcg.net`, then retry.

### SSO Audit & Coverage Expansion (2026-04-13)
**Redis Performance Fix (slow Google OAuth root cause):**
- Discovered 176K+ keys accumulating with `noeviction` policy and no `maxmemory` set
- Set live: `redis-cli CONFIG SET maxmemory 512mb` + `CONFIG SET maxmemory-policy allkeys-lru`
- Made persistent: updated `compose.yaml` command to `--save 60 1 --loglevel warning --maxmemory 512mb --maxmemory-policy allkeys-lru`
- Memory now capped at 512MB; eviction kicks in when Redis approaches limit

**New forward auth coverage (NPM snippet added):**
- portainer.home.timmcg.net, prometheus.home.timmcg.net, pihole.home.timmcg.net, llm.home.timmcg.net, loki.home.timmcg.net

**New Authentik app portal entries created:**
- Groups `AI`: chat, llm | `Dev Tools`: code, memory, sessions, terminal | `Infrastructure`: portainer | `Monitoring`: prometheus, loki | `Network`: pihole, unifi

**Ubiquiti UDM Pro (unifi.home.timmcg.net):**
- Created NPM proxy host → 10.10.0.1:443 (HTTPS, wildcard cert, WebSocket upgrade enabled)
- Added Pi-hole DNS: `unifi.home.timmcg.net` → 10.10.10.10
- Authentik portal shortcut created (no forward auth — UDM Pro has own auth)
- Note: RADIUS outpost still planned for Wi-Fi/VPN SSO

### Grafana OAuth2 SSO (2026-04-13)
Grafana previously showed default login page (not Authentik SSO). Root cause: no OAuth env vars configured.
- Added `GF_AUTH_GENERIC_OAUTH_*` env vars to TrueNAS rendered compose via SSH+Python patch
- Key issue: missing `GF_SERVER_ROOT_URL=https://grafana.home.timmcg.net` caused wrong `redirect_uri`
- Authentik redirect_uri match changed from strict → regex: `https://grafana\.home\.timmcg\.net/login/.*`
- Grafana OAuth is now functional. Direct login bypass: `https://grafana.home.timmcg.net/login/generic_oauth`

### User Cleanup & Provisioning (2026-03-04)
- **Stale User Removal:** Deleted `tim` (imported from LLDAP but now redundant with `mcglothi`).
- **New User Added:** Provisioned `dekatria` (Kate Solomon) in LLDAP with temporary password `Tinjat!!`.
- **Admin Consolidation:** 
  - Added `mcglothi` to `lldap_admin` group in LLDAP.
  - In Authentik, set `authentik Admins` (superuser group) as the parent of `lldap_admin`.
  - **Result:** `mcglothi` now has superuser rights in Authentik via LDAP sync.
- **Note:** `akadmin` (local) was kept for emergency access.

### Host Matching Conflict Fixed (2026-02-23)
- **Problem:** 18 proxy providers with identical `external_host` caused the outpost to match the wrong application, triggering "failed to detect a forward URL" and "Invalid Client ID" errors.
- **Fix:** Consolidated all Forward Auth apps into a single **"Home Lab Global"** provider (pk 23).
- **Configuration:**
  - **Mode:** `forward_domain`
  - **External Host:** `https://auth.home.timmcg.net`
  - **Cookie Domain:** `.home.timmcg.net`
- **Result:** All Forward Auth subdomains (`sonarr`, `radarr`, `opensoak`, etc.) now share a single session and provider mapping. Individual proxy providers (24-40) were deleted.
- **Native OIDC restored:** Recreated dedicated OAuth2 providers for Grafana and Nextcloud using their original Client IDs and secrets.


## ⚠️ Known Issues

### Vaultwarden — Authentik auth removed (2026-02-20)
Authentik forward auth was configured on `vault.home.timmcg.net` (NPM proxy host ID 24) but caused HTTP 500 errors. Root cause: the embedded outpost returned 500 with `"failed to detect a forward URL from nginx"` — the `X-Original-URL` / `X-Forwarded-Host` headers were not being passed in the nginx `auth_request` sub-request, so Authentik couldn't determine the redirect URL.

**Do not put Authentik SSO in front of Vaultwarden.** Bitwarden clients (mobile, desktop, browser extension) authenticate directly via the Vaultwarden API — they do not go through a browser SSO flow. Adding forward auth breaks all native clients. Vaultwarden has its own login and 2FA.
n**Jellyfin Desktop/Mobile:** Similar to Bitwarden, native Jellyfin clients may hang if the FQDN is behind Forward Auth because they cannot handle the HTML redirect to the SSO page. Use direct IP or bypass policy.

The `authentik_snippet.conf` include was removed from `/data/nginx/proxy_host/24.conf` and NPM was restarted.

### ⚠️ API / Agent Access Hazard
Forward Auth challenges ALL requests, which can break REST API calls from agents or scripts (like `curl` or `python-requests`) if they don't provide an Authentik session cookie.

**Solution:** In the `Proxy Provider` settings in Authentik, add a "Unauthenticated Path" regex or create a specific "Agent Policy" that allows bypass based on an API Key header (like `X-Agent-Key`).

**Applied (2026-03-04):** Added unauthenticated paths to the **Home Lab Global** proxy provider (pk 23) to allow AI Hub sessions WebSocket + sync:
- `^/ws/terminal/.*$`
- `^/api/sync$`

**API Access Pattern:** NPM strips the `Authorization` header, so Bearer token calls to `https://auth.home.timmcg.net/api/v3/` will return 401 even with a valid token. Always call the API directly on the internal port: `http://10.10.10.10:9000/api/v3/`.

### Passkey Lockout — Full Resolution (2026-02-23)

**Phase 1 (feynman session, earlier):**
- **Symptom:** After deploying Authentik, any home service redirected to the auth page with a browser passkey popup (WebAuthn). Login completely blocked on devices that didn't have the passkey.
- **Root cause:** 3 WebAuthn devices were enrolled during initial setup (1x Chromium Browser, 2x Google Password Manager). The MFA validation stage required one of them — `not_configured_action=skip` only applies when zero devices are enrolled.
- **Fix:** Generated recovery key via `docker exec authentik-worker-1 ak create_recovery_key 10 akadmin`, then deleted all 3 WebAuthn devices via Django ORM.

**Phase 2 (tesla session, 2026-02-23):**
- **Symptom:** Phone and Mac still prompted for biometric/passkey ("mobile device or USB key") even after devices were deleted. DB confirmed zero WebAuthn devices enrolled.
- **Root cause:** The `default-authentication-mfa-validation` stage was at **order 5 — before identification (order 10)**. At that point no user is identified, so Authentik sends a blank WebAuthn discovery challenge (`allowCredentials: []`), which causes the browser to show its passkey picker regardless of `not_configured_action=skip`. Additionally, passkeys stored in Google Password Manager on Pixel and in macOS needed to be deleted from the client side.
- **Fix:**
  1. Deleted passkey from Google Password Manager on Pixel (via passwords.google.com)
  2. Moved MFA validation stage from order 5 → order 25 via Django ORM:
     ```python
     from authentik.flows.models import Flow, FlowStageBinding
     flow = Flow.objects.get(slug="default-authentication-flow")
     binding = FlowStageBinding.objects.get(target=flow, order=5)
     binding.order = 25
     binding.save()
     ```
- **Result:** Auth flow is now: Identification (10) → Password (20) → MFA Validation/skip (25) → Login (100). No passkey prompt on any device. Login proceeds via username/password or Google/GitHub OAuth.

## Service Accounts (IdP)
- **svc_gemini:** Agent account used by Gemini CLI. Token in Vaultwarden. ✅ Superuser (admins group, 2026-02-22).
- **svc_claude:** Agent account used by Claude. Token in Vaultwarden as `Agent Token (Claude)`. ✅ Superuser (admins group, 2026-02-22). Token regenerated 2026-02-23 (old token was stale).

## Federated Sources
- **Google:** Configured for OAuth2 login. 
    - **Matching Mode:** `email_link` (links Google accounts to existing users by email).
    - **Credentials:** Stored in Vaultwarden as `Authentik GCP OAuth Token`.
- **GitHub:** Configured for OAuth2 login (Added 2026-02-22).
    - **Matching Mode:** `email_link`.
    - **Client ID:** `Ov23liWgElC8DY5G01mH`.
    - **Client Secret:** `[Stored in Vaultwarden: Authentik GitHub Secret]`.
    
## Branding & Customization
To match the `timmcg.net` dark retro hacker aesthetic, the following customizations were applied via the API (using `svc_gemini` with superuser rights):

- **Aesthetic:** Dark background, Matrix green text, scanline overlays.
- **Custom CSS:** Applied to `attributes.custom_css` and `attributes.branding_custom_css` in the default brand.
- **Verbiage:** Updated flow title/name from "Welcome to authentik!" to "home.timmcg.net".
- **Logo:** Replaced stock logo with a base64 encoded cryptic hacker SVG (animated pulsing "ACCESS_").
- **Branding Title:** Updated to "Home Lab SSO".
- **External Sources:** Google and GitHub OAuth configured and set as primary identification choices.
- **Domain Matching:** Brand domain set to `auth.home.timmcg.net` to ensure matching across services.
- **OAuth Prominence:** Google OAuth buttons are styled with high-contrast green borders and glow effects.
- **Flow Adjustment:** (Planned) Move Google OAuth source to the top of the Identification Stage in the login flow.

### Retro Hacker CSS
```css
/* --- Retro Hacker Aesthetic --- */

/* Root and Body */
:root {
  --hacker-green: #00ff41;
  --hacker-dark-green: #003b00;
  --hacker-bg: #000000;
}

body {
  background-color: var(--hacker-bg) !important;
  background-image: none !important; /* Kill the stock snowy background */
  color: var(--hacker-green) !important;
  font-family: 'Courier New', Courier, monospace !important;
}

/* Ensure the login container itself also has no background image */
.pf-c-login {
  background-image: none !important;
  background-color: var(--hacker-bg) !important;
}

/* The Login Container */
.ak-login-container, .pf-c-login__main {
  background: rgba(0, 0, 0, 0.8) !important;
  border: 1px solid var(--hacker-dark-green) !important;
  box-shadow: 0 0 20px rgba(0, 255, 65, 0.2) !important;
  color: var(--hacker-green) !important;
}

/* Scanline Effect Overlay */
body::before {
  content: " ";
  display: block;
  position: fixed;
  top: 0; left: 0; bottom: 0; right: 0;
  background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.2) 50%), 
              linear-gradient(90deg, rgba(255, 0, 0, 0.01), rgba(0, 255, 0, 0.01), rgba(0, 255, 0, 0.01));
  z-index: 9999;
  background-size: 100% 4px, 4px 100%;
  pointer-events: none;
}

/* Header and Text */
h1, h2, p, label {
  color: var(--hacker-green) !important;
  text-shadow: 0 0 10px rgba(0, 255, 65, 0.5) !important;
  text-transform: uppercase;
  letter-spacing: 2px;
}

/* Input Fields */
input.pf-c-form-control {
  background-color: #050505 !important;
  border: 1px solid var(--hacker-dark-green) !important;
  color: var(--hacker-green) !important;
  font-family: 'Courier New', Courier, monospace !important;
}

input.pf-c-form-control:focus {
  border-color: var(--hacker-green) !important;
  box-shadow: 0 0 10px var(--hacker-dark-green) !important;
}

/* Primary Action Button (Login) */
.pf-m-primary {
  background-color: var(--hacker-dark-green) !important;
  border: 1px solid var(--hacker-green) !important;
  color: var(--hacker-green) !important;
  text-transform: uppercase;
}

.pf-m-primary:hover {
  background-color: var(--hacker-green) !important;
  color: #000 !important;
}

/* --- Google OAuth Button (Making it Obvious) --- */

/* Targets the specific source list buttons in Authentik */
.ak-login-sources a, .pf-c-button.pf-m-secondary {
  display: flex !important;
  align-items: center;
  justify-content: center;
  padding: 15px !important;
  margin-top: 20px !important;
  border: 2px solid var(--hacker-green) !important;
  background-color: rgba(0, 255, 65, 0.05) !important;
  color: var(--hacker-green) !important;
  font-weight: bold !important;
  text-shadow: 0 0 5px var(--hacker-green);
  transition: all 0.3s ease;
}

.ak-login-sources a:hover {
  background-color: var(--hacker-green) !important;
  color: #000 !important;
  box-shadow: 0 0 25px var(--hacker-green) !important;
}

/* Specifically calling out the "Google" text if possible */
.ak-login-sources a::after {
  content: " [EXTERNAL AUTH]";
  font-size: 0.7rem;
  margin-left: 10px;
  opacity: 0.7;
}
```
    
    ### Redirect Loop Fixed (2026-02-21)
    
- **Symptom:** 'Too many redirects' in Firefox, but worked on mobile.
- **Resolution:** 
  1. Consolidated 18 individual providers into a single 'Home Lab Global' provider.
  2. Set Cookie Domain to `.home.timmcg.net` (with leading dot).
  3. Added `proxy_cookie_domain` to Nginx to rewrite Authentik host to the wildcard domain.
  4. Enabled `SameSite=Lax` compatibility via explicit Nginx headers.

## Future Improvements
- [ ] **Consolidate MFA/Passkeys:** Shift from device-local biometrics to Bitwarden-synced Passkeys. 
    - Goal: Single WebAuthn entry in Authentik that works across Mac (TouchID), Pixel, and Linux (Workstation Fingerprint) via Bitwarden browser extension and mobile app.
- [ ] **Friends and Visitors Auth:** Design and implement a guest access strategy.
    - Goal: Use Groups and Invitation Flows to grant limited app access to external users without manual password management.
- [ ] **RADIUS for UDM Pro:** Implement Authentik RADIUS Outpost for VPN and Wi-Fi SSO.
