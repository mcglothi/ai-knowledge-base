# Operator Loop

**Summary:** The quickest way to feel AIKB working in real life: a small daily loop for focus, wrap-up, approvals, and recurring shorthand requests.

---

## The 5-Minute Version

If you only adopt one advanced AIKB habit, make it this:

```bash
# 1. See current session state
python3 _tools/memory-pipeline/runtime_cli.py hud

# 2. Set the current objective
python3 _tools/memory-pipeline/runtime_cli.py focus set \
  --task "Ship docs refresh" \
  --verify "Open README and confirm new sections are visible"

# 3. If the agent needs sign-off for something meaningful
python3 _tools/memory-pipeline/approvals_cli.py add \
  --agent "Claude Code" \
  --project "AIKB" \
  --action "Publish public docs redesign" \
  --notes "Higher-visibility launch change"

# 4. Wrap up when you stop
python3 _tools/memory-pipeline/runtime_cli.py closeout \
  --phrase "lets wrap up for now"
```

That is enough to make AIKB feel active instead of static.

---

## What Each Part Gives You

### `hud`

Shows the operator-facing snapshot:
- current working tree cleanliness
- active session info
- recent approvals
- runtime-memory activity
- focus state if one is set

Use it when you want the "what state are we in?" answer fast.

### `focus set`

Keeps the current objective visible for longer sessions.

Good examples:
- `"Ship onboarding docs"`
- `"Debug deploy failure"`
- `"Review queued approvals"`

Good verification steps:
- `"Run tests and confirm green"`
- `"Open the live page and confirm layout"`
- `"Check git status and approval queue"`

### `approvals_cli.py`

Use approvals when the agent is about to do something with:
- architectural consequences
- preference ambiguity
- money or spending impact
- security implications
- public-facing changes you want to sanity-check first

This creates a visible trust layer instead of hiding those decisions inside chat history.

### `closeout`

Captures how a session ended:
- repo cleanliness
- branch context
- active focus/task state
- queue and approval counts
- any explicit wrap-up phrase that triggered the close

This makes the next session easier to resume.

---

## Repeated Shorthand Requests

When you notice you keep saying the same short thing:

- `"wrap up for now"`
- `"wake the lab server"`
- `"restart staging"`
- `"remember this shortcut"`

capture it in [`../home-lab/runbooks/operator-intents.md`](../home-lab/runbooks/operator-intents.md).

That is how AIKB turns operator habits into reusable workflows.

---

## A Good First Week Rollout

Day 1:
- fill in `personal/profile.md`
- fill in `personal/dev-environment/README.md`
- run `hud` once

Day 2:
- start using `closeout` when you stop
- add one approval row for a real decision

Day 3:
- capture your first operator intent
- optionally enable semantic search with `bash _tools/aikb-search/setup.sh`

You do not need the full memory pipeline on day one. The goal is a small loop you will actually keep using.
