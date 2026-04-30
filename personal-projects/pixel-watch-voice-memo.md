---
context: personal
tags: [pixel-watch, wear-os, voice, memo, telegram, sideload, chatops, aikb]
status: planning
last_updated: 2026-04-23
---

# Pixel Watch Voice Memo Capture
**Last Updated:** 2026-04-23
**Summary:** Wear OS capture path for quickly recording a spoken memo on Pixel Watch 4 and handing it off to the AIKB ideas pipeline with minimal friction.

## Goal

When an idea hits while I am away from the workstation, I want the watch to:

1. capture the memo fast
2. convert it into usable text
3. send it into the same ideas workflow that Telegram already uses
4. avoid duplicate action on the same memo later

## Recommended Shape

Build a small standalone Wear OS app with:

- one large record button
- live transcription or post-record transcription
- send / cancel controls
- a simple draft queue for failed uploads

The app should be sideloadable during development and portable enough to keep later if it proves useful.

## Why Custom App

The stock Telegram app is fine for text, but the watch memo workflow wants:

- one-tap record
- clear confirm/cancel flow
- a predictable handoff into AIKB
- a local fallback if network is weak

That points to a dedicated app rather than hoping a chat client UX will line up with the capture habit.

## v1 Transport

The first version should not try to do everything on the watch.

Best v1 path:

- use the watch mic to capture speech
- obtain text from the system speech recognizer or a simple in-app transcription step
- POST the transcript to a small TrueNAS relay
- have the relay write the note into `ideas/inbox/`

This keeps the watch app light and lets the backend stay boring.

## Later Options

After the text flow works, we can add:

- raw audio attachment storage
- optional server-side transcription
- a reply-back confirmation into Telegram
- voice memo drafts synced across devices

## Security / Access

- Keep the relay behind Tailscale or an authenticated reverse proxy.
- Use a per-device token for the watch app.
- Do not leave the capture endpoint open unauthenticated on the LAN.

## Development Plan

1. Create the Wear OS module in Android Studio.
2. Wire record + transcribe + send.
3. Point the send path at a TrueNAS relay that uses the same idea-capture backend as Telegram.
4. Test on the watch emulator.
5. Sideload a release build onto Pixel Watch 4.
6. Validate the note lands in `ideas/inbox/` and only one action is taken per memo.

## Open Questions

- Should the first release be text-only after speech capture, or should it store audio too?
- Should the relay live inside the Telegram ideas bot service or as a separate watch-memo service?
- Should failed memos queue locally on the watch or be dropped with a retry hint?

