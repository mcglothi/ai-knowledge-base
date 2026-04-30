---
context: personal
tags: [cliparr, coupons, browser-extension, truenas, dockge, automation, playwright, mv3, hannaford, shaws]
status: active
last_updated: 2026-03-04
---

# Cliparr

**Last Updated:** 2026-03-04
**Summary:** Unified coupon automation project. Backend runs on home infrastructure; browser extension handles anti-bot-protected store automation in real sessions.

## Repos and locations

- Local repo: `/Users/mcglothi/code/cliparr`
- GitHub: `mcglothi/cliparr`
- Extension source: `browser-extension/cliparr-extension`

## Deployment

- TrueNAS / Dockge stack deployed with API, scheduler, worker, web, postgres, redis
- Public endpoint: `cliparr.home.timmcg.net` (internal home DNS/proxy path)

## Current status

- Core web platform implemented (accounts, schedules, runs, insights)
- Hannaford extension clipping works with load-more and checkpoint flow
- Shaw's extension clipping is partially working; still tuning completion reliability

## Major decisions made

1. Container-only automation is not reliable for protected stores.
2. Hybrid model is preferred:
   - Backend control plane + extension execution plane
3. Human verification checkpoints are a product feature, not an exception.

## Known blockers

- Store anti-bot flows (slider/verification)
- DOM and behavior drift on Shaw's/Albertsons family pages
- Long-run stability and deterministic completion signaling

## Next actions

1. Improve Shaw's full-catalog completion logic
2. Capture coupon-level run manifest (title/id) for validation
3. Add stronger run state UX (`completed`, `partial`, `blocked`, `timed_out`)
4. Add auto-resume after challenge solve

## Notes

- User validated visible coupon clipping behavior on both Hannaford and Shaw's.
- Recent observed Shaw's run result: clipped 90 coupons with 3 load-more clicks, but additional clip buttons remained.
