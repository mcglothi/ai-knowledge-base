# Active Sessions

**Purpose:** Live session presence for AI agents. Agents register at session start and deregister at session end. If another agent has a Last Write within ~2 hours, pull before every AIKB write this session.

---

| Agent | Machine | Mode | Last Write | Task |
|-------|---------|------|-----------|------|
| *(no active sessions)* | — | — | — | — |

---

<!--
REGISTRATION FORMAT:
| Claude Code | hostname | local/MCP | 2024-01-15 14:30 UTC | Brief task description |

Remove your row at session end and commit:
git add . && git commit -m "AI Update: _agents/active.md — session end" && git push origin main
-->
