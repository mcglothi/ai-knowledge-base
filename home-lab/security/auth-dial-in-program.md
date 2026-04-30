---
context: personal-homelab
tags: [auth, sso, oidc, oauth2, forward-auth, authentik, lldap, passkeys, biometrics, webauthn, truenas, unifi, vaultwarden, hardening]
hosts: [truenas, babbage, feynman, tesla, opensoak, pihole2, udm-pro]
services: [authentik, nginx-proxy-manager, lldap, vaultwarden, nextcloud, grafana, truenas]
last_updated: 2026-03-09
---

# Auth Dial-In Program

**Last Updated:** 2026-03-09
**Summary:** Long-running program to standardize authentication across `home.timmcg.net` with minimal breakage, clear rollback points, and a biometric-capable login experience.

## Mission
- Deliver an enterprise-style SSO experience where practical: one Authentik session unlocks protected web apps.
- Keep app-native and API client compatibility intact (no blanket forward-auth that breaks mobile/desktop/API flows).
- Add durable biometric UX via passkeys and platform authenticators (feynman, tesla, Pixel).

## Non-Goals
- Forcing every appliance UI to support native OIDC/SAML when vendor support is absent.
- Removing all local break-glass accounts.
- Blocking automation API calls that are currently needed by playbooks/agents.

## Design Rules
- Prefer native app OIDC/SAML over proxy auth where supported.
- Use forward-auth for browser/admin surfaces that do not support native federation.
- Keep direct/API endpoints available where client apps or agents require non-browser auth.
- Maintain one documented break-glass local admin per critical service.
- Every auth change must include pre-check, smoke test, rollback, and AIKB update.

## Program Board

## Phase 0: Baseline and Safety Rails
- [ ] Export current Authentik config snapshot (providers, apps, flows, outposts) and store path in AIKB.
- [ ] Export NPM proxy host map with auth mode classification (`native`, `forward-auth`, `local`).
- [ ] Create a rollback runbook for Authentik/NPM auth lockout scenarios.
- [ ] Validate at least two emergency access paths (direct host:port and local admin account).
- [ ] Rotate obvious plaintext/test credentials found in legacy compose files into Vaultwarden.

## Phase 1: Capability Matrix and Target Modes
- [ ] Build service auth matrix for all active `home.timmcg.net` entries and key direct services.
- [ ] For each service, set and document target mode:
  - `Native OIDC/SAML`
  - `Forward-auth (browser only)`
  - `Local auth (explicit exception)`
- [ ] Document API bypass paths needed for automation and health checks.
- [ ] Tag client-sensitive services where forward-auth breaks native apps (e.g., Vaultwarden, Jellyfin).

## Phase 2: Per-Service Cutovers
- [ ] TrueNAS: finish native OIDC login flow validation and remove redundant proxy-level auth if still present.
- [ ] Nextcloud: verify stable native OIDC + group mapping + logout behavior.
- [ ] Grafana: verify native OIDC + role mapping from Authentik groups.
- [ ] Vaultwarden: evaluate in-app OIDC enablement path and keep non-browser client compatibility.
- [ ] NPM, Dockge, Semaphore: keep forward-auth with tested cookie/session behavior.
- [ ] Media/admin stack (`*arr`, Transmission, SAB, Jellyfin, Overseerr, Unmanic): split browser protection from API/client paths where required.
- [ ] OpenSoak: confirm forward-auth posture and API path behavior for app/widget workflows.
- [ ] Pi-hole and infra tools: decide per-surface policy (admin UI protected, automation API allowlisted as needed).

## Phase 3: Biometrics and Passkeys
- [ ] Define authenticator policy for Authentik:
  - Preferred: passkeys synced via Bitwarden across devices.
  - Allowed fallback: platform authenticators (Touch ID, Android biometrics, Linux reader).
- [ ] Stage passkey rollout in a non-lockout order:
  - Enroll backup/recovery first.
  - Enroll one cross-device synced passkey.
  - Enroll platform-specific passkeys.
- [ ] Validate on:
  - `feynman` with Kensington fingerprint reader
  - `tesla` with Touch ID (when online)
  - Pixel 10 Pro Fold biometrics
- [ ] Add policy for service accounts and headless agents (non-passkey auth paths).
- [ ] Update AIKB recovery guidance for passkey/device loss and new-device enrollment.

## Phase 4: Operations and Drift Control
- [ ] Add weekly auth posture audit task (providers, proxy coverage, stale local admins, bypass paths).
- [ ] Add a checklist gate for all new services: choose auth mode before public DNS/proxy enablement.
- [ ] Add monitoring alerts for auth failures/spikes where useful (Authentik, NPM, key apps).
- [ ] Keep `access-reference.md`, `network-dns.md`, and this file synchronized after each change.

## Initial Service Targets (starting point)

| Surface | Current Direction | Target Direction | Notes |
|--------|-------------------|------------------|-------|
| Authentik portal | Active | Keep | Central IdP and session authority |
| NPM admin (`npm.home`) | Forward-auth | Keep forward-auth | Browser-only admin surface |
| Dockge (`dockge.home`) | Forward-auth | Keep forward-auth | Browser-only admin surface |
| Semaphore (`ansible.home`) | Forward-auth | Keep forward-auth | Browser-only admin surface |
| TrueNAS (`nas.home`) | OIDC in progress | Complete native OIDC | Avoid double-auth stack |
| Nextcloud (`nc/cloud.home`) | OIDC planned/active | Native OIDC | Verify group mapping |
| Grafana (`grafana.home`) | Native OIDC | Keep native OIDC | Verify role mapping |
| Vaultwarden (`vault.home`) | Local auth | Keep client-safe model | Do not break native clients |
| Jellyfin (`jellyfin.home`) | Mixed risk w/ proxy auth | Client-safe split policy | Keep direct URL fallback |
| OpenSoak (`opensoak.home`) | Forward-auth | Keep with tested exceptions | Preserve widget/app flows |
| UDM Pro / UniFi router | Local/vendor identity | Evaluate feasible IdP integration | Likely partial coverage only |

## Change Template (copy for each service)
- **Service:**
- **Owner:**
- **Current mode:**
- **Target mode:**
- **Dependencies:**
- **Pre-checks:**
- **Cutover steps:**
- **Validation:**
- **Rollback:**
- **AIKB docs touched:**

## Decisions Needed From Operator
- [x] Vaultwarden strategy: pilot native OIDC with break-glass local account retained.
- [x] UniFi target: pursue controller-admin SSO if feasible in current product tier.
- [x] Session policy: shared Authentik session domain across `*.home.timmcg.net` with long session window target (12-24h).
- [x] Break-glass policy: retain local emergency admin access for critical systems.
- [x] Service-account posture: ensure agent/automation accounts, SSH keys, PATs, and passwords are consistently deployed and documented.
- [x] Media policy: finalize browser-vs-client auth split strategy (hybrid model approved).
- [ ] Biometric policy: decide passkey-first vs relaxed password-only baseline for home-lab services.

## Operator Decisions (Recorded 2026-03-09)
- Vaultwarden: **pilot OIDC** while retaining a **break-glass local account** to avoid lockout.
- UniFi: target **controller-admin SSO if possible**; accept partial coverage if vendor limits apply.
- Session duration: prefer **once-per-day login** with **12-24 hour** session window.
- Security posture: currently relaxed MFA posture for home services; biometrics will be introduced deliberately.
- Break-glass and service accounts: explicitly required across critical systems and automation surfaces.
- Media policy: **hybrid approved** (browser SSO where safe, client/API-safe direct paths preserved).

## Recommended Media/Auth Policy (for decision #2)
- **Recommended:** hybrid split.
  - Browser admin UIs behind SSO/forward-auth where safe.
  - Native client/API endpoints remain app-native (or direct internal URL) to avoid breakage.
- Why this is recommended:
  - Preserves family/device usability (TV/mobile/desktop clients).
  - Avoids known redirect/JSON mismatch failures on apps like Jellyfin and Vaultwarden clients.
  - Still gives SSO convenience for admin operations in browser.
- Implementation tasks:
  - [ ] Tag each media service as `browser_protected`, `client_direct`, or `local_only`.
  - [ ] For protected hosts, define explicit unauthenticated/bypass API paths only where required.
  - [ ] Add/verify direct internal fallback URLs in AIKB and runbooks for client apps.

## Critical Access Guarantees
- [ ] Maintain two validated access paths for each critical service: (1) SSO path, (2) break-glass path.
- [ ] Verify break-glass credentials quarterly and after major auth changes.
- [ ] Ensure service-account deployment parity on `babbage`, `pihole2`, `opensoak`, `turing`, and operator workstations as applicable.
- [ ] Maintain a single registry of SSH keys/PATs/password items in Vaultwarden + AIKB references.

## Execution Queue (Next)

## Sprint 1: Baseline and Inventory Freeze
- [ ] Snapshot Authentik configuration and export provider/app map.
- [ ] Export NPM proxy host auth classification (`authentik_server/location`, `authentik_snippet`, native app OIDC, local-only).
- [ ] Build authoritative service matrix for all active `home.timmcg.net` entries.
- [ ] Record break-glass account verification status for: Authentik, TrueNAS, NPM, Vaultwarden, UniFi.

## Sprint 2: Low-Risk Normalization
- [ ] Confirm/clean double-auth patterns (native OIDC + proxy auth stacked unintentionally).
- [ ] Normalize admin surfaces to forward-auth where appropriate: NPM, Dockge, Semaphore.
- [ ] Confirm direct/API-safe endpoints for client-sensitive services:
  - Vaultwarden
  - Jellyfin
  - OpenSoak app/widget APIs
  - Media automation APIs (`*arr`, SAB, Transmission, Overseerr)

## Sprint 3: Native OIDC First
- [ ] TrueNAS native OIDC validation completion + rollback test.
- [ ] Nextcloud native OIDC validation completion + group mapping verification.
- [ ] Grafana native OIDC validation completion + role mapping verification.
- [ ] Vaultwarden OIDC pilot in controlled window with break-glass verification before/after.

## Sprint 4: Biometrics Rollout
- [ ] Define passkey enrollment baseline and recovery order.
- [ ] Validate on feynman (Kensington reader) and Pixel first.
- [ ] Validate tesla Touch ID path when host is online.
- [ ] Decide whether to move from relaxed MFA posture to passkey-first posture.

## Preflight Questions and Risk Controls (Gemini Review, 2026-03-09)

### Open Questions Before Cutovers
- [ ] Vaultwarden OIDC pilot scope: confirm exact pilot window, test account, and success criteria for browser + extension + mobile clients.
- [ ] Media hybrid implementation method: decide per service whether to use:
  - direct internal URLs for native clients, or
  - NPM path-level auth bypass rules (`auth_request off`) for API/client endpoints.
- [ ] UniFi controller-admin SSO feasibility in current product tier: confirm what is technically achievable now vs endpoint-only identity integration.
- [ ] Native OIDC claim mapping matrix: confirm canonical username/email/claim mapping for `mcglothi`, `dekatria`, and service accounts.

### Risk Controls to Apply
- **Identity circular dependency:** Do not rely only on Vaultwarden-synced passkeys for Authentik login.
  - [ ] Keep at least one independent authenticator path (platform/hardware passkey not dependent on Vaultwarden availability).
  - [ ] Exempt break-glass account from strict passkey-only policies.
- **Client/API breakage through forward-auth:**
  - [ ] For client-sensitive services, test browser and native clients separately after each auth change.
  - [ ] Preserve a direct API-safe path for automation and agent workflows.
- **OIDC mapping failures:**
  - [ ] Run non-primary user test (`dekatria`) before primary admin cutover for each native OIDC service.
  - [ ] Validate group/role mapping and logout behavior per app.
- **Double-auth redirect loops:**
  - [ ] For services moving to native OIDC, remove proxy-level forward-auth first, then enable native OIDC enforcement.
  - [ ] Capture and test rollback before switching production login paths.

## Completion Criteria
- [ ] Every major service has an explicit auth mode and rollback documented.
- [ ] No core client app (Bitwarden, Jellyfin, mobile apps, automation agents) regresses due to SSO changes.
- [ ] Human admin login uses a consistent Authentik session model where technically feasible.
- [ ] Biometric/passkey login works on feynman, tesla, and Pixel with tested recovery paths.
