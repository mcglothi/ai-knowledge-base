# v2 Trial Quickstart

## Goal
Run a live A/B pilot for compact instruction architecture v2 with minimal setup friction.

## One-command readiness + bootstrap
From AIKB root:

```bash
bash _tools/validation/run_v2_trial.sh claude-code
```

Other agents:

```bash
bash _tools/validation/run_v2_trial.sh codex
bash _tools/validation/run_v2_trial.sh gemini-cli
```

## In-session load order
1. `_agents/shared/core-min.md`
2. `_agents/v2/<agent>.overlay.md`
3. Keep `_agents/shared/session-min.md` for startup/closeout checks
4. Load L2 playbooks only when needed

## Pilot metrics log
Use:
- `_runtime/scratchpads/agent-instructions-v2-ab-pilot-checklist-2026-04-29.md`

Capture at least:
- IM trigger handling
- closeout completion
- compact consistency
- safety regressions
- token/context overhead trend

## Pass gate
- 3 successful B runs per agent class
- no critical safety regressions
- changelog updated with final deltas
