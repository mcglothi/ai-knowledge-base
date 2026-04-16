# Personal Profile

**Last Updated:** 2026-04-16
**Summary:** Tim McGlothin — Unix engineer at L.L. Bean. Deep Linux background, heavy Ansible/infrastructure automation focus.

---

## Background

Tim McGlothin is a Unix engineer at L.L. Bean (Freeport, ME). He has been using Linux since 1997 — it is his primary platform both at home and at work. His day-to-day centers on enterprise infrastructure automation: writing Ansible playbooks, roles, and templates that run on Ansible Automation Platform (AAP) and are source-controlled in GitHub. He works across a multi-team environment, supporting other teams (DBA, Distribution, EDW, E-commerce) as well as owning core ESG Unix infrastructure.

---

## Skills

**Languages:** Bash, Python, YAML/Jinja2, some PowerShell
**Automation:** Ansible (playbooks, roles, collections, EDA), Ansible Automation Platform (AAP/Tower)
**Infrastructure:** Nutanix AHV (Prism), Red Hat Satellite, Infoblox, CrowdStrike Falcon, Nessus, CommVault, Control-M
**OS:** RHEL 6/7/8/9 (primary), AIX, Windows Server (supporting)
**Identity:** Centrify, Active Directory (llbean.com)
**Tools:** git, GitHub, GitHub Actions, ansible-builder, Podman
**Compliance:** CIS Benchmarks (RHEL 8/9), RHEL hardening

---

## Current Focus

- Infrastructure automation via Ansible / AAP at L.L. Bean
- AIKB onboarding — building persistent memory for AI-assisted work
- RHEL 8/9 CIS compliance hardening

---

## Communication Preferences

- Concise responses; skip preamble
- Direct answers — no over-validation
- Show code, not just descriptions
- Unix-native mindset: prefer shell/bash solutions where appropriate
- No emojis unless asked

---

## Notes for Agents

- Linux since 1997 — assume strong Unix fundamentals; no need to explain basic shell concepts
- Primary work repos live in `~/code/` (e.g. `~/code/APP_Ansible_Prod_ESGUnix`)
- Ansible playbooks follow naming convention: `PREFIX_Descriptive_Name.yml` (see CLAUDE.md)
- Variable prefixes: `cli_` for CLI vars, `g_` for global, 3+ char prefix for role vars
- Service account for Ansible runs is `svc-ansible`
- Vault-encrypted secrets live in `group_vars/vault.yml`
- Production runs go through AAP (Ansible Tower), not direct CLI
