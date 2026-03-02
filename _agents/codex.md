# Codex CLI — Global Agent Instructions

**Config location:** `AGENTS.md` in the current repository root
**Sync command:** `cp {{LOCAL_PATH}}/_agents/codex.md {project_root}/AGENTS.md`

> This file is the source of truth for Codex behavior in AIKB-enabled projects.

---

## File content (copy everything below this line)

---

# Codex — Global Agent Instructions

## AI Knowledge Base (AIKB)

All personal projects, infrastructure, and work context are documented in AIKB — a private GitHub repo (`{{GITHUB_USERNAME}}/{{REPO_NAME}}`) that serves as persistent memory across sessions and machines.

AIKB is accessed in one of two modes depending on whether a local clone exists. Determine the mode at the start of each session.

---

### Step 1 — Identify the machine

Run `hostname` and match it to `personal/dev-environment/README.md`.

Default AIKB path: `{{LOCAL_PATH}}`

If hostname is unknown, probe with:
- `uname -s`
- `uname -m`
- `which brew || which apt || which dnf || which pacman`
- `python3 --version`

If the session is substantial, create `personal/dev-environment/<hostname>.md`.

---

### Step 2 — Check for local AIKB clone (sets access mode)

```bash
ls {{LOCAL_PATH}}
```

#### Local mode (clone exists)

1. Pull first: `git -C {{LOCAL_PATH}} pull`
2. Read/write files directly
3. Commit and push updates

```bash
git -C {{LOCAL_PATH}} add . && git -C {{LOCAL_PATH}} commit -m "AI Update: [file] — [what changed]" && git -C {{LOCAL_PATH}} push origin main
```

#### MCP mode (no local clone)

Use `github-aikb` MCP against `{{GITHUB_USERNAME}}/{{REPO_NAME}}` on `main`.

- Read: `get_file_contents`
- Write: `create_or_update_file` (include SHA for updates)
- Keep commit message format consistent with local mode

---

### Step 3 — Load orientation files

Read in this order:
1. `_index.md`
2. `_state.yaml`
3. `personal/dev-environment/README.md`
4. `personal/dev-environment/<hostname>.md`

Load only files relevant to the current task. Do not bulk-load entire domains.

---

### Step 3b — Active session coordination

Read and update `_agents/active.md`:
1. If another agent wrote recently (~2 hours), pull before each write
2. Add/update row:
   `| Codex CLI | <hostname> | local/MCP | <timestamp> | <brief task> |`
3. Commit this as first session write
4. Remove your row and commit as final session write

---

### Credentials

All API tokens and service keys are stored in {{SECRETS_MANAGER}}.

Never store credentials in AIKB. Reference secrets by name only:

```markdown
[Stored in {{SECRETS_MANAGER}}: Service/Project/KeyName]
```

---

### When to update AIKB

Update AIKB before ending sessions that produced reusable information:
- System state changed
- Tasks completed or blockers discovered
- Incidents resolved
- New gotchas discovered

Rules:
- Edit in place
- Update `Last Updated` on every touched markdown file
- Update `_index.md` when project status changes
- Update `_state.yaml` when incidents/pending/cert dates change
- Use `⚠️ IN PROGRESS` markers for partial handoffs

---

### Session resilience

Use checkpoint commits during long sessions:
- After major phases
- Before risky operations
- Before context-heavy transitions

Prefer small focused commits to reduce merge conflicts in multi-agent workflows.
