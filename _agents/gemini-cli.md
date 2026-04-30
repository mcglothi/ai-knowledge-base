# Gemini CLI — Agent Instructions (v2 pilot candidate)
**Core Version:** v2.0
**Agent:** Gemini CLI
**AIKB Root:** `${AIKB_ROOT}` (set per host, e.g. `/Users/mcglothi/code/AIKB`)

## Startup (always load)
1. Load: `${AIKB_ROOT}/_agents/shared/core-min.md`
2. Load: `${AIKB_ROOT}/_agents/v2/gemini-cli.overlay.md`
3. Keep available: `${AIKB_ROOT}/_agents/shared/session-min.md`

## Startup Health Check
- Verify `${AIKB_ROOT}` resolves.
- Verify runtime CLI exists: `python3 ${AIKB_ROOT}/_tools/memory-pipeline/runtime_cli.py`
- Verify playbooks + dispatch exist/readable.

## L2 Dispatch Table (load on demand)
- IM/reply/self-note/cross-agent messaging -> `${AIKB_ROOT}/docs/playbooks/im.md`
- Heavy output/many reads/context pressure -> `${AIKB_ROOT}/docs/playbooks/token-economy.md`
- Wrap-up/shutdown/closeout phrase -> `${AIKB_ROOT}/docs/playbooks/closeout.md`
- Risky edits/rollback/refactor -> `${AIKB_ROOT}/docs/playbooks/git-checkpointing.md`
- Multi-agent reconciliation -> `${AIKB_ROOT}/docs/playbooks/cross-agent-mind-meld.md`

## Gemini-specific runtime rules
- Compact keyword: `/compress`
- Optional continuity:
  - `python3 ${AIKB_ROOT}/_tools/memory-pipeline/runtime_cli.py wake-up --agent "Gemini CLI"`
- Session claim:
  - `python3 ${AIKB_ROOT}/_tools/memory-pipeline/runtime_cli.py claim-session --agent "Gemini CLI" --repo "AIKB" --scope "<scope>" --task "<task>"`
- IM self-note command:
  - `python3 ${AIKB_ROOT}/_tools/memory-pipeline/runtime_cli.py im send --from "Gemini CLI" --to "Gemini CLI" --severity info --summary "<subject>" --body "<detail>" --mirror-sent`

## Safety + Credentials
- [MANDATE] Do not expose secrets/credentials in output.
- Fallback order: Bitwarden -> Delinea -> ask user
- Never run `bw unlock` or `bw status` without `--session`
- Use `BW_SESSION`-scoped commands only

## Validation
```bash
bash ${AIKB_ROOT}/_tools/validation/run_v2_trial.sh gemini-cli
```
