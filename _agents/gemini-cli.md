# Gemini CLI — Global Agent Instructions

**Config location:** `~/.gemini/GEMINI.md`
**Sync command:** `cp {{LOCAL_PATH}}/_agents/gemini-cli.md ~/.gemini/GEMINI.md`

> This file is the source of truth. The live config at `~/.gemini/GEMINI.md` should always match it.

---

## File content (copy everything below this line)

---

# Global Agent Instructions

## AI Knowledge Base (AIKB)

All personal projects, infrastructure, and work context are documented in the AIKB — a private GitHub repo (`{{GITHUB_USERNAME}}/{{REPO_NAME}}`) that serves as persistent memory across sessions and machines.

---

### Step 1 — Identify the machine

Run `hostname`. Match it against the machine table in `personal/dev-environment/README.md`.

Default AIKB path: `{{LOCAL_PATH}}`

**Unrecognized hostname:** probe with `uname -s`, `uname -m`, `which brew || which apt || which dnf || which pacman`, `python3 --version`. If the session will produce useful work, create `personal/dev-environment/<hostname>.md`.

---

### Step 2 — Check for local clone

```bash
ls {{LOCAL_PATH}}
```

#### Local mode (clone exists)
1. Pull: `git -C {{LOCAL_PATH}} pull`
2. Read files from the filesystem
3. Write, commit, push:
```bash
git -C {{LOCAL_PATH}} add . && git -C {{LOCAL_PATH}} commit -m "AI Update: [file] — [what changed]" && git -C {{LOCAL_PATH}} push origin main
```

#### MCP mode (no local clone)
Use the `github-aikb` MCP server if configured. Repo: `{{GITHUB_USERNAME}}/{{REPO_NAME}}`, branch: `main`.

---

### Step 3 — Load orientation files

Read in order:
1. `_index.md` — project orientation
2. `_state.yaml` — time-sensitive items
3. `personal/dev-environment/README.md` — machine table
4. `personal/dev-environment/<hostname>.md` — full machine profile

Apply the machine profile to all commands — use the right package manager, paths, Python version.

---

### When to update the AIKB

Update before finishing any session that produced information a future agent would need. Edit in place, update `Last Updated`, commit and push immediately.

**Never store credentials in AIKB.** Use: `[Stored in {{SECRETS_MANAGER}}: Name/Of/Item]`

---

### Checkpoint commits

Commit at logical checkpoints — don't wait until the end. Use in-progress markers:
`⚠️ IN PROGRESS — picked up by next session`

Replace with `✅` when complete.
