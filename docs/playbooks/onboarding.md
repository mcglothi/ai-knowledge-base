# Playbook — Agent-Driven Onboarding

**Audience:** an AI agent (Claude Code, Codex CLI, Gemini CLI, …) working inside a
freshly created AIKB repo whose setup is not finished.

**Goal:** take the operator from "cloned the template" to "AIKB is working" in one
conversation, without making them read the docs or hand-edit template files.

---

## 0. Confirm you are actually in onboarding mode

```bash
python3 _tools/memory-pipeline/doctor.py --onboarding --json
```

This is the source of truth. Work from `next_actions` — every entry carries a `fix`.
If `installer run` is `OK` and nothing else FAILs, setup is already done: stop, say so,
and switch to normal operation.

Re-run this command after every phase below. It is how you verify your own work
rather than assuming a step succeeded.

---

## 1. Explain, then ask — do not guess

Tell the operator, briefly, what you are about to do: personalize this repo for them,
wire up their AI tools, and write their profile. Then gather answers **in conversation**.

Required:

| Field | How to get it |
|---|---|
| `github_username` | `git remote get-url origin`, or `gh api user --jq .login`. Confirm it. |
| `repo_name` | From `origin`. Usually `AIKB`. |
| `local_path` | `pwd` |
| `hostname` | `hostname -s` |
| `tools` | **Ask.** Never assume — see the exact list via `--print-schema`. |
| `secrets_manager` | **Ask.** Offer the list; "Skip for now" is a fine answer. |

Optional but recommended — ask both:

- `setup_search` — builds the local index. This is how you recall memory later.
- `install_stop_hook` — captures context at session end (Claude Code only).

Never invent values for `tools` or `secrets_manager`. A wrong answer here writes the
wrong instructions into every agent file.

---

## 2. Run the installer non-interactively

The interactive TUI needs a real terminal and will refuse to run under an agent.
Use the config path instead.

```bash
python3 install.py --print-schema           # authoritative field list
```

Write the answers to a file, then **dry-run first**:

```bash
cat > /tmp/aikb-setup.json <<'JSON'
{
  "github_username": "octocat",
  "repo_name": "AIKB",
  "hostname": "my-laptop",
  "secrets_manager": "1Password",
  "tools": ["Claude Code", "Codex CLI"],
  "setup_search": true,
  "install_stop_hook": true
}
JSON

python3 install.py --config /tmp/aikb-setup.json --dry-run
```

Show the resolved config to the operator and get an explicit go-ahead. This step
writes to `~/.claude/`, `~/.gemini/`, `~/.config/opencode/` and makes a git commit —
outside this repo and not trivially reversible. Then:

```bash
python3 install.py --config /tmp/aikb-setup.json
```

Invalid input fails loudly with an actionable message. If you get one, fix the JSON
and re-run — do not work around it by editing template files by hand.

---

## 3. Interview for the profile — the part that matters most

`personal/profile.md` and `personal/dev-environment/<hostname>.md` are what make AIKB
feel like it knows the operator. The installer only scaffolds them with placeholder
text. **Filling them in is your job, not a homework assignment for the operator.**

Ask roughly five questions, conversationally, and adapt to the answers:

1. What do you do, and what do you mainly work on? *(→ Background)*
2. Which languages, frameworks, and infrastructure do you use regularly? *(→ Skills)*
3. What are you working on right now? *(→ Current Focus)*
4. How do you want me to communicate — terse or detailed, ask before big changes? *(→ Communication Preferences)*
5. Anything I should know that keeps coming up? Tooling preferences, strong opinions? *(→ Notes for Agents)*

Then write `personal/profile.md` yourself, following the section structure in
`example/personal/profile.md`. Remove the example callout and every `[bracketed]`
placeholder — leftover placeholder text is treated as "not filled in" by doctor.

For the machine profile, gather what you can without asking (`uname -sm`, `hostname -s`,
shell, package manager, code root) and only ask about role and anything ambiguous.
Use `_templates/machine-profile.md` as the shape.

Keep `**Last Updated:**` current in both files.

---

## 4. First project (optional, but the payoff moment)

If the operator has a project in mind, create it now — it turns AIKB from empty
scaffolding into something useful in the same session:

```bash
cp _templates/file-template.md projects/<name>.md
```

Fill it from conversation, then add a row to the `## 🏗️ Projects` table in `_index.md`
with searchable tags. The `_index.md` row is what makes it findable later.

---

## 5. Verify, then hand off

```bash
python3 _tools/memory-pipeline/doctor.py --onboarding
```

Resolve anything still FAILing. WARNs are acceptable if the operator declined that
step — say which ones you left and why.

Commit and report:

```bash
git add -A && git commit -m "chore: complete AIKB onboarding" && git push origin main
```

Close by telling the operator the three things that actually change their day:

- say **"let's wrap up"** at session end and context is captured for next time
- ask **"what was I working on?"** at session start
- say **"remember that we decided X because Y"** to persist a decision

---

## Guardrails

- [MANDATE] Never write a real credential into any AIKB file. Store the *reference*.
- Confirm before the installer runs — it writes outside this repo.
- Do not hand-edit `_agents/*.md` to fix personalization. Re-run the installer or
  `./sync.sh`, so `.aikb-config.d/` stays the single source of truth.
- If the operator is unsure about a tool or secrets manager, `"Skip for now"` and
  re-running later is always safe.
