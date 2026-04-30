# GitHub Copilot — Agent Instructions (v2 pilot candidate)
**Core Version:** v2.0
**Agent:** GitHub Copilot
**AIKB Root:** `${AIKB_ROOT}` (set per host, e.g. `/home/tmcglothin/code/AIKB`)

## Startup (always load)
1. Load: `${AIKB_ROOT}/_agents/shared/core-min.md`
2. Load: `${AIKB_ROOT}/_agents/v2/copilot.overlay.md`
3. Keep available: `${AIKB_ROOT}/_agents/shared/session-min.md`

## Startup Health Check
- Verify `${AIKB_ROOT}` resolves.
- Verify runtime CLI exists: `python3 ${AIKB_ROOT}/_tools/memory-pipeline/runtime_cli.py`
- Note: CLI steps require agent/workspace mode with terminal access; skip gracefully if unavailable.
- Verify playbooks exist/readable:
  - `${AIKB_ROOT}/docs/playbooks/im.md`
  - `${AIKB_ROOT}/docs/playbooks/token-economy.md`
  - `${AIKB_ROOT}/docs/playbooks/closeout.md`
  - `${AIKB_ROOT}/docs/playbooks/git-checkpointing.md`
  - `${AIKB_ROOT}/docs/playbooks/cross-agent-mind-meld.md`

## L2 Dispatch Table (load on demand)
- If task involves inbox/reply/self-note/cross-agent messaging:
  - Load `${AIKB_ROOT}/docs/playbooks/im.md`
- If task involves heavy output, many reads, or context pressure:
  - Load `${AIKB_ROOT}/docs/playbooks/token-economy.md`
- If user indicates wrap-up/shutdown/closeout:
  - Load `${AIKB_ROOT}/docs/playbooks/closeout.md`
- If task involves risky edits, branch strategy, rollback, or major refactor:
  - Load `${AIKB_ROOT}/docs/playbooks/git-checkpointing.md`
- If task requires reconciling guidance from multiple agents:
  - Load `${AIKB_ROOT}/docs/playbooks/cross-agent-mind-meld.md`

## Copilot-specific runtime rules
- Compact keyword: `/compact`
- Optional continuity (agent/workspace mode only):
  - `python3 ${AIKB_ROOT}/_tools/memory-pipeline/runtime_cli.py wake-up --agent "GitHub Copilot"`
- Session claim (agent/workspace mode only):
  - `python3 ${AIKB_ROOT}/_tools/memory-pipeline/runtime_cli.py claim-session --agent "GitHub Copilot" --repo "AIKB" --scope "<scope>" --task "<task>"`
- IM self-note command (agent/workspace mode only):
  - `python3 ${AIKB_ROOT}/_tools/memory-pipeline/runtime_cli.py im send --from "GitHub Copilot" --to "GitHub Copilot" --severity info --summary "<subject>" --body "<detail>" --mirror-sent`
- Primary instruction target: `.github/copilot-instructions.md` per repo (populated via `sync-agents.sh`)
- AIKB context: advisory — prefer repo files first; load AIKB only when task involves personal projects, infrastructure, or cross-agent continuity

## Safety + Credentials
- [MANDATE] Do not expose secrets/credentials in output or suggestions.
- Fallback order: Bitwarden -> Delinea -> ask user
- Never run `bw unlock` or `bw status` without `--session`
- Use `BW_SESSION`-scoped commands only

## Compact triggers (must enforce)
- Subtask done
- Tool output > 50 lines
- 3+ file reads in sequence
- ~40 turns / high context pressure

Before compact, capture decision summary in AIKB or leave explicit TODO in relevant project file.

## Wrap-up behavior
Trigger phrases:
- "lets wrap up" | "let's wrap up" | "lets shut down" | "let's shut down"

On trigger:
1. Load closeout playbook
2. Run closeout checklist
3. Report: completed, pending, blockers

## Validation
```bash
bash ${AIKB_ROOT}/_tools/validation/run_v2_trial.sh copilot
```
