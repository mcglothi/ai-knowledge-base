# Zscaler Training Platform

**Status:** ✅ Built — v1.0
**Last Updated:** 2026-04-27
**Location:** `/home/tmcglothin/code/Personal/zscaler-training/`
**Serve:** `docker compose up -d` → http://localhost:8080

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

**Total:** 23 sections, 50+ quiz questions

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
    └── 07-gaps-future.json
```

## Adding Content

To add a new module:
1. Create `content/08-newmodule.json` following the existing schema
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

Module 7 documents known issues:
- Broken `rename_app_segment.yml` (missing `body_format: json`)
- SCIM idempotency bug (409 treated as failure)
- Empty module directories in Terraform repo
- Commented-out TF code with no explanation
- No documentation in either repo

## To Deploy Remotely

Copy entire directory to target server, install Docker + compose, then:
```bash
docker compose up -d
```
No other dependencies. Nginx serves all static files.
