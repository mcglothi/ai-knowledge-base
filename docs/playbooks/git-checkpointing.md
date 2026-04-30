# Git Checkpointing Playbook (v2)

## When to Load
- Before risky operations, multi-file edits, or long-running changes.

## Checkpoint Rules
- Commit at phase boundaries.
- Commit before risky refactors.
- Keep commits small and focused.
- Use branches for harder-to-reverse changes.

## AIKB Write Rules (parity)
- Edit in place where possible.
- Update `Last Updated` when modifying canonical docs.
- Update `_index.md` when status changes.
- Update `_state.yaml` when incident/SSL cert/pending-item state changes.

## Project Repo Branching Guidance
- Main branch: typos/minor docs only.
- Branch required: features, assets, harder-to-reverse changes.
- Pattern: `git checkout -b claude/<desc>` -> `git push -u origin HEAD` -> `gh pr create --fill`
- Binary assets: use new filename (CDN cache safety).

## Template Sync Safety
- Use `runtime_cli.py template-sync --auto-check` (weekly cadence).
- Never run `./sync.sh` without explicit approval.

## Minimal Flow
1. Inspect status/diff.
2. Stage targeted files.
3. Commit with scoped message.
4. Push branch or main per repo policy.
