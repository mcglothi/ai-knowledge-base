---
context: personal
tags: [apf, autism-partnership, wordpress, aws, migration, costs, nonprofit, freelance, certificate-registry, ec2]
last_updated: 2026-02-18
---

# APF: Autism Partnership Foundation — Project Overview

**Last Updated:** 2026-02-18
**Summary:** Top-level APF project status with links to active implementation and infrastructure subfiles.
**Status:** MIGRATION COMPLETE. Site live at autismpartnershipfoundation.org on WordPress.com.

---

## Quick Links (read the relevant subfile for details)

| Topic | File |
|-------|------|
| Live WordPress.com site — SSH, plugins, DNS, remaining tasks | [`wordpress-com.md`](wordpress-com.md) |
| Certificate lookup app — EC2, MariaDB, S3, OCR pipeline | [`certificate-registry.md`](certificate-registry.md) |
| AWS infrastructure — what remains, costs, simplification | [`aws-infrastructure.md`](aws-infrastructure.md) |

---

## Project Summary

- **Client:** Autism Partnership Foundation (nonprofit RBT training)
- **Migration:** AWS 3-tier WordPress stack → WordPress.com managed hosting
- **Timeline:** Jan 30 – Feb 9, 2026
- **DNS Cutover:** Feb 6, 2026 (evening)
- **AWS Decommission:** Feb 9, 2026

## Cost Impact

| | Monthly | Annual |
|-|---------|--------|
| Previous AWS | $3,482 | $41,800 |
| WordPress.com (nonprofit) | $53 | $636 |
| AWS remainder (cert lookup) | ~$72 | ~$864 |
| **Current total** | **~$125** | **~$1,500** |
| **Savings** | **~$3,358** | **~$40,296** |

Further simplification of AWS cert-lookup infra could cut another ~$54/mo → **~$18/mo AWS** (pending client approval).

## Migration Timeline

| Date | Milestone |
|------|-----------|
| Jan 30 | AWS audit; XML export (33 files, 4.7 GB) |
| Feb 1–2 | WordPress.com setup; import attempts; LearnDash blocker discovered |
| Feb 2 | DB cleanup — 769k idle users removed; DB 33 GB → 5 GB |
| Feb 3 | Certificate registry created (64,451 certs, standalone MariaDB) |
| Feb 6 (day) | Content, PHP fixes, media (3,662), users (7,517), login fixes |
| **Feb 6 (evening)** | **DNS cutover — live at autismpartnershipfoundation.org** |
| Feb 7–8 | Post-cutover monitoring |
| **Feb 9** | **Health check, plugin cleanup, AWS decommission** |

## Remaining Tasks

- [ ] AWS infra simplification (ALB + NAT removal, saves ~$54/mo) — awaiting client approval
- [ ] Post revision cleanup (45,284 revisions) + quiz stats pruning (26.3M rows) — needs client sign-off
- ✅ OCR enrichment results import (64,336 certs enriched)
- [ ] Ongoing: weekly DB backups for certificate registry

## Pricing Reference

- **Migration quote:** $5,500 fixed (30/40/30 payment split)
- **ROI:** recovers in <2 months from AWS savings
- **Add-ons:** custom theme recreation $1,500–3,000; archive search interface $2,000; 3-month support $1,200
