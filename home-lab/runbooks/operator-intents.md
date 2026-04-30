---
context: personal-homelab
tags: [operator-intents, shortcuts, runbook, wol, restart, repetitive-ops, phrase-map]
status: active
last_updated: 2026-03-09
---

# Operator Intents

**Last Updated:** 2026-03-09
**Summary:** Canonical phrase-to-action map for frequent operator commands. Use this file first for terse requests like "WoL feynman" or "restart ai.home".

---

## Purpose

This runbook turns recurring shorthand requests into explicit, repeatable actions with verification and cleanup steps.

Pattern:
- `Intent phrase` -> `Execution path` -> `Verify success` -> `Optional cleanup`

When an agent had to "figure out" a path once, add it here so next execution is immediate.

Shortcut CLI (v1):

```bash
~/code/AIKB/_tools/home-lab/cmd wol feynman
~/code/AIKB/_tools/home-lab/cmd status feynman
~/code/AIKB/_tools/home-lab/cmd shutdown feynman --yes
```

Session workflow shortcuts:

```bash
~/code/AIKB/_tools/home-lab/aikb start
~/code/AIKB/_tools/home-lab/aikb status
~/code/AIKB/_tools/home-lab/aikb stop
```

Tip: symlink for shorter typing:

```bash
mkdir -p ~/.local/bin
ln -sf ~/code/AIKB/_tools/home-lab/cmd ~/.local/bin/cmd
```

---

## Intents

### cmd: calibrate memory

- Intent phrase:
  - `cmd: calibrate memory`
  - `calibrate memory`
- Why this exists:
  - Proposal queues can accumulate mixed-quality memories. This shortcut triggers a policy-learning cleanup pass that groups items into patterns, minimizes manual review, and promotes durable knowledge into canonical AIKB docs/state.
- Execution path:
  - Review the live AIKB Memory Core proposal queue.
  - Group proposals into patterns instead of treating every item as unique.
  - Recommend default actions by pattern: `reject`, `approve`, `apply`, or `keep for follow-up`.
  - Surface only the smallest ambiguous set for the user.
  - Learn from the user's calls during the pass and apply that policy consistently to the rest of the queue.
  - Promote durable product backlog, runbook knowledge, workflow intent, and already-documented facts into canonical AIKB docs/state when appropriate.
  - Reject transient chatter, speculative advice, implementation progress blurts, duplicate fact/task copies, and stale debugging noise.
  - End with a summary of learned patterns, queue actions taken, and upstream rule changes to make future review faster.
- Default policy:
  - Keep domain behavior and real workflow/automation intent.
  - Auto-apply things that are already documented or should clearly become canonical backlog/docs.
  - Reject speculative, partial-progress, advisory, and transient operational chatter.
  - Only turn confirmations into tasks when they include meaningful feature/detail text.
  - If something looks important but is not yet verified in-repo, keep it as follow-up instead of overstating it.
- Verify success:
  - Proposal queue meaningfully reduced or cleared.
  - Canonical AIKB docs/state updated for anything durable that was preserved.
  - A short policy summary captured in the final response so the same calibration logic can be reused next time.
- Optional cleanup:
  - If a new decision pattern emerged, update Memory Core harvest/hygiene rules or agent instructions so the same noise does not return.
  - Automatically delete source `.yaml` files from `_runtime/candidates/` once all items within them are in a terminal state (`merged` or `rejected`).

### let's shut down for now

- Intent phrase:
  - `lets shut down for now`
  - `let's shut down for now`
  - `lets shut down for the day`
  - `let's shut down for the day`
  - `wrap up for the day`
- Why this exists:
  - Ending a session should not leave silent loose ends behind. This shortcut forces a quick end-of-day operational check before stopping.
- Execution path:
  - Capture structured closeout memory first:

```bash
~/code/AIKB/_tools/home-lab/aikb closeout --phrase "lets shut down for now"
```

  - Check AIKB git status and call out any uncommitted or untracked changes.
  - Distinguish meaningful repo changes from transient artifacts like `__pycache__`, `.pyc`, journals, or scratch outputs.
  - Check whether the proposal queue still has `new` items.
  - Check `_agents/active.md` so no stale active-session entry is left behind.
  - Summarize whether there is any obvious commit, push, cleanup, or review work still pending before shutdown.
  - If the repo is dirty, do not imply that shutdown is clean; explicitly say what is still open.
- Verify success:
  - The user gets a clear “safe to stop” vs “here are the loose ends” summary.
  - No active-session bookkeeping is left behind.
  - Memory queue state is called out explicitly.
- Optional cleanup:
  - If requested, clean transient artifacts, stage real changes, commit, and push before ending the session.

### start AIKB session

- Intent phrase:
  - `start AIKB session`
  - `aikb-start`
  - `aikb start`
  - `sync me up`
- Why this exists:
  - Consistent cross-workstation startup should always refresh memory + instruction files + vault session status before work begins.
- Execution path:
  - Run:

```bash
~/code/AIKB/_tools/home-lab/aikb start
```

  - Optional full repo instruction sync:

```bash
~/code/AIKB/_tools/home-lab/aikb start --sync-repos
```

- Verify success:
  - AIKB pull succeeded (`ff-only`)
  - `~/.claude/CLAUDE.md` and `~/.gemini/GEMINI.md` were refreshed
  - Bitwarden session check reported unlocked or prompted to run `bwu`

### wrap AIKB session

- Intent phrase:
  - `wrap AIKB session`
  - `aikb-wrap`
  - `aikb stop`
  - `aikb status`
  - `check before shutdown`
- Why this exists:
  - Standardized closeout status check before final commit/push and shutdown.
- Execution path:
  - Run:

```bash
~/code/AIKB/_tools/home-lab/aikb status
# or
~/code/AIKB/_tools/home-lab/aikb stop
```

- Verify success:
  - Branch/upstream state displayed
  - Dirty/untracked files are visible before deciding commit/push actions

### WoL feynman

- Intent phrase:
  - `WoL feynman`
  - `wake feynman`
- Why this exists:
  - WoL tooling is not always installed on the caller host. TrueNAS is a reliable relay on the home LAN.
- Execution path:
  - Send magic packet from TrueNAS relay using the 10G MAC (`6c:fe:54:1c:61:80`):

```bash
cd /Users/mcglothi/code/ansible
ANSIBLE_LOCAL_TEMP=/tmp ANSIBLE_REMOTE_TEMP=/tmp ANSIBLE_SSH_CONTROL_PATH_DIR=/tmp \
ansible -i ai/inventory.ini truenas -b -m shell -a \
"python3 -c \"import socket; mac='6cfe541c6180'; magic=bytes.fromhex('ff'*6 + mac*16); s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1); s.sendto(magic, ('<broadcast>', 9)); print('wol_sent')\""
```

- Verify success:
  - Ping until host responds (`10.10.145.26`), then verify SSH:

```bash
for i in {1..30}; do
  ping -c 1 -W 1 10.10.145.26 >/dev/null 2>&1 && { echo "feynman_up attempt=$i"; break; }
  sleep 2
done

ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new mcglothi@10.10.145.26 'hostname && whoami'
```

- Optional cleanup:
  - Shut down after task completion:

```bash
ssh -o StrictHostKeyChecking=accept-new mcglothi@10.10.145.26 'sudo systemctl poweroff'
```

---

### Full Deployment

- Intent phrase:
  - `Full Deployment`
- Why this exists:
  - Standardized multi-step workflow for new services to ensure they are production-ready.
- Execution path:
  - Check/Update DNS in Pi-hole.
  - Check/Update Proxy in NPM.
  - Check/Update SSL in Vaultwarden/Cloudflare.
  - Deploy service (systemd/docker).
  - Update AIKB documentation.
- Verify success:
  - Service is reachable at the internal/external domain.
  - SSL cert is valid.
  - AIKB docs are current.

### POC (Proof of Concept)

- Intent phrase:
  - `POC`
  - `Proof of Concept`
- Why this exists:
  - Quick, local-only setup for testing ideas without overhead.
- Execution path:
  - Local-only installation/run.
  - Ignore Pi-hole, NPM, SSL, and AIKB updates (initially).
  - Minimize dependency checks.
- Verify success:
  - Feature/Idea is demonstrably working.

### Session Compact

- Intent phrase:
  - `Session Compact`
  - `Compact Session`
  - `Summarize and Restart`
- Why this exists:
  - Context bloat causes AI degradation. This intent forces a summary to AIKB and a fresh session.
- Execution path:
  - Summarize session state, decisions, and progress to AIKB.
  - Update `session_state.md` if applicable.
  - Suggest starting a new session.
- Verify success:
  - AIKB is updated.
  - New session is ready with fresh context.

---

## Capture Rule

If a terse operator request required more than one lookup/search step, add or update an entry in this file before session end.

Capture checklist:
- exact intent phrase(s)
- authoritative execution path
- verification command(s)
- rollback/cleanup when relevant
- required host/context assumptions
