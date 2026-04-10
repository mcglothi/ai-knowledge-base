# Pending Approvals Log

**Last Updated:** 2026-04-08
**Summary:** Central registry for agents to post decisions or actions requiring human sign-off.

---

| Date | Agent | Project | Action/Decision | Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-04-08 | Template | AIKB | Initialize `_pending_approvals.md` | Approved | Ready for agent use. |

---

## Instructions for Agents

1. **When to post:** If a decision has architectural, security, financial, or preference risk, or if you're unsure what the operator wants.
2. **Format:** Add a row with `Pending` status. Include enough context in the Notes column for quick review from mobile or desktop.
3. **Resolution:** Only proceed once the status is updated to `Approved` or an equivalent done state.

---

## Examples

| Situation | Good approval row |
| :--- | :--- |
| Public launch change | `Publish docs redesign` with notes about visibility and rollback |
| Infra spend | `Provision hosted vector DB` with notes about monthly cost |
| Preference ambiguity | `Switch default model to Claude` with notes about tradeoffs |
| Security-sensitive action | `Open external port for demo` with notes about exposure window |
