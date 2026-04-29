# Zscaler Training Platform

**Status:** ✅ Deployed — v1.1
**Last Updated:** 2026-04-29
**Repo:** https://github.com/tmcglothin_llbean/zscaler-training (private)
**Local dev:** `docker compose up -d` → http://localhost:8080
**Server:** `inf-dv-tim01:8080` — podman rootless via systemd user service

## Purpose

Self-paced training platform for onboarding as lead of L.L.Bean's Zscaler program after the previous senior architect departed. Covers Zscaler fundamentals, ZPA/ZIA deep dives, Terraform automation, and LLB-specific implementation details derived from `APP_Zscaler_Ansible` and `APP_Zscaler_Terraform`.

## Tech Stack

- Plain HTML/CSS/JS — no build step, no Node.js
- Docker Compose + nginx:alpine — serves static files with correct JSON MIME type
- localStorage — quiz progress and scores, no backend
- Hash router — `#home`, `#module/<id>/<section>`

## Modules

| # | ID | Title | Sections |
|---|-----|-------|----------|
| 1 | `01-fundamentals` | Zscaler Fundamentals | 3 |
| 2 | `02-zpa-deepdive` | ZPA Deep Dive | 4 |
| 3 | `03-zia-overview` | ZIA Overview | 3 |
| 4 | `04-terraform` | Terraform for Zscaler | 3 |
| 5 | `05-llb-zpa` | LLB ZPA Implementation | 4 |
| 6 | `06-llb-zia` | LLB ZIA Implementation | 3 |
| 7 | `07-gaps-future` | Gaps, Pain Points & Future | 3 |
| 8 | `08-pse-compliance` | Private Service Edge & Compliance Zones | 3 |
| 9 | `09-operational-realities` | Operational Realities & Troubleshooting | 3 |

**Total:** 29 sections, 74+ quiz questions

## File Structure

```
zscaler-training/
├── docker-compose.yml
├── nginx.conf
├── index.html
├── app.js
├── style.css
└── content/
    ├── modules.json
    ├── 01-fundamentals.json
    ├── 02-zpa-deepdive.json
    ├── 03-zia-overview.json
    ├── 04-terraform.json
    ├── 05-llb-zpa.json
    ├── 06-llb-zia.json
    ├── 07-gaps-future.json
    ├── 08-pse-compliance.json
    └── 09-operational-realities.json
```

## Adding Content

To add a new module:
1. Create `content/10-newmodule.json` following the existing schema
2. Add entry to `content/modules.json` modules array
3. Module auto-appears in sidebar on next page load

Module JSON schema:
```json
{
  "id": "08-newmodule",
  "title": "Module Title",
  "sections": [
    {
      "id": "section-id",
      "title": "Section Title",
      "content": "<html content>",
      "quiz": [
        {
          "question": "Question text?",
          "options": ["A", "B", "C", "D"],
          "correct": 0,
          "explanation": "Why A is correct..."
        }
      ]
    }
  ]
}
```

## Key Design Decisions

- **No build step** — portable, runs anywhere with Docker
- **fetch() requires HTTP** — file:// won't work, Docker is mandatory
- **localStorage state** — quiz scores persist across sessions, no backend needed
- **Score threshold for completion** — 67% (2/3) to pass a section quiz
- **Retry anytime** — users can retake quizzes; scores update on retry

## Context — LLB-Specific Content Sources

Module 5 and 6 content derived from exploration of:
- `APP_Zscaler_Ansible` — naming conventions, SCIM playbooks, broken rename bug
- `APP_Zscaler_Terraform` — app segment structure, admin roles, forwarding rules, commented-out TF

Module 7 documents known issues (corrected in v1.1):
- Broken `rename_app_segment.yml` (missing `body_format: json`)
- SCIM idempotency bug (409 treated as failure)
- TF modules exist in `zpa_test/` but not promoted to `zpa_prod/` (not empty — 4 modules scaffolded)
- Commented-out TF code with no explanation
- `APP_Zscaler_Terraform` has a README + Confluence link; deeper runbooks still missing

Modules 8-9 added 2026-04-29 (content from Copilot, sourced from Teams/Outlook intel + actual repo inspection):
- Module 8: PSE architecture, CDE/PCI-DSS connector isolation, `zscalertwo.net` cloud identity
- Module 9: Troubleshooting methodology, SSL inspection, MCP/API automation frontier

## Deployment — inf-dv-tim01

**Running on:** RHEL 8.10, rootless Podman 4.9.4 (no Docker)
**SSH:** `ssh -i ~/.ssh/svc-ansible_id_rsa -o IdentitiesOnly=yes svc-ansible@inf-dv-tim01`
**Files:** `/home/svc-ansible/zscaler-training/`
**Service:** `~/.config/systemd/user/zscaler-training.service` (enabled, survives reboots)

**Update deployment:**
```bash
rsync -avz --exclude='.git' \
  -e "ssh -i ~/.ssh/svc-ansible_id_rsa -o IdentitiesOnly=yes -o BatchMode=yes" \
  /home/tmcglothin/code/Personal/zscaler-training/ \
  svc-ansible@inf-dv-tim01:/home/svc-ansible/zscaler-training/
# No restart needed — nginx serves files directly from the volume
```

**Restart container if needed:**
```bash
ssh -i ~/.ssh/svc-ansible_id_rsa -o IdentitiesOnly=yes svc-ansible@inf-dv-tim01 \
  "systemctl --user restart zscaler-training.service"
```

## To Deploy to Another Server

Server needs: Podman (RHEL 8+) or Docker. Rsync files, then:
```bash
# Podman
podman run -d --name zscaler-training -p 8080:80 \
  -v /path/to/zscaler-training:/usr/share/nginx/html:ro,z \
  -v /path/to/zscaler-training/nginx.conf:/etc/nginx/conf.d/default.conf:ro,z \
  docker.io/nginx:alpine

# Docker
docker compose up -d
```
