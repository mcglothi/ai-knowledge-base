---
context: personal
tags: [security-agents, shannon, keygraph, pentest, appsec, homelab, hermes, defensive-security, automation]
status: planning
last_updated: 2026-04-23
---

# Project: Security Agents with Shannon

**Last Updated:** 2026-04-23
**Status:** Planning
**Summary:** Explore a defensive security-agent lane alongside Hermes: autonomous agents that can pentest owned web apps/APIs, learn from findings, and help secure ongoing homelab and project operations.

---

## Seed Idea

Set up security agents that can pentest and learn in order to secure ongoing operations. Initial candidate/tooling anchor:

- Shannon by Keygraph: https://github.com/KeygraphHQ/shannon
- Repo description observed 2026-04-23: Shannon Lite is an autonomous white-box AI pentester for web applications and APIs. It analyzes source code, identifies attack vectors, and executes working exploits against running apps so findings are proven before reporting.

## Relationship to Hermes

Hermes is the operations/remediation lane: alert intake, triage, and controlled execution through approved playbooks.

This project should become the security validation lane:

- test owned applications and internal APIs before and after deployments
- feed confirmed vulnerabilities into Hermes or a remediation queue
- generate reproducible proof-of-concept findings for review
- learn recurring weakness patterns across personal projects and homelab services
- become a CI/CD or release-gate option only after the workflow is trusted

## Guardrails

This lane is defensive only. Scope must stay limited to owned systems, explicit lab targets, intentionally vulnerable apps, or targets with written authorization.

Initial safety constraints:

- run in an isolated workspace/network segment first
- never aim autonomous exploitation at third-party systems
- require explicit target allowlists
- keep credentials in Vaultwarden/Delinea references, not project files
- preserve logs, commands, and generated reports for review
- prefer read-only reconnaissance until the toolchain and blast radius are understood

## Candidate First Targets

- OpenSoak local/staging app
- AIKB Bootstrap site staging environment
- internal FastAPI services behind Authentik/forward-auth
- intentionally vulnerable local targets such as OWASP Juice Shop for baseline validation

## First Pass Plan

1. Review Shannon Lite install/runtime requirements and license implications.
2. Build a disposable local lab with one intentionally vulnerable app and one owned toy app.
3. Define a target allowlist format and report storage path.
4. Run Shannon manually and evaluate report quality, reproducibility, and safety.
5. Decide whether Shannon becomes a standalone tool, a Hermes-triggered workflow, or part of a broader security-agent stack.

## Open Questions

- Where should reports live: AIKB `_runtime`, a dedicated security repo, or per-project artifacts?
- Should findings flow into GitHub issues, Hermes remediation prompts, or an AppSec dashboard?
- What level of autonomy is acceptable for authenticated testing against homelab services?
- Can the learning loop become a reusable corpus of project-specific security patterns without storing secrets or sensitive exploit payloads?
