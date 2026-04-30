# Claude Code — Agent Instructions (v2 pilot candidate)
**Core Version:** v2.0
**Agent:** Claude Code
**AIKB Root:** `${AIKB_ROOT}` (set per host, e.g. `/Users/mcglothi/code/AIKB`)

## Startup (always load)
1. Load: `${AIKB_ROOT}/_agents/shared/core-min.md`
2. Load: `${AIKB_ROOT}/_agents/v2/claude-code.overlay.md`
3. Keep available: `${AIKB_ROOT}/_agents/shared/session-min.md`

## Startup Health Check
- Verify `${AIKB_ROOT}` resolves.
- Verify runtime CLI exists: `python3 ${AIKB_ROOT}/_tools/memory-pipeline/runtime_cli.py`
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

## Claude-specific runtime rules
- Compact keyword: `/compact`
- Optional continuity:
  - `python3 ${AIKB_ROOT}/_tools/memory-pipeline/runtime_cli.py wake-up --agent "Claude Code"`
- Session claim:
  - `python3 ${AIKB_ROOT}/_tools/memory-pipeline/runtime_cli.py claim-session --agent "Claude Code" --repo "AIKB" --scope "<scope>" --task "<task>"`
- IM self-note command:
  - `python3 ${AIKB_ROOT}/_tools/memory-pipeline/runtime_cli.py im send --from "Claude Code" --to "Claude Code" --severity info --summary "<subject>" --body "<detail>" --mirror-sent`

## Safety + Credentials
- [MANDATE] Do not expose secrets/credentials in output.
- Fallback order: Bitwarden -> Delinea -> ask user
- Never run `bw unlock` or `bw status` without `--session`
- Use `BW_SESSION`-scoped commands only

## Compact triggers (must enforce)
- Subtask done
- Tool output > 50 lines
- 3+ file reads in sequence
- ~40 turns / high context pressure

Before compact, run runtime capture decision summary.

## Wrap-up behavior
Trigger phrases:
- "lets wrap up" | "let's wrap up" | "lets shut down" | "let's shut down"

On trigger:
1. Load closeout playbook
2. Run closeout checklist
3. Report: completed, pending, blockers

## Validation
```bash
bash ${AIKB_ROOT}/_tools/validation/run_v2_trial.sh claude-code
```
