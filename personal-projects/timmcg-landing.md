---
context: personal
tags: [timmcg.net, landing-page, firebase, gcp, react, vite, cloudflare, dns, typescript, hosting]
last_updated: 2026-03-07
---

# timmcg.net Landing Page
**Last Updated:** 2026-03-07
**Summary:** "Old school hacker" terminal-style landing page for `timmcg.net`. Hosted on GCP to buffer traffic to the home lab.

## Environment Requirements
- **Platform:** Any machine (cross-platform)
- **Tools:** Node.js 18+, npm, Firebase CLI (`npm install -g firebase-tools`)
- **Cloud:** GCP credentials configured (`gcloud auth login`)
- **DNS:** Cloudflare access for domain config

## Overview
- **Objective:** Create a cryptic, dark-themed landing page to serve as the public face of the domain.
- **Tech Stack:** React (TypeScript), Vite, Vanilla CSS.
- **Aesthetic:** Green-on-black, intense CRT effects, "broken" terminal simulation with bit-rot glitches and cryptic symbols (Lost/Matrix inspired).
- **Hosting Strategy:** Deploy to GCP (Firebase Hosting or Cloud Run) to keep the home IP (`home.timmcg.net`) private from casual root-domain traffic.

## Status
- **Repository:** [mcglothi/timmcg-landing](https://github.com/mcglothi/timmcg-landing)
- **Development:** ✅ UI Refinement complete (Darker background, text above scanlines).
    - Large fixed-width terminal (90vw, 90vh).
    - Symbolic resolution: Characters type as "Lost" symbols and resolve into text.
    - Persistent bit-rot: Random characters stay corrupted or re-glitch over time.
    - Enhanced CRT effects (scanlines, flicker, noise).
    - Anonymized header (`NULL_NODE://TTY0`).
- **Deployment:** 🟢 LIVE at [timmcg-landing-1771472937.web.app](https://timmcg-landing-1771472937.web.app).
    - Firebase initialized (`firebase.json`, `.firebaserc`).
    - Build script ready.
- **Custom Domain:** ✅ Complete — resolving to Firebase Hosting via Cloudflare
    - **Issue:** `timmcg.net` needed to cleanly redirect to `www.timmcg.net`.
    - **Action:** `www.timmcg.net` now uses a Cloudflare `CNAME` to `timmcg-landing-1771472937.web.app`, and Cloudflare proxying was disabled on the verification path so Firebase Hosting domain validation could complete cleanly.
    - **Action:** Created a Cloudflare Page Rule `timmcg.net/*` -> `https://www.timmcg.net/$1` (301) for apex-to-www redirection.
    - **Constraint:** Do NOT touch `home.timmcg.net` (points to home fiber static IP).
    - **Zone ID:** `64abc4843bd03f9972b2a08cfe01e891`

## Features
- [x] Intense CRT scanline, flicker, and noise effects.
- [x] Symbolic typing resolution (Matrix/Lost style).
- [x] Persistent "bit-rot" character glitching.
- [x] Abstract, symbolic content (Lost sequence, hex codes).
- [ ] Subdomain routing for other services.

## Roadmap: The Hacker's Puzzle
**Objective:** Transform the landing page into a multi-layered mystery game.
- [ ] **Hidden Terminal Input:** Ensure the `PROBE_THE_VOID...` input line is functional and captures user commands. (Note: Source for this exists on `feynman` but is currently missing on `tesla` and GitHub).
- [ ] **Challenge 1: Numbers Station:** Randomly trigger a numbers-station style code display. If the user types the code into the terminal within a time limit, they unlock the first "hidden room".
- [ ] **Hidden Rooms:** Create a series of mysterious rooms/interfaces that the user can navigate through as they progress down the "rabbit hole".
- [ ] **Prizes/Lore:** Add "little prizes" or lore fragments in each room to keep the user intrigued.

## Project Notes
- **Code Discrepancy (2026-04-08):** The live site (`timmcg.net`) and the compiled assets in `public/assets/` on `tesla` contain advanced features (hidden terminal, `PROBE_THE_VOID`, 3D elements) that are **missing** from the `src/` directory in GitHub and on `tesla`. It is suspected that these changes were made on `feynman` and deployed to Firebase without being pushed to the `master` branch on GitHub. **Do not attempt to reconcile until the source code on `feynman` is pushed.**
