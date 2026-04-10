#!/usr/bin/env bash
# =============================================================================
# AIKB Feature Tour
# A guided walkthrough of the habits and features that make AIKB useful
# after the initial install.
#
# Run standalone: bash _tools/feature-tour.sh
# =============================================================================

set -euo pipefail

BOLD='\033[1m'
DIM='\033[2m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RESET='\033[0m'

TOTAL=7

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
  if [[ -n "${AIKB_TOUR_AUTO_ADVANCE:-}" ]] || [[ ! -t 0 ]]; then
    sleep 0.05
    return 0
  fi
  read -r
}

page 1 "AIKB HAS A BASE LAYER AND A POWER LAYER"

echo -e "  The base layer is simple:"
echo -e "  ${BOLD}Markdown + Git + agent instructions.${RESET}"
echo ""
echo -e "  That's enough to get persistent memory across sessions."
echo ""
echo ""
echo -e "  The power layer is optional:"
echo -e "  ${BOLD}operator loop, approvals, operator intents, and search.${RESET}"
echo ""
echo -e "  You do ${BOLD}not${RESET} need all of it on day one."
echo -e "  But as AIKB grows, this layer is what keeps useful features"
echo -e "  from getting buried."

next

page 2 "START WITH THE OPERATOR LOOP"

echo -e "  If you only adopt one advanced workflow, make it this one:"
echo ""
echo -e "  ${DIM}    python3 _tools/memory-pipeline/runtime_cli.py hud${RESET}"
echo -e "  ${DIM}    python3 _tools/memory-pipeline/runtime_cli.py focus set ...${RESET}"
echo -e "  ${DIM}    python3 _tools/memory-pipeline/runtime_cli.py closeout ...${RESET}"
echo ""
echo -e "  ${BOLD}hud${RESET} answers: what state are we in?"
echo -e "  ${BOLD}focus set${RESET} keeps the current objective visible."
echo -e "  ${BOLD}closeout${RESET} captures how the session ended."
echo ""
echo -e "  This turns AIKB from static notes into a working loop."

next

page 3 "USE APPROVALS TO BUILD TRUST"

echo -e "  Not every decision should happen silently in chat history."
echo ""
echo -e "  Use approvals when something has:"
echo -e "  ${DIM}    • architectural consequences${RESET}"
echo -e "  ${DIM}    • money/spend impact${RESET}"
echo -e "  ${DIM}    • security implications${RESET}"
echo -e "  ${DIM}    • preference ambiguity${RESET}"
echo ""
echo -e "  Example:"
echo -e "  ${DIM}    python3 _tools/memory-pipeline/approvals_cli.py add \\\n      --agent \"Claude Code\" --project \"AIKB\" \\\n      --action \"Publish docs redesign\"${RESET}"
echo ""
echo -e "  This gives the operator a visible sign-off surface."

next

page 4 "CAPTURE YOUR SHORTHAND"

echo -e "  When you keep saying things like:"
echo -e "  ${DIM}    \"wrap up for now\"${RESET}"
echo -e "  ${DIM}    \"restart staging\"${RESET}"
echo -e "  ${DIM}    \"wake the lab server\"${RESET}"
echo ""
echo -e "  capture them in ${BOLD}operator intents${RESET}."
echo ""
echo -e "  That means:"
echo -e "  ${DIM}    phrase -> execution path -> verify success -> cleanup${RESET}"
echo ""
echo -e "  The result is simple but powerful:"
echo -e "  future sessions stop rediscovering the same path."

next

page 5 "SEARCH IS THE FIRST GREAT ADDON"

echo -e "  When your AIKB gets bigger, users stop remembering where"
echo -e "  everything lives."
echo ""
echo -e "  That's where ${BOLD}aikb-search${RESET} starts paying for itself."
echo ""
echo -e "  Good questions:"
echo -e "  ${DIM}    \"what changed since my last session?\"${RESET}"
echo -e "  ${DIM}    \"what approvals are still pending?\"${RESET}"
echo -e "  ${DIM}    \"where is the runbook for staging deploys?\"${RESET}"
echo ""
echo -e "  Search should help the agent ${BOLD}find the right file${RESET}."
echo -e "  The file remains the source of truth."

next

page 6 "A GOOD FIRST-WEEK ADOPTION PLAN"

echo -e "  ${BOLD}Day 1${RESET}"
echo -e "    • Fill in profile + dev environment"
echo -e "    • Run ${BOLD}hud${RESET} once"
echo ""
echo -e "  ${BOLD}Day 2${RESET}"
echo -e "    • Start using ${BOLD}closeout${RESET} when you stop"
echo -e "    • Add one real approval row"
echo ""
echo -e "  ${BOLD}Day 3${RESET}"
echo -e "    • Capture your first operator intent"
echo -e "    • Enable search if the repo is growing"
echo ""
echo -e "  The goal is not to enable every feature."
echo -e "  The goal is to build habits that scale with the repo."

next

page 7 "COME BACK TO THIS TOUR"

echo -e "  As AIKB grows, this tour becomes your feature map."
echo ""
echo -e "  Run it again any time:"
echo -e "  ${DIM}    bash _tools/feature-tour.sh${RESET}"
echo ""
echo -e "  Best companion docs:"
echo -e "  ${DIM}    docs/operator-loop.md${RESET}"
echo -e "  ${DIM}    docs/search-setup.md${RESET}"
echo -e "  ${DIM}    home-lab/runbooks/operator-intents.md${RESET}"
echo ""
echo -e "  ${BOLD}${GREEN}Teach the workflow, not just the files.${RESET}"

next "Press Enter to finish"

clear
