---
tags: [vaultwarden, passwords, secrets, bitwarden, bw, truenas, docker, litestream, gcs, vault.home.timmcg.net, api-keys, dockge, backup, failover]
hosts: [truenas]
services: [vaultwarden, litestream]
last_updated: 2026-03-14
---

# Vaultwarden (Bitwarden)

**Last Updated:** 2026-03-14
**Summary:** Self-hosted Bitwarden-compatible password manager running as a Docker container on TrueNAS. Accessible at vault.home.timmcg.net with wildcard SSL. Signups disabled.

---

## Deployment
- **Type:** Docker Container (TrueNAS SCALE / Dockge)
- **Internal Port:** 30080
- **External URL:** https://vault.home.timmcg.net
- **Storage:** /mnt/Containers/Vaultwarden

## Configuration
- **Signups:** Disabled (via environment variable)
- **Admin Panel:** Active via ADMIN_TOKEN
- **SSL:** Wildcard cert (*.home.timmcg.net) handled by NPM.

## Remote Access & Failover
- **Tailscale:** Primary remote access node runs on TrueNAS.
- **Cloud Failover (Proposed):** Sync to a GCP Free Tier instance for high availability.
    - **Primary:** TrueNAS (Home Lab)
    - **Failover:** GCP E2-micro instance
    - **Mechanism:** Litestream 0.3.13 (for SQLite replication to GCS bucket) + Secondary Tailscale node on GCP.
    - **Status:** 🟢 ACTIVE. Litestream sidecar running on TrueNAS, replicating to `gs://mcglothi-vaultwarden-replication`.
    - **Database:** ✅ Confirmed SQLite.

## Recovery Steps (to GCP VPS)
1. Provision GCP `e2-micro` instance.
2. Install Tailscale and Docker.
3. Deploy Vaultwarden + Litestream stack with `LITESTREAM_REPLICA_TYPE=gcs` and the service account key.
4. Run `litestream restore -config /data/litestream.yml /data/db.sqlite3` before starting the container.

## Bitwarden CLI (`bw`) Notes
- **Install:** `npm install -g @bitwarden/cli` (not available via brew)
- **Point to self-hosted instance:** `bw config server https://vault.home.timmcg.net`
- **Login:** `bw login`

## Session Persistence (`bwu`)
`bwu` is a shell function in `~/.zshrc` that unlocks the vault and writes the session token to `~/.bw_session` (chmod 600). Scripts read it via `BW_SESSION=$(cat ~/.bw_session)` instead of prompting interactively. Run once per work session.

**Concurrent agent fix (2026-02-24):** When Claude Code and Gemini CLI both run `bwu`, each generates a new session token and overwrites `~/.bw_session`, invalidating the other's session mid-task. Two fixes applied:

1. **Vault timeout set to never:** `~/Library/Application Support/Bitwarden CLI/data.json` → `"vaultTimeout": -1`. An unlocked session never auto-locks.
2. **`bwu()` checks existing session first:** Before prompting for master password, `bwu` calls `bw status --session <existing>` and reuses the session if it's still `"unlocked"`. Only prompts if missing or stale.

Net effect: once the vault is unlocked with `bwu`, both agents share the session indefinitely without re-prompting.

**Follow-up hardening note (2026-03-14):** A Nyquist/UniFi follow-up exposed one more edge case on `tesla`: the operator's interactive shell reported `bwu` session reuse, but a separate Codex shell still saw `~/.bw_session` as stale until the token was explicitly rewritten with `bw unlock --raw > ~/.bw_session`. Treat the current implementation as mostly working but still brittle. The next improvement should:

1. Validate session state via `jq -r '.status'` instead of grepping for an exact compact JSON substring.
2. If the current shell already has a valid `BW_SESSION`, rewrite `~/.bw_session` from that known-good token before prompting.
3. Optionally add a lightweight `bw sync` after unlock/rewrite so newly created items become visible to CLI callers immediately.

## PAT / API Key Organization
All API tokens live in the **API Keys** folder using the naming convention `PAT/<Service>/<Name>`:
- `PAT/GitHub/AIKB MCP Token` — GitHub PAT for AIKB MCP server
- `PAT/Cloudflare/Global` — Cloudflare Global API Key (⬜ should be replaced with a scoped API Token)

## Gotchas
- **AI agents must not run `bw unlock` directly** — it prompts for the master password interactively and will hang or fail. All AI tools (Claude Code, Gemini CLI, etc.) must check for `~/.bw_session` first. If it's missing or stale, they must stop and ask the user to run `bwu` in their terminal. See `_agents/registry.md` for per-agent notes.
- **`bwu` reuse can still be fooled by stale session-file state** in some cross-shell cases even when the operator shell says "Session reused." If an agent sees `bw status` as locked while the operator believes the vault is already unlocked, refresh the file explicitly with `bw unlock --raw > ~/.bw_session && chmod 600 ~/.bw_session`.
- **`bw sync` required after creating items in the web UI.** The CLI caches vault data locally — newly created items won't be found until you run `bw sync`. Symptom: `bw get password "Item Name"` returns "Not found" immediately after creating the item in the browser.
- **Cloudflare credential is a Global API Key** (37 chars, numeric prefix), not a scoped API Token. Use `X-Auth-Email` + `X-Auth-Key` headers, not `Authorization: Bearer`. Scripts must account for this until replaced with a scoped token.

## Future Roadmap & Investigations
- **SSO Integration:** Investigate adding Single Sign-On (SSO) capability to Vaultwarden (potentially via Authentik).
- **Automated Unlocking:** Research methods to automate vault unlocking to reduce interactive prompts.
- **Biometric Authentication:** Look into integrating fingerprint readers or other biometric options for more seamless access.
