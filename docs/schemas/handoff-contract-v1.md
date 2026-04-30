# Handoff Contract v1

Use this schema for cross-agent handoffs to reduce ambiguity.

## Required Fields
- `title`: short handoff title
- `from_agent`: source agent name
- `to_agent`: target agent name (or `broadcast`)
- `repo`: repository name
- `scope`: task scope in one line
- `decision`: chosen direction + rationale
- `top_risks`: 3-5 bullet risks
- `next_actions`: ordered checklist with owners
- `artifacts`: files/paths touched or to inspect
- `rollback`: how to revert safely if needed

## Optional Fields
- `blocked_by`
- `assumptions`
- `deadline`
- `links`

## Template
```md
# <title>
from_agent: <Agent>
to_agent: <Agent|broadcast>
repo: <repo>
scope: <scope>

decision:
- <what>
- rationale: <why>

top_risks:
- [ ] <risk 1>
- [ ] <risk 2>
- [ ] <risk 3>

next_actions:
- [ ] <action> (owner: <agent/person>)
- [ ] <action> (owner: <agent/person>)

artifacts:
- <path>
- <path>

rollback:
- <revert command or procedure>
```
