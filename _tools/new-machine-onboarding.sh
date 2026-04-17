#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AIKB_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CODE_ROOT="$(cd "$AIKB_ROOT/.." && pwd)"
HOSTNAME_SHORT="$(hostname -s 2>/dev/null || hostname)"
HOSTNAME_CANONICAL="$(printf '%s' "$HOSTNAME_SHORT" | tr '[:upper:]' '[:lower:]')"
RUN_SEARCH=1
RUN_OPENCODE=1
RUN_PULL=1
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_ROOT="$HOME/.aikb-backups/new-machine-onboarding-$TIMESTAMP"

info() {
  printf '[aikb] %s\n' "$*"
}

warn() {
  printf '[aikb] WARNING: %s\n' "$*" >&2
}

usage() {
  cat <<'EOF'
Usage: bash _tools/new-machine-onboarding.sh [options]

Run this from an existing private AIKB clone on a new machine.

Options:
  --code-root PATH     Override the code root written into local configs.
                       Default: parent directory of the current AIKB clone.
  --skip-search        Skip aikb-search setup.
  --skip-opencode      Skip OpenCode config sync.
  --skip-pull          Skip `git pull --ff-only origin main` before syncing.
  -h, --help           Show this help text.

This workflow intentionally syncs only repo-managed instructions and safe
settings. It does not copy auth/session state, SSH keys, cloud credentials,
or tool-local history databases.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --code-root)
      CODE_ROOT="${2:?missing value for --code-root}"
      shift 2
      ;;
    --skip-search)
      RUN_SEARCH=0
      shift
      ;;
    --skip-opencode)
      RUN_OPENCODE=0
      shift
      ;;
    --skip-pull)
      RUN_PULL=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      warn "unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ ! -d "$AIKB_ROOT/.git" ]]; then
  warn "this script must run from inside an AIKB clone"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  warn "python3 is required"
  exit 1
fi

if [[ "$RUN_PULL" -eq 1 ]]; then
  info "pulling latest AIKB"
  git -C "$AIKB_ROOT" pull --ff-only origin main
fi

backup_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    local backup="$BACKUP_ROOT${path#$HOME}"
    mkdir -p "$(dirname "$backup")"
    cp "$path" "$backup"
  fi
}

ensure_line() {
  local file="$1"
  local line="$2"
  touch "$file"
  if ! grep -Fqx "$line" "$file"; then
    backup_file "$file"
    {
      printf '\n'
      printf '%s\n' "$line"
    } >> "$file"
  fi
}

write_file() {
  local path="$1"
  mkdir -p "$(dirname "$path")"
  backup_file "$path"
  cat > "$path"
}

normalize_remote() {
  local raw="$1"
  raw="${raw#git@github.com:}"
  raw="${raw#https://github.com/}"
  raw="${raw%.git}"
  printf '%s\n' "$raw"
}

ORIGIN_URL="$(git -C "$AIKB_ROOT" remote get-url origin)"
REMOTE_PATH="$(normalize_remote "$ORIGIN_URL")"
GITHUB_USERNAME="${REMOTE_PATH%%/*}"
REPO_NAME="${REMOTE_PATH##*/}"

if [[ -z "$GITHUB_USERNAME" || -z "$REPO_NAME" || "$GITHUB_USERNAME" == "$REMOTE_PATH" ]]; then
  warn "could not derive GitHub owner/repo from origin: $ORIGIN_URL"
  exit 1
fi

REPO_URL="https://github.com/$GITHUB_USERNAME/$REPO_NAME"
REPO_SSH="git@github.com:$GITHUB_USERNAME/$REPO_NAME.git"
OS_FRIENDLY="$(uname -s)"
case "$OS_FRIENDLY" in
  Darwin) OS_FRIENDLY="macOS" ;;
  Linux) OS_FRIENDLY="Linux" ;;
esac

info "writing local AIKB config metadata"
mkdir -p "$AIKB_ROOT/.aikb-config.d"
printf '%s' "$GITHUB_USERNAME" > "$AIKB_ROOT/.aikb-config.d/GITHUB_USERNAME"
printf '%s' "$REPO_NAME" > "$AIKB_ROOT/.aikb-config.d/REPO_NAME"
printf '%s' "$REPO_URL" > "$AIKB_ROOT/.aikb-config.d/REPO_URL"
printf '%s' "$REPO_SSH" > "$AIKB_ROOT/.aikb-config.d/REPO_SSH"
printf '%s' "$AIKB_ROOT" > "$AIKB_ROOT/.aikb-config.d/LOCAL_PATH"
printf '%s/' "$CODE_ROOT" > "$AIKB_ROOT/.aikb-config.d/CODE_ROOT"
printf '%s' "$HOSTNAME_CANONICAL" > "$AIKB_ROOT/.aikb-config.d/PRIMARY_HOSTNAME"
printf '%s' "$OS_FRIENDLY" > "$AIKB_ROOT/.aikb-config.d/OS"
printf '%s' 'Bitwarden/Vaultwarden' > "$AIKB_ROOT/.aikb-config.d/SECRETS_MANAGER"
printf '%s' 'bw get password' > "$AIKB_ROOT/.aikb-config.d/SECRETS_RETRIEVE"
printf '%s' 'y' > "$AIKB_ROOT/.aikb-config.d/SETUP_CLAUDE"
printf '%s' 'y' > "$AIKB_ROOT/.aikb-config.d/SETUP_GEMINI"
printf '%s' "$([[ "$RUN_OPENCODE" -eq 1 ]] && printf 'y' || printf 'n')" > "$AIKB_ROOT/.aikb-config.d/SETUP_OPENCODE"

info "syncing Claude Code files"
mkdir -p "$HOME/.claude"
backup_file "$HOME/.claude/CLAUDE.md"
cp "$AIKB_ROOT/_agents/claude-code.md" "$HOME/.claude/CLAUDE.md"
write_file "$HOME/.claude/settings.json" <<EOF
{
  "statusLine": {
    "type": "command",
    "command": "bash $HOME/.claude/statusline-command.sh"
  },
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash $AIKB_ROOT/_tools/memory-pipeline/aikb-session-stop.sh"
          }
        ]
      }
    ]
  }
}
EOF
write_file "$HOME/.claude/statusline-command.sh" <<'EOF'
#!/usr/bin/env bash
# Claude Code statusLine command
# Mirrors the prompt with directory, git branch, model, and context usage.

input=$(cat)

cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')
model=$(echo "$input" | jq -r '.model.display_name // ""')
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

short_dir="${cwd/#$HOME/~}"

git_branch=""
if git -C "$cwd" rev-parse --git-dir >/dev/null 2>&1; then
  git_branch=$(git -C "$cwd" -c gc.auto=0 symbolic-ref --short HEAD 2>/dev/null \
               || git -C "$cwd" -c gc.auto=0 rev-parse --short HEAD 2>/dev/null)
fi

parts=()
parts+=("$(printf '\033[34m%s\033[0m' "$short_dir")")

if [[ -n "$git_branch" ]]; then
  parts+=("$(printf '\033[36m(%s)\033[0m' "$git_branch")")
fi

if [[ -n "$model" ]]; then
  parts+=("$(printf '\033[35m%s\033[0m' "$model")")
fi

if [[ -n "$used_pct" ]]; then
  used_int=$(printf '%.0f' "$used_pct")
  parts+=("$(printf '\033[33mctx:%s%%\033[0m' "$used_int")")
fi

printf '%s' "$(IFS=' | '; echo "${parts[*]}")"
EOF
chmod +x "$HOME/.claude/statusline-command.sh"

info "syncing Gemini CLI files"
mkdir -p "$HOME/.gemini"
backup_file "$HOME/.gemini/GEMINI.md"
cp "$AIKB_ROOT/_agents/gemini-cli.md" "$HOME/.gemini/GEMINI.md"
write_file "$HOME/.gemini/settings.json" <<EOF
{
  "general": {
    "previewFeatures": true,
    "vimMode": true,
    "sessionRetention": {
      "enabled": true,
      "maxAge": "30d",
      "warningAcknowledged": true
    },
    "preferredEditor": "vim"
  },
  "hooks": {
    "SessionEnd": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash $AIKB_ROOT/_tools/memory-pipeline/aikb-session-stop.sh"
          }
        ]
      }
    ]
  },
  "mcpServers": {
    "github-aikb": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_TOKEN": "\$GITHUB_TOKEN"
      }
    },
    "chrome-devtools": {
      "command": "npx",
      "args": [
        "-y",
        "chrome-devtools-mcp@latest"
      ],
      "trust": true
    },
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--extension"
      ],
      "env": {
        "PLAYWRIGHT_MCP_EXTENSION_TOKEN": "\$PLAYWRIGHT_MCP_EXTENSION_TOKEN"
      },
      "trust": true
    },
    "fetch": {
      "command": "uvx",
      "args": [
        "mcp-server-fetch"
      ],
      "trust": true
    },
    "multicli": {
      "command": "npx",
      "args": [
        "-y",
        "@osanoai/multicli"
      ]
    },
    "aikb-search": {
      "command": "$AIKB_ROOT/_tools/aikb-search/.venv/bin/python",
      "args": [
        "$AIKB_ROOT/_tools/aikb-search/server.py"
      ]
    }
  }
}
EOF

info "syncing Codex files"
mkdir -p "$HOME/.codex/agents"
backup_file "$HOME/.codex/AGENTS.md"
cp "$AIKB_ROOT/_agents/codex.md" "$HOME/.codex/AGENTS.md"
write_file "$HOME/.codex/config.toml" <<EOF
personality = "friendly"
network_access = true
sandbox_mode = "danger-full-access"
approval_policy = "on-request"
model = "gpt-5.4"
model_reasoning_effort = "medium"
service_tier = "fast"
approvals_reviewer = "user"

[projects."$CODE_ROOT"]
trust_level = "trusted"

[projects."$AIKB_ROOT"]
trust_level = "trusted"

[projects."$HOME"]
trust_level = "trusted"

[mcp_servers.github-aikb]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]

[mcp_servers.github-aikb.tools.create_repository]
approval_mode = "approve"

[mcp_servers.crash]
command = "npx"
args = ["-y", "crash-mcp"]

[mcp_servers.chrome-devtools]
command = "npx"
args = ["-y", "chrome-devtools-mcp@latest"]

[mcp_servers.chrome-devtools.tools.fill]
approval_mode = "approve"

[mcp_servers.chrome-devtools.tools.navigate_page]
approval_mode = "approve"

[mcp_servers.chrome-devtools.tools.take_screenshot]
approval_mode = "approve"

[mcp_servers.chrome-devtools.tools.click]
approval_mode = "approve"

[mcp_servers.chrome-devtools.tools.evaluate_script]
approval_mode = "approve"

[mcp_servers.playwright]
command = "npx"
args = ["@playwright/mcp@latest"]

[mcp_servers.playwright.tools.browser_navigate]
approval_mode = "approve"

[mcp_servers.playwright.tools.browser_click]
approval_mode = "approve"

[mcp_servers.playwright.tools.browser_evaluate]
approval_mode = "approve"

[mcp_servers.playwright.tools.browser_fill_form]
approval_mode = "approve"

[mcp_servers.playwright.tools.browser_resize]
approval_mode = "approve"

[mcp_servers.filesystem]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "$CODE_ROOT"]

[mcp_servers.filesystem.tools.create_directory]
approval_mode = "approve"

[mcp_servers.sequential-thinking]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-sequential-thinking"]

[mcp_servers.multicli]
command = "npx"
args = ["-y", "@osanoai/multicli"]

[features]
multi_agent = true

[agents]
max_threads = 6
max_depth = 2

[profiles.orchestrator]
model = "gpt-5-codex"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
model_instructions_file = "$HOME/.codex/agents/orchestrator.md"

[profiles.research]
model = "gpt-5-codex"
model_reasoning_effort = "medium"
sandbox_mode = "read-only"
approval_policy = "never"

[profiles.ship]
model = "gpt-5-codex"
model_reasoning_effort = "low"
sandbox_mode = "workspace-write"
approval_policy = "on-request"

[plugins."github@openai-curated"]
enabled = true

[agents.orchestrator]
description = "Used to orchestrate multi-agent workflows"
config_file = "$HOME/.codex/agents/orchestrator.toml"

[agents.reviewer]
description = "Used to review code changes and provide feedback"
config_file = "$HOME/.codex/agents/reviewer.toml"

[agents.researcher]
description = "Use for deep research, codebase exploration, exploratory tasks, and other read-only work."
config_file = "$HOME/.codex/agents/researcher.toml"

[agents.worker]
description = "Used to implement changes to the codebase"
config_file = "$HOME/.codex/agents/worker.toml"
EOF
write_file "$HOME/.codex/agents/orchestrator.md" <<'EOF'
# Codex Orchestrator

You are Codex Orchestrator, based on GPT-5. You are running as an orchestration agent in the Codex CLI on a user's computer.

## Role

* You are the interface between the user and the researchers, workers and reviewers.
* Your job is to understand the task via researcher agents, decompose it, and delegate well-scoped work to workers.
* You plan and coordinate execution, monitor progress, resolve conflicts, and integrate results into a single coherent outcome.
* You may perform lightweight actions (e.g. reading files, basic commands) to understand the task, but all substantive work and research/exploration must be delegated to researchers and workers.
* You may not modify any code. All coding should be done by workers.
* **Your job is not finished until the entire task is fully completed and verified.**
* While the task is incomplete, you must keep monitoring and coordinating workers. You must not return early.

## Core invariants

* **Never stop monitoring workers.**
* **Do not rush workers. Be patient.**
* The orchestrator must not return unless the task is fully accomplished.
* If the user asks a question/status while you are working, always answer before continuing your work.

## Worker execution semantics

* While a worker is running, you cannot observe intermediate state.
* Workers can run commands, update/create/delete files, and are fully autonomous for their scope.
* Messages sent with `send_input` are queued and processed only after the worker finishes, unless interrupted.
* Therefore:
    * Do not send messages to "check status" or "ask for progress" unless asked.
    * Monitoring happens via `wait`.
    * Sending a message is a commitment for the *next* phase of work.
* Workers can surface approvals directly to the user; if denied, the agent may appear as interrupted. You can continue it with `send_input`.

## Interrupt semantics

* If a worker or researcher is taking longer than expected but still working, do nothing and keep waiting unless asked.
* Only intervene if you must change, stop, or redirect the *current* work.
* To stop current work, use `send_input(interrupt=true)`.
* Use `interrupt=true` sparingly.

## Multi-agent workflow

1. Check current git status and preserve existing unrelated modifications unless they conflict with the objective.
2. Understand the request by spawning researcher agents as needed.
3. Create a plan and determine the optimal set of agents.
4. Execute the plan by spawning worker(s) with precise goals, constraints, expected deliverables, and acceptance criteria.
5. Monitor workers using `wait`.
6. When a worker finishes:
    * verify correctness,
    * check integration with other work,
    * check alignment with gathered research,
    * assess whether the global task is closer to completion.
7. If issues remain, assign fixes and repeat.
8. When all workers are finished:
    1. Spawn reviewer agent to review current changes.
    2. Delegate review findings to the appropriate worker.
    3. Repeat review until no further findings.
9. Close agents only when no further work is required.
10. Return only when the task is fully completed and verified.

## Collaboration rules

* Workers operate in a shared environment; remind them of this.
* You and spawned agents must not revert, hard reset, checkout, delete, overwrite, or conflict with others' work.
* By default, workers must not spawn sub-agents unless explicitly allowed.
* When multiple workers are active, pass multiple IDs to `wait` and use long timeouts.

## Final response

* Keep responses concise, factual, and plain text.
* Summarize:
    * decisions made,
    * what was delegated,
    * key outcomes,
    * review findings and resolutions,
    * verification performed,
    * remaining risks.
* Include agents spawned and jobs completed.
* If verification failed, state issues and what was reassigned.
* Do not dump large files inline; reference paths with `backticks`.
EOF
write_file "$HOME/.codex/agents/orchestrator.toml" <<EOF
model = "gpt-5-codex"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
model_instructions_file = "$HOME/.codex/agents/orchestrator.md"
EOF
write_file "$HOME/.codex/agents/researcher.md" <<'EOF'
# Codex Researcher

You are Codex Researcher, based on GPT-5. You are running as a research agent in the Codex CLI on a user's computer.

## Role

* Research best practices, reference implementations, and robust solutions.
* You are not a code-writing agent; your deliverable is guidance.
* Prioritize authoritative sources (official docs, specs, upstream repos, high-signal maintainers) and local repo patterns.
* Match recommendations to repo maturity and constraints.

## Core invariants

* **Evidence over opinion.**
* **Repository-first.**
* **Scope discipline.**
* **No magic.**
* **Security realism.**

## Research workflow

1. Understand the core question.
2. Analyze relevant factors/components.
3. Explore repository patterns and constraints.
4. Gather authoritative external references.
5. Synthesize options and tradeoffs.
6. Conclude with explicit recommendation.

## Deliverables

Provide:

* **Summary**: key insights.
* **Explanation**: deeper reasoning.
* **Repository notes**: relevant files/modules.
* **Options**: tradeoffs and when to choose each.
* **Recommendation**: explicit choice + rationale.
* **Verification**: tests/checks and failure cases.
* **Citations**: 1-5 best links.

## What to avoid

* Major rewrites unless clearly justified.
* Disabling checks as a workaround in production.
* Unmaintained dependencies.
* Hand-wavy answers without repo/source grounding.
EOF
write_file "$HOME/.codex/agents/researcher.toml" <<EOF
model = "gpt-5-codex"
model_reasoning_effort = "medium"
sandbox_mode = "read-only"
approval_policy = "never"
model_instructions_file = "$HOME/.codex/agents/researcher.md"
EOF
write_file "$HOME/.codex/agents/reviewer.md" <<'EOF'
# Codex Reviewer

You are Codex Reviewer, acting as a reviewer for proposed changes.

## Review focus

Prioritize concrete, actionable issues affecting:

1. Correctness
2. Security/privacy
3. Reliability/operability
4. Performance
5. Maintainability

## Review behavior

* Flag issues that are likely unintentional regressions.
* Keep findings concise and specific.
* Prefer one finding per distinct issue.
* Include severity and confidence.
* If no substantive issues are found, state that clearly.

## Output expectations

* Findings first, ordered by severity.
* Brief open questions/assumptions next.
* Short overall correctness verdict last.
EOF
write_file "$HOME/.codex/agents/reviewer.toml" <<EOF
model = "gpt-5-codex"
model_reasoning_effort = "high"
sandbox_mode = "read-only"
approval_policy = "never"
model_instructions_file = "$HOME/.codex/agents/reviewer.md"
EOF
write_file "$HOME/.codex/agents/worker.md" <<'EOF'
You are Codex, based on GPT-5. You are running as a coding agent in the Codex CLI on a user's computer.

## General

- Prefer `rg` / `rg --files` for fast search.

## Editing constraints

- Default to ASCII unless the file already uses Unicode for a clear reason.
- Add concise comments only when they improve comprehension.
- Avoid reverting unrelated local changes.
- Never use destructive git commands unless explicitly requested.
- Use `apply_patch` for focused single-file edits when practical.

## Execution style

- Default to autonomous `read -> edit -> validate` loops.
- Run targeted tests/checks after edits when practical.
- Stop and ask if unexpected changes appear that may conflict with task scope.

## Final responses

- Be concise and action-oriented.
- Report what changed, what was run, and any remaining risks.
EOF
write_file "$HOME/.codex/agents/worker.toml" <<EOF
model = "gpt-5-codex"
model_reasoning_effort = "low"
sandbox_mode = "workspace-write"
approval_policy = "on-request"
model_instructions_file = "$HOME/.codex/agents/worker.md"
EOF

if [[ "$RUN_OPENCODE" -eq 1 ]]; then
  info "syncing OpenCode config"
  write_file "$HOME/.config/opencode/opencode.json" <<EOF
{
  "\$schema": "https://opencode.ai/config.json",
  "instructions": [
    "$AIKB_ROOT/_agents/opencode.md"
  ],
  "model": "hopper/gemma4:26b",
  "small_model": "hopper/nemotron-mini:4b",
  "provider": {
    "hopper": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Hopper Ollama",
      "options": {
        "baseURL": "http://10.10.10.200:11434/v1"
      },
      "models": {
        "nemotron-mini:4b": {
          "name": "Hopper Fast - Nemotron Mini 4B"
        },
        "gpt-oss:20b": {
          "name": "Hopper Reasoning - GPT OSS 20B"
        },
        "gemma4:31b": {
          "name": "Hopper General - Gemma 4 31B Dense"
        },
        "gemma4:26b": {
          "name": "Hopper General - Gemma 4 26B MoE"
        },
        "qwen3-coder:30b": {
          "name": "Hopper Code - Qwen3 Coder 30B"
        },
        "gpt-oss:120b": {
          "name": "Hopper Heavy - GPT OSS 120B"
        }
      }
    }
  },
  "mcp": {
    "github-aikb": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
      "enabled": true,
      "environment": {
        "GITHUB_TOKEN": "\$GITHUB_TOKEN"
      }
    },
    "crash": {
      "type": "local",
      "command": ["npx", "-y", "crash-mcp"],
      "enabled": true
    },
    "chrome-devtools": {
      "type": "local",
      "command": ["npx", "-y", "chrome-devtools-mcp@latest"],
      "enabled": true
    },
    "playwright": {
      "type": "local",
      "command": ["npx", "-y", "@playwright/mcp@latest"],
      "enabled": true
    },
    "filesystem": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "$CODE_ROOT"],
      "enabled": true
    },
    "sequential-thinking": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-sequential-thinking"],
      "enabled": true
    },
    "multicli": {
      "type": "local",
      "command": ["npx", "-y", "@osanoai/multicli"],
      "enabled": true
    },
    "aikb-search": {
      "type": "local",
      "command": [
        "$AIKB_ROOT/_tools/aikb-search/.venv/bin/python",
        "$AIKB_ROOT/_tools/aikb-search/server.py"
      ],
      "enabled": true
    }
  }
}
EOF
fi

info "installing Codex wrapper and shell hooks"
ensure_line "$HOME/.zshrc" "source \"$AIKB_ROOT/_tools/memory-pipeline/codex-wrapper.sh\""
if [[ -x "$AIKB_ROOT/_tools/memory-pipeline/install_zsh_hooks.sh" ]]; then
  bash "$AIKB_ROOT/_tools/memory-pipeline/install_zsh_hooks.sh"
fi
chmod +x "$AIKB_ROOT/_tools/memory-pipeline/aikb-session-stop.sh"

if [[ "$RUN_SEARCH" -eq 1 ]]; then
  info "setting up aikb-search"
  bash "$AIKB_ROOT/_tools/aikb-search/setup.sh"
else
  info "skipping aikb-search setup"
fi

info "new machine onboarding complete"
info "backups of overwritten files were saved under: $BACKUP_ROOT"
cat <<EOF

Next steps:
  1. Authenticate tools on this host:
     - gh auth login
     - gemini auth login
     - codex login
     - bwu
  2. Copy machine-local credentials that are intentionally excluded here:
     - SSH keys
     - ~/.aws
     - tool auth/session databases
  3. Restart your shell so the Codex wrapper and AIKB hooks load.
  4. Add or update personal/dev-environment/$HOSTNAME_CANONICAL.md with this host's details.

Intentionally not copied:
  - ~/.claude/settings.local.json
  - auth.json / oauth token files / session databases
  - SSH keys and cloud credentials
EOF
