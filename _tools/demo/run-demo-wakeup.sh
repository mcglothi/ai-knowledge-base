#!/bin/bash
# Mock AIKB Wake-up Briefing for demo recordings

# Colors
BOLD='\033[1m'
NC='\033[0m' # No Color
BLUE='\033[34m'
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
DIM='\033[2m'

echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  AIKB Wake-up Briefing · 2026-04-14 09:12 UTC"
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
sleep 0.5

echo -e "\n${BLUE}▸ SESSION${NC}"
echo -e "  Agent    : Claude Code"
echo -e "  Machine  : dev-box (macOS)"
echo -e "  Scope    : personal-projects"
sleep 0.4

echo -e "\n${BLUE}▸ ACTIVE PROJECTS (3)${NC}"
echo -e "  ● portfolio-site      ${GREEN}🟢 Active${NC}     deploy pending — waiting on DNS TTL"
echo -e "  ● homelab-ansible     ${YELLOW}🟡 Attention${NC}  cert expiry 2026-05-02 · auto-renew not verified"
echo -e "  ● llm-experiments     ${GREEN}🟢 Active${NC}     last session: added Ollama sidecar config"
sleep 0.4

echo -e "\n${BLUE}▸ PENDING (2)${NC}"
echo -e "  ⬜ Review Ansible vault password rotation  [homelab-ansible]"
echo -e "  ⬜ Push portfolio v2 branch after DNS confirms"
sleep 0.4

echo -e "\n${BLUE}▸ RECENT EVENTS (last 24h)${NC}"
echo -e "  09:04  deployed portfolio staging build — build clean, no regressions"
echo -e "  08:31  updated homelab cert registry — flagged homelab-ansible for follow-up"
sleep 0.4

echo -e "\n${BLUE}▸ CONTEXT NOTES${NC}"
echo -e "  • portfolio-site: Cloudflare Pages, branch deploys on push to main"
echo -e "  • homelab-ansible: runs on feynman (Arch), inventory at hosts/prod.yml"
echo -e "  • Gemini CLI also active this session — check _runtime/events/ for overlap"
sleep 0.4

echo -e "\n${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  Ready. Load a project file or ask what's next."
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
