# New Machine Onboarding
**Last Updated:** 2026-04-16

**Summary:** Fast path for bringing an existing private AIKB onto a new host without rerunning the full first-time installer.

---

## When to use this

Use this workflow when:

- you already have a private `AIKB` repo
- you are setting up a second machine or a replacement machine
- you want repo-managed agent configs, stop hooks, and local AIKB helpers on the new host

Use the full install only when you are creating your private AIKB for the first time.

---

## Fast path

1. Clone your private repo to the standard location:

```bash
mkdir -p ~/code
git clone git@github.com:YOUR_USERNAME/AIKB.git ~/code/AIKB
cd ~/code/AIKB
```

2. Run the onboarding script:

```bash
bash _tools/new-machine-onboarding.sh
```

3. Restart your shell and then authenticate the tools you want to use on that host:

```bash
gh auth login
gemini auth login
codex login
```

If you do not want OpenCode or `aikb-search` configured yet:

```bash
bash _tools/new-machine-onboarding.sh --skip-opencode --skip-search
```

---

## What it does

The script is idempotent and safe to rerun. It will:

- pull the latest `origin/main` for the local AIKB clone
- write fresh local `.aikb-config.d/` values for the current host
- sync repo-managed agent instruction files:
  - `~/.claude/CLAUDE.md`
  - `~/.gemini/GEMINI.md`
  - `~/.codex/AGENTS.md`
- install safe repo-managed settings for:
  - `~/.claude/settings.json`
  - `~/.claude/statusline-command.sh`
  - `~/.gemini/settings.json`
  - `~/.codex/config.toml`
  - `~/.codex/agents/*`
  - `~/.config/opencode/opencode.json`
- wire Codex session closeout into `~/.zshrc`
- install AIKB zsh hooks via `_tools/memory-pipeline/install_zsh_hooks.sh`
- run `_tools/aikb-search/setup.sh` unless you skip it
- back up any overwritten config files under `~/.aikb-backups/`

---

## What it does not copy

This workflow deliberately avoids machine-secret and machine-state files.

It does not copy:

- `~/.claude/settings.local.json`
- OAuth tokens, auth databases, session files, or CLI history
- SSH keys
- `~/.aws`
- Bitwarden session state

That means you still need to authenticate tools and restore secrets on each new host.

---

## Notes

- The generated Gemini and OpenCode GitHub MCP config expects `GITHUB_TOKEN` to be available in the environment when those tools start.
- `aikb-search` remains local to each machine. The onboarding script builds the local venv and index for the new host.
- If you use a nonstandard code root, pass `--code-root /your/path`.

---

## Postflight

After the script finishes:

1. Restart the shell.
2. Run your first AIKB session startup command.
3. Add a machine note under `personal/dev-environment/`.
4. Commit and push any intentional documentation updates from the new machine.
