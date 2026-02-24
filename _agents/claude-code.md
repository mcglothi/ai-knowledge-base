# Claude Code — Global Agent Instructions

**Config location:** `~/.claude/CLAUDE.md`
**Sync command:** `cp {{LOCAL_PATH}}/_agents/claude-code.md ~/.claude/CLAUDE.md`

> This file is the source of truth. The live config at `~/.claude/CLAUDE.md` should always match it.
> After editing here, run the sync command above and commit the change.

---

## File content (copy everything below this line)

---

# Global Agent Instructions

## AI Knowledge Base (AIKB)

All personal projects, infrastructure, and work context are documented in the AIKB — a private GitHub repo (`{{GITHUB_USERNAME}}/{{REPO_NAME}}`) that serves as persistent memory across sessions and machines.

AIKB is accessed in one of two modes depending on whether a local clone exists. Determine the mode at the start of each session.

---

### Step 1 — Identify the machine

Run `hostname`. Match it to the table below (edit this table when you add or remove machines):

| Hostname | OS | Code root | AIKB local path |
|----------|----|-----------|-----------------|
| {{PRIMARY_HOSTNAME}} | — | `~/Code/` | `{{LOCAL_PATH}}` |

**Unrecognized hostname:**
Run `uname -s` — Darwin = macOS, Linux = Linux. Probe for package manager: `which brew || which apt || which dnf || which pacman`. If the session will produce useful work, create a machine profile at `personal/dev-environment/<hostname>.md`.

---

### Step 2 — Check for local AIKB clone

```bash
ls {{LOCAL_PATH}}
```

---

#### Local mode (clone exists) — preferred

1. Pull to ensure fresh: `git -C {{LOCAL_PATH}} pull`
2. Read files directly from the filesystem
3. Write updates directly to files, commit, and push

**Commit format:**
```bash
git -C {{LOCAL_PATH}} add . && git -C {{LOCAL_PATH}} commit -m "AI Update: [file] — [what changed]" && git -C {{LOCAL_PATH}} push origin main
```

**Checkpoint commit (mid-session):**
```bash
git -C {{LOCAL_PATH}} add . && git -C {{LOCAL_PATH}} commit -m "AI Checkpoint: [file] — [done so far / still in progress]" && git -C {{LOCAL_PATH}} push origin main
```

---

#### MCP mode (no local clone) — online only

Use the `github-aikb` MCP server. Repo: `{{GITHUB_USERNAME}}/{{REPO_NAME}}`, branch: `main`.

Note at session start: running in MCP mode — online only. Writes go directly to GitHub as commits.

**Reading:** `get_file_contents` tool with repo `{{GITHUB_USERNAME}}/{{REPO_NAME}}` and the file path.

**Writing:** `create_or_update_file` tool. Each write creates a commit. Include the current file SHA when updating existing files (retrieve it with `get_file_contents` first).

**After a substantial MCP session:** clone the repo so future sessions use local mode:
```bash
git clone https://github.com/{{GITHUB_USERNAME}}/{{REPO_NAME}}.git {{LOCAL_PATH}}
```

---

### Step 3 — Load orientation files

Whether in local or MCP mode, read in this order:
1. `_index.md` — one-row-per-project orientation
2. `_state.yaml` — time-sensitive surface (SSL expiry, incidents, pending items)
3. `personal/dev-environment/README.md` — machine table, confirm code root and tools
4. `personal/dev-environment/<hostname>.md` — machine profile (package manager, installed tools, paths)

Apply the machine profile to all commands in the session. Use the machine's package manager, paths, and Python version. Do not assume a tool is available unless it's listed in the Installed Tools section.

---

### Step 3b — Register in active sessions

Read and update `_agents/active.md`:
1. If another agent has a Last Write within ~2 hours, pull before every write this session.
2. Add or update your row: `| Claude Code | <hostname> | local/MCP | <timestamp> | <brief task> |`
3. Commit this as your first AIKB write of the session.
4. At session end: remove your row and commit as the final write.

---

### Step 4 — Load project context (when needed)

**Trigger topics that warrant loading AIKB project files:**
- Personal background, skills, dev environment, local paths
- Any project listed in `_index.md` that's relevant to the current task
- Infrastructure, client work, self-hosted services

**For unrelated tasks** (general coding questions, throwaway scripts) — skip AIKB loading.

**Before loading any project file — choose a retrieval strategy:**

| Query type | Strategy |
|------------|----------|
| You know the domain | Grep `_index.md` tags, load matched file |
| Freeform / diagnostic | Use `aikb_search` MCP tool if available |
| Cross-system queries | Grep `hosts:` frontmatter across files |

Load only files whose tags match the current task. Do not bulk-load entire domain folders.

---

### Credentials

All API tokens and service keys are stored in {{SECRETS_MANAGER}}.

**Retrieve a credential:**
```bash
{{SECRETS_RETRIEVE}}
```

**Naming convention:** use a consistent hierarchical name like `Service/Project/KeyName` so agents can reference them unambiguously.

**Never store credentials in AIKB.** Reference them by name only:
```markdown
[Stored in {{SECRETS_MANAGER}}: Service/Project/KeyName]
```

---

### When to update the AIKB

Update before finishing any session that produced information a future agent would need:
- Changed system state, completed tasks, discovered pitfalls, resolved incidents
- **Security:** never save clear-text passwords or keys — use `[Stored in {{SECRETS_MANAGER}}: <Name>]`
- Edit in place — never append corrections below stale content
- Update `Last Updated` on every file you touch
- Update `_index.md` if a project's status changes
- Update `_state.yaml` when SSL certs, incidents, or pending items change

**`_state.yaml` maintenance rules:**

| Event | Action |
|-------|--------|
| New incident or blocker | Add to `open_incidents` or `pending` |
| Incident resolved | Remove the entry entirely |
| SSL cert renewed | Update `expires` and `warn_after` dates |
| Any file modified this session | Add/update in `recently_changed` (keep last ~10) |

Update `_state.yaml` in the same commit as the related file — never let them drift apart.

---

### Session resilience — checkpoint commits

Commit at logical checkpoints, not just at the end:
- A discrete phase of work completes
- A significant decision is made worth preserving
- A long-running background process is started
- Before any risky or hard-to-reverse operation
- The conversation has grown long — checkpoint what's been learned

**In-progress marker:** add `⚠️ IN PROGRESS — picked up by next session` at the top of the relevant file. Replace with `✅` when complete.
