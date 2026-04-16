# Operator Intent Template

**Last Updated:** YYYY-MM-DD
**Summary:** Template for adding a phrase-to-action shortcut to `home-lab/runbooks/operator-intents.md` or another domain runbook.

---

### <Intent Name>

- Intent phrase:
  - `<short phrase 1>`
  - `<short phrase 2>`
- Why this exists:
  - `<why this request was ambiguous, slow, or easy to mis-execute>`
- Execution path:

```bash
<exact command sequence or step list>
```

- Verify success:

```bash
<verification command or checks>
```

- Optional cleanup:

```bash
<cleanup or rollback command>
```

---

## Capture Checklist

- exact phrase(s) the operator is likely to use
- command path that works reliably in the current environment
- post-condition verification
- cleanup or rollback steps when relevant
- host, credential, or tool assumptions
