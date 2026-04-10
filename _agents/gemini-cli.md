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

### Active session coordination

Read and update `_agents/active.md`:
1. If another agent has a recent Last Write (~2 hours), pull before every write this session.
2. Add or update your row: `| Gemini CLI | <hostname> | local/MCP | <timestamp> | <repo name or AIKB> | <scope/path glob> | <brief task> |`
   Preferred helper:
   `python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py claim-session --agent "Gemini CLI" --repo "<repo>" --scope '<scope>' --task "<task>"`
3. For work outside AIKB itself, claim the external repo and the narrowest useful scope you can describe.
4. If you encounter unexpected modified/untracked files, or any other evidence of work you did not create, re-read `_agents/active.md` and run `python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py check-repo --path <repo-or-file>` before editing. Treat dirty unclaimed repos as possible crash-recovery work until proven otherwise.
5. Commit this as your first AIKB write of the session.
6. At session end: remove your row and commit as the final write.
   Preferred helper:
   `python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py release-session --agent "Gemini CLI"`

---

### Wrap-up workflow

When the operator uses a closing phrase like `lets wrap up for now` or `let's shut down`, perform these steps before ending the session:

1. **Capture Closeout:** If runtime tools are available, record a structured closeout event:
   `python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py closeout --phrase "<operator phrase>"`
2. **Build Temporal Graph:** Update the entity graph:
   `python3 {{LOCAL_PATH}}/_tools/memory-pipeline/build_temporal_graph.py`
3. **Run Dream Cycle:** Distill the session's memories:
   `python3 {{LOCAL_PATH}}/_tools/memory-pipeline/dream_cycle.py`
4. **Final Sync:** Add, commit, and push all changes (including `_runtime/` updates) to the remote repository.
5. **Release Session:** Remove your entry from `_agents/active.md`.
