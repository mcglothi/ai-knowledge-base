# AIKB — Repository Instructions

You are working inside an **AIKB** repo (AI Knowledge Base): a Git-backed, human-readable
memory store that AI agents read and write across sessions, tools, and machines.

This repo has two modes. **Determine which one you are in before doing anything else.**

---

## Step 1 — Which mode am I in?

```bash
python3 _tools/memory-pipeline/doctor.py --onboarding --json
```

- **`installer run` is `FAIL`** → this is a fresh, unconfigured clone.
  Go to **Onboarding mode** below.
- **otherwise** → setup is done. Go to **Normal operation** below.

If Python is unavailable, fall back to: does `.aikb-config.d/` exist? No → onboarding.

Do not skip this check. The instructions in `_agents/` assume setup is already
complete and will not make sense on a fresh clone.

---

## Onboarding mode — setup is not finished

**Load `docs/playbooks/onboarding.md` and follow it.** That playbook is the procedure;
this section is only the trigger.

The short version of what you are about to do:

1. Run the doctor command above to see exactly what is missing.
2. Ask the operator which AI tools and secrets manager they use — **do not guess**.
3. Run `python3 install.py --config <file>` (the interactive TUI cannot be driven by
   an agent; it will refuse to run without a terminal). Dry-run and confirm first.
4. Interview the operator and write `personal/profile.md` and their machine profile
   yourself, rather than leaving placeholder text for them to fill in.
5. Re-run the doctor to verify, then commit.

If the operator opens this repo and says anything like "set this up", "get me started",
or "configure AIKB", that is this flow.

---

## Normal operation — setup is complete

Your operating instructions live in `_agents/`. Load, in order:

1. `_agents/shared/core-min.md` — always
2. `_agents/v2/claude-code.overlay.md` — always
3. `_agents/shared/session-min.md` — keep available

Then follow the L2 dispatch table in `_agents/claude-code.md` to load playbooks from
`docs/playbooks/` on demand. Never bulk-load `docs/playbooks/`.

Key habits:

- **Search before working.** Use AIKB search to find prior decisions and context
  before exploring code or asking the operator to restate anything.
- **Load narrowly.** `_index.md` and `_state.yaml` first, then specific files.
  Never bulk-load domain folders.
- **Write as you go.** Update `Last Updated`, update `_index.md` on status change,
  and `_state.yaml` on incidents or pending items.
- **On "let's wrap up"** — run the closeout checklist in `docs/playbooks/closeout.md`.

---

## Always

- [MANDATE] Never write credential *values* into any AIKB file. Store a reference to
  the secrets manager instead.
- [MANDATE] Be precise. Do not invent facts, file contents, or tool results.
- Prefer targeted reads and search over bulk directory loads.

---

*This file is the agent entry point for the AIKB repo itself. Your machine-wide Claude
Code instructions are installed separately at `~/.claude/CLAUDE.md` by the installer.*
