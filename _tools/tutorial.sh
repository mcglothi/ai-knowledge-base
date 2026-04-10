#!/usr/bin/env bash
# =============================================================================
# AIKB Onboarding Tutorial
# A 4-minute orientation for anyone new to AI in the terminal.
#
# Run standalone:  bash _tools/tutorial.sh
# Called by install.sh at setup completion if the user opts in.
# =============================================================================

set -euo pipefail

# ── Colors & styles ───────────────────────────────────────────────────────────
BOLD='\033[1m'
DIM='\033[2m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RESET='\033[0m'

TOTAL=6

# ── Layout helpers ────────────────────────────────────────────────────────────

page() {
  local n="$1" title="$2"
  clear
  echo ""
  echo -e "  ${DIM}${n} of ${TOTAL}${RESET}"
  echo ""
  echo ""
  echo -e "  ${BOLD}${CYAN}${title}${RESET}"
  echo ""
  echo -e "  ${DIM}──────────────────────────────────────────────────────${RESET}"
  echo ""
}

next() {
  local label="${1:-Press Enter to continue}"
  echo ""
  echo ""
  echo -e "  ${DIM}→  ${label}${RESET}"
  read -r
}

# ── Pages ─────────────────────────────────────────────────────────────────────

# 1 ── What this is
page 1 "IT DOESN'T JUST ANSWER — IT ACTS"

echo -e "  A chatbot produces text."
echo -e "  ${BOLD}You${RESET} decide what to do with it."
echo ""
echo ""
echo -e "  Claude Code is different."
echo ""
echo -e "  It ${BOLD}reads files${RESET} on your machine."
echo -e "  It ${BOLD}runs commands${RESET} in your terminal."
echo -e "  It ${BOLD}writes and edits${RESET} files directly."
echo ""
echo ""
echo -e "  Think of it as working ${BOLD}alongside someone who has a keyboard${RESET} —"
echo -e "  not asking a question and getting a text response."

next

# 2 ── Tool calls
page 2 "WHAT THOSE TOOL CALLS ARE"

echo -e "  You'll see things like this appear mid-session:"
echo ""
echo ""
echo -e "  ${DIM}    ●  Read   personal/profile.md${RESET}"
echo -e "  ${DIM}    ●  Bash   git status${RESET}"
echo -e "  ${DIM}    ●  Edit   projects/my-project.md${RESET}"
echo ""
echo ""
echo -e "  That's real. The file is actually being read."
echo -e "  The command is actually running."
echo ""
echo ""
echo -e "  Some actions ask for ${BOLD}your approval${RESET} before they happen."
echo -e "  Read them — they tell you exactly what will change."
echo -e "  Five seconds now beats an unwanted edit."

next

# 3 ── AIKB
page 3 "WHY IT REMEMBERS YOU"

echo -e "  Every chatbot session starts from zero."
echo ""
echo -e "  You re-explain your setup, your projects, your preferences."
echo -e "  Every. Single. Time."
echo ""
echo ""
echo -e "  ${BOLD}${YELLOW}AIKB is the fix.${RESET}"
echo ""
echo ""
echo -e "  The agent reads your knowledge base at the start of every"
echo -e "  session. It already knows who you are, what you're working"
echo -e "  on, and how your machine is configured."
echo ""
echo ""
echo -e "  ${BOLD}Fill in personal/profile.md first.${RESET}"
echo -e "  That's the most valuable 10 minutes you'll spend here."

next

# 4 ── Short prompts
page 4 "YOU DON'T NEED BIG PROMPTS"

echo -e "  Chatbot habit: write a long, careful prompt."
echo -e "  Pack in all the context. Explain everything."
echo ""
echo -e "  That habit makes sense there. ${BOLD}Unlearn it here.${RESET}"
echo ""
echo ""
echo -e "  The context is already loaded from your knowledge base."
echo -e "  Short prompts work."
echo ""
echo ""
echo -e "  ${DIM}    \"Help me add a new project\"${RESET}"
echo -e "  ${DIM}    \"What should I work on next?\"${RESET}"
echo -e "  ${DIM}    \"Set up Python for this project\"${RESET}"
echo ""
echo ""
echo -e "  Say what you want. The agent knows the rest."

next

# 5 ── When things go wrong
page 5 "WHEN SOMETHING LOOKS WRONG — JUST SAY SO"

echo -e "  Chatbot mistake: text you disagree with."
echo -e "  You ignore it and move on."
echo ""
echo ""
echo -e "  Terminal AI mistake: a file gets changed."
echo -e "  A command runs that you didn't intend."
echo ""
echo ""
echo -e "  ${BOLD}If something looks off, say so immediately.${RESET}"
echo ""
echo -e "  ${DIM}    \"Wait, stop\"${RESET}"
echo -e "  ${DIM}    \"That's not what I meant\"${RESET}"
echo -e "  ${DIM}    \"Undo that and let's try differently\"${RESET}"
echo ""
echo ""
echo -e "  The agent doesn't take irreversible actions without asking."
echo -e "  But you're the final check — ${BOLD}stay in the loop.${RESET}"

next

# 6 ── Go
page 6 "YOU'RE READY"

echo -e "  The best way to learn this is to ${BOLD}use it${RESET}."
echo -e "  Not to read about it."
echo ""
echo ""
echo -e "  ${BOLD}Start here:${RESET}"
echo ""
echo -e "    1.  Fill in ${BOLD}personal/profile.md${RESET} — your background and skills"
echo -e "    2.  Open a new terminal session"
echo -e "    3.  Start with something you ${BOLD}actually want to do${RESET}"
echo ""
echo ""
echo -e "  ${DIM}You can run this tutorial again any time:${RESET}"
echo -e "  ${DIM}    bash _tools/tutorial.sh${RESET}"
echo ""
echo ""
echo -e "  ${BOLD}${GREEN}Good luck.${RESET}"

next "Press Enter to finish"

clear
