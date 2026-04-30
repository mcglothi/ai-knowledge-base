# New Agent Tiered Onboarding Playbook (v2)

## Purpose
Standardize onboarding for any new agent runtime (e.g., Hermes, Goose) into AIKB's layered instruction model:
- L0: shared core mandates
- L1: agent/runtime overlay
- L2: on-demand playbooks via dispatch

## When to Load
- Adding a new agent file under `_agents/`
- Migrating a monolithic instruction file to v2
- Creating local runtime instruction targets (e.g., `~/.<agent>/<file>.md`)

## Required Outputs
1. New overlay file: `_agents/v2/<agent>.overlay.md`
2. New candidate dispatcher: `_agents/<agent>-v2-candidate.md`
3. Runtime backup + swap plan
4. Trial run evidence (IM/token/dispatch/closeout)
5. Pilot checklist run entries

## Step-by-Step

### 1) Baseline + Backup
- Backup current monolithic file and runtime target.
- Record backup path in `_runtime/backups/...`.

### 2) Create L1 Overlay
Use `_agents/v2/_overlay-template.md` and fill:
- agent label
- AIKB root macro `${AIKB_ROOT}`
- runtime CLI command path
- compact keyword (`/compact` or `/compress`)
- credential safety + fallback
- IM conventions and fuzzy trigger preservation
- startup health checks
- expected core version

### 3) Create Candidate Dispatcher File
Create `_agents/<agent>-v2-candidate.md` with:
- startup load order (core -> overlay -> session-min)
- startup health check
- L2 dispatch table to standard playbooks
- agent-specific runtime rules
- compact triggers + closeout phrases
- validation command (`run_v2_trial.sh <agent>`) 

### 4) Map Runtime Target
Identify target file for agent runtime, e.g.:
- Claude: `~/.claude/CLAUDE.md`
- Codex: `~/.codex/AGENTS.md`
- Gemini: `~/.gemini/GEMINI.md`
- New agents: define in overlay and onboarding notes.

### 5) Smoke Test (minimum)
Run in fresh session:
1. IM trigger
2. token-economy check
3. dispatch check (git or cross-agent)
4. wrap-up trigger

### 6) Score + Log
- Append run entry to pilot checklist.
- Require 3 successful B-runs for production promotion.

## Promotion Gate (per new agent)
- 3/3 PASS B-runs
- no critical safety regressions
- readiness checks pass
- changelog updated with migration notes

## Guardrails
- Do not delete original monolith until gate passes.
- Always backup runtime target before swap.
- Preserve exact security rules (BW_SESSION and no-secrets mandates).
- Keep L0/L1 line budgets intact; push detail into L2.
