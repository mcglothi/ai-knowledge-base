# Cursor — Agent Instructions

**Config:** Settings → Cursor Settings → Rules → User Rules
**Source of truth:** `{{LOCAL_PATH}}/_agents/cursor.md`

After editing, re-paste into Cursor Settings.

---

## Paste everything below this line into Cursor User Rules

---

# Global Agent Instructions

## AI Knowledge Base (AIKB)

I maintain a private GitHub repo (`{{GITHUB_USERNAME}}/{{REPO_NAME}}`) as a persistent knowledge base for all my projects, machines, and work context. You should read relevant files from it when they're useful for the current task. The local clone is at `{{LOCAL_PATH}}`.

---

### At the start of a session (when relevant)

1. Read `{{LOCAL_PATH}}/_index.md` — one-row-per-project orientation
2. Read `{{LOCAL_PATH}}/_state.yaml` — time-sensitive items (SSL expiry, incidents)
3. Load specific project files only when they're relevant to the current task

Do not bulk-load everything. Load only what the task requires.

---

### When to update AIKB

Update AIKB files when you learn something useful for future sessions:
- Task completed or failed
- New gotcha discovered
- Decision made with rationale worth preserving
- System state changed

Write updates directly to files in `{{LOCAL_PATH}}`, then commit:
```bash
git -C {{LOCAL_PATH}} add . && git -C {{LOCAL_PATH}} commit -m "AI Update: [file] — [what changed]" && git -C {{LOCAL_PATH}} push origin main
```

---

### Security

Never store credentials in AIKB files. Use: `[Stored in {{SECRETS_MANAGER}}: Name/Of/Item]`

---

### Machine context

I work from multiple machines. Check `personal/dev-environment/README.md` for the machine table. Apply the correct package manager and paths for the current machine.
