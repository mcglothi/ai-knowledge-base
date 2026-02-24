# Getting Started with AIKB

This guide walks through setting up AIKB from scratch, filling in your first files, and getting an AI agent to use it effectively.

---

## Overview of the workflow

```
1. Create a private AIKB repo (from this template)
2. Run install.sh to personalize
3. Configure one AI tool
4. Fill in your profile and machine info
5. Add projects as you work on them
```

The last step is the most important: AIKB grows as you use it. You don't need to fill everything in on day one.

---

## Step 1: Create your private repo

**Option A: GitHub template (recommended)**

1. Click **Use this template** at the top of the repo
2. Name it `AIKB`
3. Set visibility to **Private** — this repo will contain system details and project notes
4. Click **Create repository**
5. Clone it:
   ```bash
   git clone https://github.com/YOUR_USERNAME/AIKB.git ~/Code/AIKB
   cd ~/Code/AIKB
   ```

**Option B: GitHub CLI**
```bash
gh repo create AIKB --template mcglothi/aikb --private --clone
cd AIKB
```

---

## Step 2: Run the setup script

```bash
chmod +x install.sh
./install.sh
```

The script will:
- Ask for your GitHub username, repo name, and local path
- Substitute those values into the agent instruction files
- Optionally copy instructions to `~/.claude/CLAUDE.md` or `~/.gemini/GEMINI.md`

This is the only time you need to run the script. After this, agent files are plain Markdown — edit them directly.

---

## Step 3: Configure your primary AI tool

### Claude Code (recommended for technical users)

The script handles this if you accepted the prompt. To do it manually:
```bash
cp ~/Code/AIKB/_agents/claude-code.md ~/.claude/CLAUDE.md
```

Optional — set up the GitHub MCP server for remote access (skip for now if you'll always have a local clone):
```
See docs/mcp-setup.md
```

### Gemini CLI

```bash
cp ~/Code/AIKB/_agents/gemini-cli.md ~/.gemini/GEMINI.md
```

### Cursor

Cursor Settings → Cursor Settings → Rules → User Rules → paste the content of `_agents/cursor.md`.

### ChatGPT / Gemini (web) / Grok

Open the tool's settings and paste the relevant agent file into Custom Instructions.
Note: These tools require you to paste `_index.md` at the start of sessions for best results.

---

## Step 4: Fill in your profile

Start with two files:

### `personal/profile.md`
Copy `example/personal/profile.md` and fill in:
- Your name and background
- Skills (the things agents should assume you know)
- Areas you're working in
- Preferred tools and stack

### `personal/dev-environment/README.md`
Copy `_templates/domain-readme.md` and `_templates/machine-profile.md`. For each machine you use:
- Hostname and OS
- Code root path and AIKB path
- Package manager
- Installed tools (be specific — agents will use this list)

Once these files exist, agents can orient without asking "what machine are you on?" or "what's your stack?"

---

## Step 5: Add your first project

When you start a new project or start using AIKB on an existing one:

1. Create a file for it:
   ```bash
   cp ~/Code/AIKB/_templates/file-template.md ~/Code/AIKB/projects/my-project.md
   ```

2. Fill in the template — at minimum:
   - Summary (1–2 sentences)
   - Current state (what exists, what's pending)
   - Key details (URLs, paths, commands)
   - Gotchas you've already hit

3. Add a row to `_index.md`:
   ```markdown
   | My Project | 🟢 Active | my-project, python, api | [`projects/my-project.md`](projects/my-project.md) |
   ```

4. Commit and push:
   ```bash
   git add . && git commit -m "Add my-project to AIKB" && git push
   ```

Now agents know the project exists and can load the file when relevant.

---

## Step 6: Let agents maintain it

After the initial setup, agents take over most of the maintenance. At the end of sessions where something significant happened, an agent configured with AIKB will:

- Update the relevant project file
- Add discovered gotchas
- Mark completed tasks
- Update `_state.yaml` if anything time-sensitive changed
- Commit and push

You can also ask explicitly: "Update AIKB with what we learned today."

---

## Growing your AIKB over time

### Adding a new domain

When you have a coherent set of related projects (e.g. home lab, a client, a side project), give them a folder:

```bash
mkdir -p ~/Code/AIKB/home-lab
cp ~/Code/AIKB/_templates/domain-readme.md ~/Code/AIKB/home-lab/README.md
```

Common domains:
| Folder | Contents |
|--------|---------|
| `personal/` | Profile, skills, dev environments (already created) |
| `projects/` | Personal coding projects |
| `work/` | Professional context |
| `home-lab/` | Self-hosted services, networking, servers |
| `clients/` | Freelance / consulting work |

After adding a domain, update `_index.md` and re-sync your agent instruction files.

### Keeping files from growing stale

- The `Last Updated` field is the primary staleness signal. Agents update it when they touch a file.
- If a project ends, mark it `✅ Complete` at the top — don't delete it. Historical context has value.
- Run `git log --since="30 days ago" --name-only --pretty=""` periodically to see which files haven't been touched.

---

## Troubleshooting

**Agent doesn't seem to know about my project**
→ Check `_index.md` — does the project have a row with useful tags? Tags are how agents decide which files to load.

**Agent asks questions I've already answered in AIKB**
→ Check `personal/profile.md` and `personal/dev-environment/README.md` — are they filled in? Agents load these early in sessions.

**Changes not persisting across sessions**
→ Check that the agent's commit went through: `git -C ~/Code/AIKB log --oneline -5`. If commits aren't appearing, the agent may not have write access or the MCP server may not be configured.

**Two agents wrote conflicting updates**
→ Check `_agents/active.md` — it's designed to prevent this. If conflicts occur, resolve them manually: `git -C ~/Code/AIKB pull` then resolve any merge conflicts.
