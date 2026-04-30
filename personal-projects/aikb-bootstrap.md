---
context: personal
tags: [aikb-bootstrap, aikb.timmcg.net, firebase-hosting, bootstrap, codex, claude, gemini]
last_updated: 2026-03-04
---

# AIKB Bootstrap Site (aikb.timmcg.net)
**Last Updated:** 2026-03-04
**Summary:** Static bootstrap site and script for AIKB onboarding. Source repo: `mcglothi/aikb-bootstrap`. Deployed to Firebase Hosting project `aikb-bootstrap`.

## Repository
- **Repo:** `git@github.com:mcglothi/aikb-bootstrap.git`
- **Local path (feynman):** `~/code/aikb-bootstrap`
- **Hosting config:** `firebase.json` (`public/` directory)
- **Site URL:** `https://aikb.timmcg.net`

## Deployment Rule (Required)
Whenever `mcglothi/aikb-bootstrap` is updated, `aikb.timmcg.net` must be redeployed in the same work cycle.

- Code change only is not sufficient.
- Deploy is required for the live page/script to reflect repo changes.

## Deploy Command
```bash
cd ~/code/aikb-bootstrap
firebase deploy --only hosting
```

## Latest Deploy (2026-03-04)
- Firebase CLI re-auth completed on feynman.
- `firebase deploy --only hosting` successful for project `aikb-bootstrap`.
