---
context: personal-homelab
title: Blurt + Dropzone — Watch-to-AIKB Capture Stack
Last Updated: 2026-04-24 (verified 2026-04-24)
Summary: WearOS app (blurt) + FastAPI relay (dropzone) that captures voice/typed notes from the watch and writes them into AIKB ideas/inbox/.
---

# Blurt + Dropzone — Watch-to-AIKB Capture Stack

## Overview

Two-repo system for capturing quick notes from a WearOS watch and landing them in AIKB for agent triage.

**Flow:**
```
Watch tap → voice/type → confirm → POST /memo → dropzone:8080
  → runtime_cli.py idea add → ideas/inbox/YYYY-MM-DD/<slug>.md
  → sync hook: git commit + push AIKB → agents see it next session
```

---

## blurt (mcglothi/blurt) — WearOS App

**Repo:** `github.com/mcglothi/blurt` (private)  
**Language:** Kotlin, Jetpack Compose for Wear  
**Modules:** `wear/` (UI), `shared/` (DropzoneClient HTTP client)

### UI States
| State | Description |
|-------|-------------|
| Idle | Pulsing glow circle with mic icon. Tap to start. |
| PickMode | Choose Voice or Type |
| Confirm | Shows transcribed/typed text. Send or cancel. |
| Sending | Animated expanding rings while POST in flight |
| Done | Green check, auto-returns to Idle after 2.2s |
| Error | Red ✕ + message, auto-returns after 3s |

### Input Modes
- **Voice:** Android `RecognizerIntent` (speech-to-text), requires `RECORD_AUDIO` permission
- **Type:** WearOS `RemoteInput` keyboard, key `blurt_text`

### Config (build-time)
- `BuildConfig.DROPZONE_URL` — base URL of dropzone service
- `BuildConfig.DROPZONE_TOKEN` — bearer token for auth

These are baked into the APK at build time (set in `local.properties` or CI secrets).

---

## dropzone (mcglothi/dropzone) — HTTP Relay

**Repo:** `github.com/mcglothi/dropzone` (private)  
**Language:** Python, FastAPI + uvicorn  
**Host:** babbage (TrueNAS, 10.10.10.10)  
**Port:** 8080  
**Deploy:** Docker Compose via Dockge

### Compose Stack
```yaml
# compose.yaml (deployed from repo root on babbage)
volumes:
  - /mnt/VMs/mcglothi/Code/AIKB:/aikb       # AIKB repo mount
  - /mnt/Containers/dropzone:/data           # persistent data/env
  - .:/app                                   # app code
env_file: /mnt/Containers/dropzone/env
```

### Environment (`/mnt/Containers/dropzone/env`)
| Var | Required | Description |
|-----|----------|-------------|
| `DROPZONE_TOKEN` | Yes | Bearer token — must match blurt BuildConfig |
| `DROPZONE_SYNC_HOOK` | No | Shell command to run after each memo (git sync) |
| `DROPZONE_SYNC_HOOK_TIMEOUT` | No | Timeout in seconds (default 180) |
| `AIKB_ROOT` | Set in compose | Path to AIKB mount (default `/aikb`) |

### API
| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /health` | None | Returns `{"ok": true}` |
| `POST /memo` | Bearer token | Write note to AIKB ideas/inbox |

**MemoRequest schema:**
```json
{
  "text": "string (1–4096 chars)",
  "source": "blurt",
  "sender": null,
  "title": null,
  "tag": []
}
```

**What it does:**  
Calls `runtime_cli.py idea add --source blurt --text <text>` → note lands in `AIKB/ideas/inbox/YYYY-MM-DD/<slug>.md` with `status: open`. Returns `{"ok": true, "title": "<generated title>"}`.

### Sync Hook (`scripts/dropzone-aikb-sync.sh`)
Optional post-memo hook. When `DROPZONE_SYNC_HOOK` is set:
1. Runs `sync.sh --yes` if present (template refresh)
2. `git add -A && git commit -m "AI Update: <note slug> - <title>"`
3. `git push origin main`

Runs in a background thread — doesn't block the HTTP response.

**To enable:** add to env file:
```
DROPZONE_SYNC_HOOK=bash /app/scripts/dropzone-aikb-sync.sh
```

---

**Note (2026-04-24):** Blurt notes automatically appear in `_state.yaml.pending:` when captured via dropzone. Agents see them at session start via the wake-up routine's PENDING section (shown as `⬜ [awaiting triage]`).

When a blurt note is triaged (status changes from "open"), the pending entry is automatically removed.

Implementation: `runtime_cli.py` — `_sync_blurt_to_pending()` and `_remove_blurt_from_pending()`.

---

## Credentials

- `DROPZONE_TOKEN`: stored in Vaultwarden — `PAT/Dropzone/dropzone`  
  Retrieve: `BW_SESSION=$(cat ~/.bw_session) && bw get password "PAT/Dropzone/dropzone" --session "$BW_SESSION"`

---

## Status

- ✅ Blurt app (WearOS) — voice and typed notes work on watch
- ✅ Dropzone service — deployed and running on babbage. Port **8084** (host) → 8080 (container). Health: `{"ok":true}`. Actively receiving memos.
- ✅ SSH Newton → babbage — fixed. `~/.ssh/config` updated to use `svc_gemini`/`~/.ssh/svc_gemini`. Use `ssh babbage` or `ssh svc_gemini@10.10.10.10 -i ~/.ssh/svc_gemini`.
- ✅ Agent awareness gap — resolved in `runtime_cli.py` (blurt notes surface in `_state.yaml.pending:`)
- ✅ Auto-sync (aikb-sync.sh) — running on babbage via svc_ansible. Commits new ideas/inbox notes every ~10 min. **Note:** script updated 2026-04-24 to only track `ideas/` (was `ideas/ _runtime/`, which caused merge conflicts with Newton sessions).
