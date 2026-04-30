# Active Sessions

**Purpose:** Live session presence for AI agents. Agents register at session start and deregister at session end. If another agent has a recent Last Write, pull before every AIKB write and compare repo/scope claims before editing a dirty external repo.

**Staleness:** Entries older than ~2 hours may be stale, but do not clear them blindly. First check the claimed repo for recovery evidence such as uncommitted files, untracked files, or recent file mtimes in the claimed scope.

**Scope format:** Use repo-relative path prefixes or globs when possible, such as `preview/*`, `docs/*`, or `src/auth/*`.

---

| Agent | Machine | Mode | Last Write | Repo | Scope | Task |
|-------|---------|------|-----------|------|-------|------|
| *(no active sessions)* | — | — | — | — | — | — |

---

<!--
REGISTRATION FORMAT:
| Claude Code | hostname | local/MCP | 2024-01-15 14:30 UTC | ai-knowledge-base | docs/* | Brief task description |

Remove your row at session end and commit:
git add . && git commit -m "AI Update: _agents/active.md — session end" && git push origin main
-->
