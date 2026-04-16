# Machine Profile: J9RC8S3-LP

**Last Updated:** 2026-04-16
**Summary:** Work laptop running Ubuntu 24.04 LTS under WSL2 on Windows. Primary machine for L.L. Bean infrastructure work.

---

## Identity

| Field | Value |
|-------|-------|
| Hostname | `J9RC8S3-LP` |
| OS | Ubuntu 24.04.3 LTS (WSL2 — Windows host) |
| Architecture | `x86_64` |
| Role | Work laptop — primary daily driver for LLBean engineering |
| Code root | `~/code/` |
| AIKB path | `~/code/AIKB/` |
| Shell | `zsh` |
| Python command | `python3` (3.12.3) |

---

## Package Manager

`apt` (Ubuntu)

---

## Installed Tools

- [x] `git`
- [x] `gh` (GitHub CLI)
- [x] `python3` (3.12.3)
- [x] `ansible` + `ansible-playbook`
- [ ] `docker` (not confirmed)
- [ ] `node` / `npm` (not confirmed)

---

## Key Paths

| Path | Purpose |
|------|---------|
| `~/code/AIKB/` | AI Knowledge Base |
| `~/code/APP_Ansible_Prod_ESGUnix/` | Primary LLBean Ansible repo (ESG Unix) |
| `~/.bw_session` | Bitwarden session token (secrets manager) |

---

## Notes

- Running WSL2 on a Windows work laptop — kernel is `6.6.87.2-microsoft-standard-WSL2`
- Bitwarden pattern: `BW_SESSION=$(cat ~/.bw_session)` — never run `bw unlock` (hangs interactively)
- AAP/Tower runs production Ansible; local `ansible-playbook` is for dev/testing only
- SSH to LLBean servers: always use `svc-ansible` — `~/.ssh/config` handles this automatically for `*.llbean.com` and common host prefixes. Personal AD account requires Centrify MFA and will block.
