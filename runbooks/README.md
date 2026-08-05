# Runbooks

**Last Updated:** YYYY-MM-DD
**Summary:** Repeatable procedures and phrase-to-action shortcuts for recurring operator requests.

---

## Files

| File | Status | Description |
|------|--------|-------------|
| [`operator-intents.md`](operator-intents.md) | ⬜ Optional | Phrase-to-action shortcuts for recurring operator requests |

---

## What belongs here

- recurring operational procedures worth writing down once
- phrase-to-action shortcuts (operator intents)
- verification and rollback steps for routine work

Domain-specific runbooks can also live next to their domain — for example
`work/runbooks/` or a private `home-lab/runbooks/`. This folder is for
procedures that aren't tied to a single domain.

## Why operator intents matter

Operator intents turn shorthand requests into repeatable actions. If you often
say things like "restart staging", "wake server", or "wrap up for now", capture
the exact phrase, execution path, and verification steps once so future sessions
are faster and safer.

Use [`_templates/operator-intent-template.md`](../_templates/operator-intent-template.md)
to add a new entry.
