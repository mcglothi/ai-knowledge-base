---
context: personal-homelab
---
# Goose Telegram Reliability Migration Plan (Newton → Turing/Hopper)

**Last Updated:** 2026-04-29  
**Status:** Planned (execute tomorrow)

## Goal
Ensure Telegram messages are always received by Goose even when Newton is offline by moving the Telegram gateway to an always-on host (Turing or Hopper).

## Current Observation
Newton currently has active Telegram gateway pairing in Goose config. If Newton is offline, Telegram messages are not processed in real time.

## Success Criteria
- Telegram bot remains responsive while Newton is powered off.
- Goose gateway process auto-starts on reboot of host machine.
- Health-check command and rollback path are documented.

## Phase 1 — Preflight (15–20 min)
- [ ] Choose primary host: **Turing** or **Hopper** (must be always on).
- [ ] Verify Goose is installed on chosen host and can run interactively.
- [ ] Confirm required credentials/providers on host (same LLM/provider config).
- [ ] Snapshot current Newton config for backup:

```bash
cp ~/.config/goose/config.yaml ~/.config/goose/config.yaml.pre-migration.$(date +%Y%m%d%H%M%S)
```

## Phase 2 — Migrate Telegram Pairing (20–30 min)
### Option A (Preferred): Re-pair cleanly on host
- [ ] Start Goose on host.
- [ ] Enable/configure Telegram gateway on host.
- [ ] Pair Telegram account with host Goose instance.
- [ ] Send test message and verify reply.

### Option B (Faster, more fragile): Copy pairing state
- [ ] Copy only needed gateway sections from Newton config to host config.
- [ ] Restart Goose on host.
- [ ] Validate by sending Telegram test message.

## Phase 3 — Run as Service (30–45 min)
- [ ] Configure auto-start service on host (systemd/launchd, per OS).
- [ ] Set restart policy (`always` or `on-failure`).
- [ ] Start service and verify it survives process kill and reboot.
- [ ] Capture service logs location/command for troubleshooting.

## Phase 4 — Cutover + Validation (15–20 min)
- [ ] Power off or disconnect Newton from network.
- [ ] Send Telegram messages (simple + multi-turn).
- [ ] Confirm session continuity and timely responses.
- [ ] Confirm no duplicate responders (Newton gateway disabled).

## Phase 5 — Newton as Client (10 min)
- [ ] Keep Newton for interactive/local work only.
- [ ] Disable Telegram gateway on Newton to avoid split-brain.
- [ ] Document source of truth: host owns Telegram gateway.

## Operational Guardrails
- [ ] Add a daily/boot health-check command (service status + recent logs).
- [ ] Optional alerting: notify if Goose service is down > N minutes.
- [ ] Keep timestamped config backups before each change.

## Rollback Plan
- [ ] Stop Goose Telegram service on host.
- [ ] Restore Newton config backup.
- [ ] Re-enable Newton gateway and verify Telegram replies.

## Execution Order (Tomorrow)
1. Pick host (Turing/Hopper)
2. Backup configs (both machines)
3. Re-pair Telegram on host
4. Set up service + restart policy
5. Test with Newton offline
6. Disable Newton gateway
7. Final verification + notes

## Decisions Needed
- [ ] Which host: Turing or Hopper?
- [ ] Re-pair vs config-copy approach?
- [ ] Enable alerting on day 1?
