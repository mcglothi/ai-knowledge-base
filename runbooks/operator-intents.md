# Operator Intents

**Last Updated:** 2026-04-08
**Summary:** Phrase-to-action map for recurring shorthand requests. Use this when the operator says something short that implies a known workflow.

---

## Purpose

This runbook turns terse requests into explicit, repeatable actions.

Pattern:
- `Intent phrase` -> `Execution path` -> `Verify success` -> `Optional cleanup`

When an agent had to figure out a workflow once, capture it here so the next run is immediate.

---

## Starter Intents

### wrap up for now

- Intent phrase:
  - `lets wrap up for now`
  - `let's wrap up for now`
  - `lets shut down`
  - `let's shut down`
- Why this exists:
  - Session closeout is easy to do inconsistently. This shortcut ensures the agent checks memory updates, repo cleanliness, and any pending approvals before ending work.
- Execution path:
  - review meaningful repo changes
  - capture durable memory updates
  - summarize whether the repo is clean, ahead, or behind
  - call out any loose ends instead of implying a clean shutdown when one does not exist
- Verify success:
  - the operator receives a clear "safe to stop" versus "loose ends remain" summary
  - no stale active-session entry is left behind
  - pending approval or memory-queue state is called out explicitly when relevant
- Optional cleanup:
  - commit and push final changes if the operator wants a clean stop

### add an operator intent

- Intent phrase:
  - `remember this shortcut`
  - `add this as an operator intent`
- Why this exists:
  - Once a shorthand request takes more than one lookup step, it is worth capturing so the workflow becomes reusable.
- Execution path:

```bash
cp _templates/operator-intent-template.md /tmp/operator-intent-example.md
```

  - use the template to capture the exact phrase, execution path, verification steps, and optional cleanup
  - merge the new entry into this file before session end
- Verify success:
  - the next agent can execute the same shorthand request without rediscovering the path
- Optional cleanup:
  - if the command is broadly useful, also link to the owning service or project doc from `_index.md`

---

## Capture Rules

- Capture exact phrases people actually say, not polished rewrites.
- Prefer commands or steps that are deterministic and easy to verify.
- Include verification every time.
- Reference secrets by name in your secrets manager instead of writing them inline.
