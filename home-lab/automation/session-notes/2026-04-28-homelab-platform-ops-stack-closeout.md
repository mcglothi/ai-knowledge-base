# Homelab Platform Ops Stack — Session Closeout (2026-04-28)

## Executive Summary
This session completed the core implementation of a secure, repeatable homelab automation platform with:
- Terraform for stable infrastructure state
- Ansible for operational/routine tasks
- GitHub Actions + self-hosted runner execution model
- MinIO-backed Terraform remote state
- GCP (GCS) cloud recovery backup workflow
- Monitoring/alerting/watchdog scaffolding for runner reliability

End state: **Recovery Backup to Cloud workflow achieved successful end-to-end execution** after resolving runner, backend, DNS, MinIO, and auth-path issues.

---

## What Was Built

### Repos and scaffolding
- `homelab-platform` created/initialized, committed, and pushed.
- Standardized repo structure for:
  - `terraform/` modules + stacks
  - `ansible/` inventories, roles, playbooks
  - `docs/` standards, runbooks, roadmaps
  - `semaphore/` project/task templates
  - `.github/workflows/` CI/CD automation

### CI/CD workflow policy
- Enforced model:
  - **PRs → Terraform Plan**
  - **Merge to main → Terraform Apply**
- Added Ansible lint/syntax/check workflows.
- Added recovery backup workflow for state artifacts.

### Terraform
- DNS module scaffold matured to Cloudflare-backed implementation.
- Core-network stack wiring completed.
- Backend generation script (`backend.hcl`) added for runtime config.
- Recovery artifact creation added (state snapshot + manifests/hashes).

### Ansible
- Role-based structure established and playbooks refactored.
- Added/expanded playbooks:
  - patching
  - service restart
  - backup verify
  - health drift check
  - npm proxy verify
  - pihole sync
  - github runner watchdog
  - monitoring stack deploy
- Added Pi-hole shortname sync playbook/role.

### Semaphore
- Added integration docs/templates/matrix for Terraform + Ansible tasks.

### Monitoring
- Added Prometheus rules and scrape snippets for runner health.
- Added Grafana dashboard/provisioning scaffolds.
- Added Alertmanager template.

### SSH / operator friction reduction
- Added scripts/docs for TrueNAS SSH config/bootstrap.
- Identified and fixed key-auth failure root cause: TrueNAS home mode was `777` (too permissive for strict SSH key auth).

---

## Critical Incidents + Resolutions

### 1) Self-hosted runner queue hang
**Symptom:** Workflows queued indefinitely.
**Root cause:** No online runner matching `runs-on: [self-hosted, homelab]`.
**Fix:** Installed/configured runner on Turing with required labels.

### 2) MinIO backend not actually deployed
**Symptom:** Backend endpoint errors; auth redirects; non-S3 responses.
**Root cause:** MinIO references existed in code/docs, but service absent.
**Fix:** Deployed MinIO via Dockge stack; corrected TrueNAS Dockge stacks path.

### 3) MinIO container crash-loop
**Symptom:** Invalid credentials + no bound ports.
**Root cause:** Compose/env mismatch and invalid root credential values.
**Fix:** Corrected compose/env usage, redeployed, verified health and port mappings.

### 4) Backend auth failures (`InvalidAccessKeyId`)
**Symptom:** Terraform init failed listing backend workspaces.
**Root causes:**
- Multiple credential source collisions on self-hosted runner
- Secret value mismatch/override behavior
**Fix:**
- Hardened init path
- Shifted MinIO backend creds to dedicated workflow vars (`MINIO_BACKEND_*`) to avoid AWS env collisions
- Verified successful run after switch

### 5) GCP upload failures on self-hosted runner
**Symptom:** gcloud action/config permission issues; recursive copy misuse.
**Fixes:**
- Reworked gcloud auth/config for writable local dirs
- Corrected GCS copy command usage
- Verified end-to-end success

---

## DNS / Naming Lessons

- FQDN resolution worked while shortnames failed due to missing DNS records and resolver precedence.
- Implemented DNS-side shortname strategy using Pi-hole `custom.list` sync via Ansible.
- Policy decision: shortname behavior should be solved centrally in DNS/DHCP, not per-host hacks.

---

## Security and Operational Decisions

1. Terraform backend primary remains MinIO (S3-compatible), with offsite backup to GCS.
2. Root MinIO credentials were used for unblocking and validation; transition to least-priv backend key is recommended.
3. Prefer deterministic, dedicated credential names over generic AWS env names for non-AWS backends in self-hosted contexts.
4. Session-closeout + AIKB capture should be default for major operations work.

---

## Final Verified State (Session End)

- Recovery workflow reached successful end-to-end execution with:
  - backend init
  - state snapshot/recovery artifacts
  - GCP auth
  - GCS upload
- Project is operational for the defined objective.

---

## Recommended Follow-ups

1. Rotate MinIO root password and store final values in Vaultwarden.
2. Re-establish least-priv backend user (`tfstatekey`) and validate in pipeline.
3. Remove remaining debug-only workflow instrumentation.
4. Add quarterly DR restore drill checklist and runbook evidence capture.
5. Continue container control-plane consolidation strategy (Dockge-first).

