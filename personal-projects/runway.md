---
tags: [runway, ai-tools, quota, tracking, electron, macos, menu-bar]
last_updated: 2026-04-19
---

# Runway
**Last Updated:** 2026-04-19
**Summary:** Live AI quota and utilization tracking for the macOS menu bar. Provides real-time "runway" estimates (time until exhaustion) for Claude, Codex/ChatGPT, Gemini, and GitHub Copilot.

## Environment Requirements
- **Platform:** macOS (primary), Windows/Linux support via Electron
- **Tools:** Node.js, Electron
- **Framework:** Vanilla JS + Electron + CSS

## Overview
- **Objective:** Give power users a "gas gauge" for their AI models so they can pace their work and avoid hitting hard limits mid-task.
- **Differentiator:** Real-time runway estimation based on current burn rate, supporting both official APIs and browser-session sync.

## Status
- **Repository:** `mcglothi/runway`
- **Phase:** 🔨 Pre-launch polish (all core features complete, launch blockers remaining)
- **Recent Updates (2026-04-19):**
  - **macOS Tahoe crash fix:** `~/.gemini/telemetry.json` had grown to 2.8 GB; `fs.readFileSync` at startup exhausted Node.js heap → `EXC_BREAKPOINT/SIGTRAP`. Fixed: tail-read last 512 KB only; auto-trim file to 2 MB when it exceeds 50 MB after each successful poll.
  - **Electron 34→35 upgrade:** Packaged app was built with bundled Electron 34 while `node_modules` had 35.7.5. npm workspaces hoists `electron` to root, making it invisible to `electron-builder` unless the version is pinned exactly. Fixed: pinned `"electron": "35.7.5"` in `apps/electron/package.json`.
  - **Lazy BrowserWindow creation:** Removed eager `ensure*Window()` calls at app startup — windows are created on first poll instead, eliminating redundant parallel DNS resolution at boot.
- **Previous Updates (2026-04-17):**
  - **UI Polish:** Spinning refresh button, live "Updated X ago" footer (15s tick), reset-time tooltips on runway column, amber error states for telemetry errors, popup widened 340→360px
  - **Configurable Refresh:** Settings UI for 1m/5m/15m/1h/manual intervals; `schedulePoll()` re-reads on save
  - **Gemini estimateRunway fix:** Zero-division bug when utilization=0; Pro mode now shows N/1500 count matching telemetry display
  - **Gemini auto-detect:** Reads `outfile` from `~/.gemini/settings.json`; `fs.watch` for real-time updates on session end
  - **Copilot display:** Provider exposes seat count as `short.text` and acceptance rate as `long` window with bar fill; renderer shows two rows
  - **Onboarding:** Connect-hint banner after first poll with per-provider sign-in links
  - **Distribution pipeline:** GitHub Actions release.yml (matrix: mac arm64+x64 / linux / win), Homebrew cask template, entitlements.plist, docs

## Architecture
- **Core Package:** `packages/core` contains the provider logic and quota schemas.
- **Electron App:** `apps/electron` handles the tray icon, popup window, and secure session management.
- **Browser Extension:** `apps/extension` (bridge) allows syncing session cookies from the browser to the desktop app.

## Roadmap
- [x] Initial scaffold and tray implementation
- [x] Claude and Codex session-sync providers
- [x] Gemini session-based tracking (requests/day)
- [x] Gemini CLI telemetry mode (OTLP, fs.watch, auto-detect path)
- [x] Mode selection (API Key vs. Pro Plan vs. Telemetry) for all providers
- [x] Copilot Enterprise metrics (seat utilization + acceptance rate display)
- [x] AIKB Integration: push quota snapshots to `_runtime/events/`
- [x] Configurable auto-refresh intervals (1m/5m/15m/1h/manual)
- [x] Onboarding connect-hint banner
- [x] Distribution pipeline (GitHub Actions, Homebrew cask template)
- [x] macOS Tahoe compatibility (Electron 35, telemetry tail-read, auto-trim)
- [ ] **App icon** — no icon.png/icns/ico yet; tray shows "RW" text fallback
- [ ] Historical usage graphs (local-only)
- [ ] Agent self-awareness API — let agents query their own headroom over MCP
- [ ] electron-updater (auto-update from GitHub releases)
- [ ] Extension build step (currently load-unpacked only, no dist/)

## Launch Blockers (before v0.1.0 tag)
1. **App icon** — `icon.png`, `icon.icns`, `icon.ico` all missing. Design work needed. This is the only true hard block.
2. **README Quick Start** — still references `.env.example` / manual session keys. Auth is now in-app. Needs rewrite.
3. **`discovery.js` in `apps/electron/`** — dev debug script will ship in the build. Move to `scripts/` or delete.
4. **Copilot "Individual — Coming soon"** radio option — makes settings look incomplete. Should be hidden.
5. **Extension dist/** — README says load from `dist/` but no build step exists. Either add esbuild/webpack or update README to load from source.
6. **`electron-updater`** not wired — users get no auto-update notifications after v0.1.0.
7. **`hero_graphic.png`** — noted as placeholder from day one. Needs real design.
