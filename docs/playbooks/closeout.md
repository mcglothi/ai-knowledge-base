# Closeout Playbook (v2)

## When to Load
- User indicates wrap-up/shutdown/closeout intent.

## Wrap-up Trigger Phrases
- "lets wrap up"
- "let's wrap up"
- "lets shut down"
- "let's shut down"

## Closeout Checklist
1. Persist AIKB updates made this session (`_index.md`, `_state.yaml`, project docs where relevant).
2. Commit and push relevant repositories.
3. Run session stop hook/script if configured.
4. Report final status: done, pending, blockers.
5. If process requires, remove session entry from `_agents/active.md`.

## Output Format
- What changed
- What remains
- Next recommended action
