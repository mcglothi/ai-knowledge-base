#!/usr/bin/env bash
# Mock AIKB installer for demo recording.
# Simulates install.py TUI output with no side effects — safe to run anywhere.

BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'
CYAN='\033[36m'; GREEN='\033[32m'; BLUE='\033[34m'

sleep 0.3

# ── Welcome ───────────────────────────────────────────────────────────────────
printf "${CYAN}╭──────────────────────────────────────────────────────────╮\n${NC}"
printf "${CYAN}│${NC}                                                          ${CYAN}│\n${NC}"
printf "${CYAN}│${NC}                  ${BOLD}${CYAN}AIKB Setup${NC}                              ${CYAN}│\n${NC}"
printf "${CYAN}│${NC}          ${CYAN}AI Knowledge Base — Unified Memory${NC}               ${CYAN}│\n${NC}"
printf "${CYAN}│${NC}                                                          ${CYAN}│\n${NC}"
printf "${CYAN}╰──────────────────────────────────────────────────────────╯\n${NC}"
sleep 0.5

printf "${CYAN}╭─ About AIKB ─────────────────────────────────────────────╮\n${NC}"
printf "${CYAN}│${NC} Welcome! This installer sets up AIKB — a private Git      ${CYAN}│\n${NC}"
printf "${CYAN}│${NC} repo that becomes your AI's long-term memory.             ${CYAN}│\n${NC}"
printf "${CYAN}│${NC}                                                           ${CYAN}│\n${NC}"
printf "${CYAN}│${NC} After setup, every agent you configure will read from     ${CYAN}│\n${NC}"
printf "${CYAN}│${NC} this repo at session start — knowing your projects,       ${CYAN}│\n${NC}"
printf "${CYAN}│${NC} preferences, and past decisions automatically.            ${CYAN}│\n${NC}"
printf "${CYAN}│${NC}                                                           ${CYAN}│\n${NC}"
printf "${CYAN}│${NC} ${BOLD}${CYAN}What this script does:${NC}                                   ${CYAN}│\n${NC}"
printf "${CYAN}│${NC}   + Personalize your agent instruction files              ${CYAN}│\n${NC}"
printf "${CYAN}│${NC}   + Wire up whichever AI tools you use                    ${CYAN}│\n${NC}"
printf "${CYAN}│${NC}   + Create a committed, push-ready repo                   ${CYAN}│\n${NC}"
printf "${CYAN}│${NC}                                                           ${CYAN}│\n${NC}"
printf "${CYAN}│${NC} ${DIM}Time to complete: ~3 minutes${NC}                             ${CYAN}│\n${NC}"
printf "${CYAN}╰──────────────────────────────────────────────────────────╯\n${NC}"
sleep 1.5

printf "\n${BOLD}? Ready to begin?${NC} (Y/n) ${GREEN}Y${NC}\n"
sleep 0.8

# ── Platform + prereqs ────────────────────────────────────────────────────────
printf "\n${GREEN}✓ Platform: macOS — good to go${NC}\n"
sleep 0.5
printf "\n  Checking prerequisites...\n\n"
printf "  ${CYAN}Tool               Status        Note${NC}\n"
printf "  ${DIM}──────────────────────────────────────────────────────────${NC}\n"
printf "  git                ${GREEN}✓ 2.43.0${NC}\n"
printf "  python3            ${GREEN}✓ 3.11.9${NC}\n"
printf "  gh (GitHub CLI)    ${GREEN}✓ 2.47.0${NC}    Optional — one-command repo creation\n"
sleep 1.2

# ── Tool selection ────────────────────────────────────────────────────────────
printf "\n─── ${BOLD}Which tools do you use?${NC} ────────────────────────────────\n\n"
printf "  AIKB can be wired into multiple AI tools at once.\n"
printf "  ${DIM}(Space to select, Enter to confirm)${NC}\n\n"
printf "  ${GREEN}> [x] Claude Code${NC}\n"
printf "    ${GREEN}[x] Gemini CLI${NC}\n"
printf "    [ ] OpenCode\n"
printf "    [ ] Cursor\n"
printf "    [ ] ChatGPT (web)\n"
printf "    [ ] Gemini (web)\n"
printf "    [ ] Grok\n"
sleep 2.0

# ── Config ────────────────────────────────────────────────────────────────────
printf "\n─── ${BOLD}Your Configuration${NC} ─────────────────────────────────────\n\n"
printf "  Pre-filled from your Git config. Press Enter to accept.\n\n"
sleep 0.8

printf "${DIM}╭─ GitHub Username ────────────────────────────────────────╮\n${NC}"
printf "${DIM}│${NC} Your username constructs the AIKB repo URL so agents and  ${DIM}│\n${NC}"
printf "${DIM}│${NC} the MCP server can find it.                              ${DIM}│\n${NC}"
printf "${DIM}╰──────────────────────────────────────────────────────────╯\n${NC}"
printf "${BOLD}? GitHub username:${NC} ${DIM}(jane)${NC} ${GREEN}jane${NC}\n"
sleep 0.8

printf "${DIM}╭─ Repo Name ──────────────────────────────────────────────╮\n${NC}"
printf "${DIM}│${NC} The name of your AIKB repo on GitHub.                    ${DIM}│\n${NC}"
printf "${DIM}╰──────────────────────────────────────────────────────────╯\n${NC}"
printf "${BOLD}? Repo name:${NC} ${DIM}(AIKB)${NC} ${GREEN}AIKB${NC}\n"
sleep 0.8

printf "${DIM}╭─ Local Path ─────────────────────────────────────────────╮\n${NC}"
printf "${DIM}│${NC} Where this repo lives. Agents use this to commit updates. ${DIM}│\n${NC}"
printf "${DIM}╰──────────────────────────────────────────────────────────╯\n${NC}"
printf "${BOLD}? Local clone path:${NC} ${DIM}(~/code/AIKB)${NC} ${GREEN}~/code/AIKB${NC}\n"
sleep 0.8

printf "${DIM}╭─ Hostname ───────────────────────────────────────────────╮\n${NC}"
printf "${DIM}│${NC} A short name for this machine (e.g. my-macbook).         ${DIM}│\n${NC}"
printf "${DIM}╰──────────────────────────────────────────────────────────╯\n${NC}"
printf "${BOLD}? Primary machine hostname:${NC} ${DIM}(dev-box)${NC} ${GREEN}dev-box${NC}\n"
sleep 0.8

printf "\n─── ${BOLD}Credential Retrieval (Optional)${NC} ────────────────────────\n\n"
printf "${BOLD}? Which password manager do you use?${NC} ${DIM}(Skip for now)${NC} ${GREEN}Skip for now${NC}\n"
sleep 1.0

# ── Summary ───────────────────────────────────────────────────────────────────
printf "\n─── ${BOLD}Configuration Summary${NC} ──────────────────────────────────\n\n"
printf "${GREEN}╭──────────────────────────────────────────────────────────╮\n${NC}"
printf "${GREEN}│${NC} ${BOLD}GitHub username${NC}  :  jane                                   ${GREEN}│\n${NC}"
printf "${GREEN}│${NC} ${BOLD}Repo name${NC}        :  AIKB                                   ${GREEN}│\n${NC}"
printf "${GREEN}│${NC} ${BOLD}Repo URL${NC}         :  https://github.com/jane/AIKB            ${GREEN}│\n${NC}"
printf "${GREEN}│${NC} ${BOLD}Local path${NC}       :  ~/code/AIKB                             ${GREEN}│\n${NC}"
printf "${GREEN}│${NC} ${BOLD}Hostname${NC}         :  dev-box                                 ${GREEN}│\n${NC}"
printf "${GREEN}│${NC}                                                           ${GREEN}│\n${NC}"
printf "${GREEN}│${NC} ${BOLD}Tools to configure:${NC}                                         ${GREEN}│\n${NC}"
printf "${GREEN}│${NC}     * Claude Code                                          ${GREEN}│\n${NC}"
printf "${GREEN}│${NC}     * Gemini CLI                                           ${GREEN}│\n${NC}"
printf "${GREEN}╰──────────────────────────────────────────────────────────╯\n${NC}"
sleep 2.0

printf "\n${BOLD}? Proceed with setup?${NC} (Y/n) ${GREEN}Y${NC}\n\n"
sleep 1.0

# ── Progress ──────────────────────────────────────────────────────────────────
printf "  Setting up AIKB...\n\n"
sleep 0.5

printf "  ${GREEN}✓${NC} [1/7] Substituting placeholders in agent files\n"
sleep 0.6
printf "  ${GREEN}✓${NC} [2/7] Updating _index.md\n"
sleep 0.5
printf "  ${GREEN}✓${NC} [3/7] Scaffolding personal profile files\n"
sleep 0.6
printf "  ${GREEN}✓${NC} [4/7] Saving configuration to .aikb-config.d/\n"
sleep 0.5
printf "  ${GREEN}✓${NC} [5/7] Adding upstream remote\n"
sleep 0.6
printf "  ${GREEN}✓${NC} [6/7] Creating initial commit\n"
sleep 0.6
printf "  ${GREEN}✓${NC} [7/7] Configuring AI tools\n"
sleep 1.0

# ── Next steps ────────────────────────────────────────────────────────────────
printf "\n─── ${BOLD}Setup Complete${NC} ─────────────────────────────────────────\n\n"
printf "${GREEN}✓${NC} AIKB is configured and committed locally.\n\n"
printf "${BOLD}${CYAN}Next: push to GitHub${NC}\n"
printf "    git push origin main\n\n"
printf "${BOLD}${CYAN}Then fill in two files:${NC}\n"
printf "    * personal/profile.md                — your background, skills, stack\n"
printf "    * personal/dev-environment/dev-box.md — tools on this machine\n\n"
printf "  ${GREEN}✓${NC} Claude Code  ->  ~/.claude/CLAUDE.md\n"
printf "  ${GREEN}✓${NC} Gemini CLI   ->  ~/.gemini/GEMINI.md\n\n"
printf "${BOLD}? Run a 4-minute orientation?${NC} (y/N) N\n"
sleep 0.5
printf "${BOLD}? Run the feature tour?${NC} (y/N) N\n"
sleep 0.5
printf "\n${BOLD}${GREEN}Happy building.${NC}\n"
sleep 3.0
