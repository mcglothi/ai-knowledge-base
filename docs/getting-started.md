# Getting Started with AIKB
**Last Updated:** 2026-04-29

Setup from scratch. Already have a private AIKB and need a new machine? Use [new-machine-onboarding.md](new-machine-onboarding.md).

## Pick Your Path
| I use... | Setup |
|----------|--------|
| Claude Code or Gemini CLI | Follow this guide top to bottom |
| Cursor or OpenCode | Steps 1–3, then see Cursor/OpenCode section |
| Microsoft Copilot Studio | Steps 1–3, then [MS Copilot Studio connector setup →](mscs-connector-setup.md) (Windows/no-WSL lane supported) |
| ChatGPT, Gemini (web), or Grok | Steps 1–2 + 2-minute paste → [web tools](#web-tools) |
| Windows | [WSL guide first →](windows-wsl.md) |

## Step 1 — Create your private repo

**Option A (recommended):**
1. Click **Use this template** → name it `AIKB` → set **Private** → **Create repository**
2. `git clone https://github.com/YOUR_USERNAME/AIKB.git ~/code/AIKB`

**Option B:** `gh repo create AIKB --template mcglothi/ai-knowledge-base --private --clone`

Windows: clone inside WSL filesystem (not `/mnt/c/...`). See [windows-wsl.md](windows-wsl.md).

## Step 2 — Run setup
```bash
chmod +x install.sh && ./install.sh
```
Asks for GitHub username, repo name, local path → substitutes into agent files → optionally copies to `~/.claude/CLAUDE.md` and `~/.gemini/GEMINI.md`.
If cloned from your GitHub repo first, `install.sh` pre-fills from `origin`.

Optional walkthroughs: `bash _tools/tutorial.sh` · `bash _tools/feature-tour.sh`

## Step 3 — Configure your AI tool

**Claude Code:** `cp ~/code/AIKB/_agents/claude-code.md ~/.claude/CLAUDE.md`
Optional GitHub MCP for remote access: [docs/mcp-setup.md](mcp-setup.md)

**Gemini CLI:** `cp ~/code/AIKB/_agents/gemini-cli.md ~/.gemini/GEMINI.md`

**Codex CLI:** `cp ~/code/AIKB/_agents/codex.md /path/to/project/AGENTS.md` (per workspace)

**GitHub Copilot:** `./sync-agents.sh --agent copilot /path/to/project` (writes `.github/copilot-instructions.md`)

**Microsoft Copilot Studio (optional addon):** follow [docs/mscs-connector-setup.md](mscs-connector-setup.md) after base install.

**Cursor:** Settings → Cursor Settings → Rules → User Rules → paste `_agents/cursor.md`

**ChatGPT / Gemini (web) / Grok:** Settings → Custom Instructions → paste matching `_agents/` file.

### Web tools {#web-tools}
| Tool | Location |
|------|----------|
| ChatGPT | Settings → Customize ChatGPT → Custom Instructions |
| Gemini | Settings → Custom Instructions |
| Grok | Customize Grok → System Prompt |

Web tools can't read your repo directly — paste `_index.md` at the start of each session.

## Step 4 — Fill in your profile

**`personal/profile.md`** — copy `example/personal/profile.md`, fill in: name, background, skills, areas, preferred stack.

**`personal/dev-environment/README.md`** — copy templates, fill in per machine: hostname, OS, code root, AIKB path, package manager, installed tools.

## Step 5 — Add your first project
```bash
cp ~/code/AIKB/_templates/file-template.md ~/code/AIKB/projects/my-project.md
```
Fill in: summary, current state, key URLs/paths/commands, gotchas.
Add row to `_index.md`: `| My Project | 🟢 Active | tags | [path] |`
Commit: `git add . && git commit -m "Add my-project to AIKB" && git push`

## Step 6 — Let agents maintain it
After setup, agents handle maintenance. At session end, a configured agent will update project files, add gotchas, mark tasks, update `_state.yaml`, and commit.

| What you want | What to say |
|---|---|
| Today's goal | "My focus is X" |
| Flag for sign-off | "Ask before you do X" |
| Save a decision | "Remember that we decided Y because Z" |
| Wrap up | "Let's wrap up" |

One habit: end sessions with "Let's wrap up" — captures context for the next session.

## Growing AIKB

**New domain:**
```bash
mkdir -p ~/code/AIKB/home-lab
cp ~/code/AIKB/_templates/domain-readme.md ~/code/AIKB/home-lab/README.md
```
Common: `personal/` · `projects/` · `work/` · `home-lab/` · `clients/`
After adding: update `_index.md` and re-sync agent files.

**Staleness:** `Last Updated` is the primary signal. Mark ended projects `✅ Complete` — don't delete. Run `git log --since="30 days ago" --name-only --pretty=""` to find untouched files.

## Troubleshooting
- **Agent doesn't know about my project** → check `_index.md` has a row with useful tags
- **Agent asks things already in AIKB** → check `personal/profile.md` and dev-environment are filled in
- **Changes not persisting** → `git -C ~/code/AIKB log --oneline -5` — confirm commits appeared
- **Two agents wrote conflicts** → check `_agents/active.md` · `git -C ~/code/AIKB pull` then resolve
