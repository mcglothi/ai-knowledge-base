# Operator Loop

**Summary:** The quickest way to feel AIKB working in real life: a small daily loop for focus, wrap-up, approvals, and recurring shorthand requests.

---

## Session Start: wake-up

Run one command at the start of every session:

    python3 _tools/memory-pipeline/runtime_cli.py wake-up

Output: SSL expiry warnings, pending blockers, in-progress items, recent events.
This replaces reading `_index.md` and `_state.yaml` manually.

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

## Capture quality

Good capture makes the compact-and-recall loop work. A one-line capture preserves the decision but loses the *shape* of reasoning around unfinished work.

The four-field capture model adds high-fidelity context:

- **Rejected:** what was tried or considered and ruled out, and why. Prevents future agents from re-litigating solved questions.
- **Assumptions:** things true right now that won't be obvious from the code later.
- **Invariants:** temporary states: things intentionally broken or incomplete until X happens.
- **Next Step:** the single most important action when this work resumes.

### Example: Weak vs. Rich Capture

**Weak capture (preserves the decision, loses the context):**
```bash
python3 _tools/memory-pipeline/runtime_cli.py capture \
  --type decision --summary "switched to PostgreSQL"
```

**Rich capture (a future agent can actually resume from this):**
```bash
python3 _tools/memory-pipeline/runtime_cli.py capture \
  --type decision \
  --summary "switched from SQLite to PostgreSQL for multi-user support" \
  --rejected "SQLite WAL mode doesn't handle concurrent writes from multiple agents; tested and confirmed deadlocks under load" \
  --assumptions "DB schema is read-only until migration 004 runs — do not write to users table yet" \
  --invariants "user.role column exists but is always NULL until seeder is written" \
  --next-step "write migration 004, then update UserService.getRole() to read from DB instead of hardcoded default"
```

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
