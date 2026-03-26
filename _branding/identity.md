---
tags: [branding, identity, aikb, signal-relay]
last_updated: 2026-03-11
status: active
---

# AIKB Brand Identity

**Last Updated:** 2026-03-11
**Summary:** Canonical brand direction for the public AIKB project. Defines the Signal Relay identity system, tone, and visual rules used across the README, landing mock, and launch materials.

---

## Brand Core

- **Name:** `AIKB`
- **Expansion:** `AI Knowledge Base`
- **Primary tagline:** `Persistent memory for your AI tools.`
- **Supporting line:** `Shared context across sessions, tools, and machines.`
- **Positioning:** AIKB gives agents durable, inspectable memory without forcing users into a hosted black box.

## Chosen Direction

### Signal Relay

AIKB should feel like context moving cleanly between sessions rather than "AI thinking harder."

This direction favors:
- relay marks over brain icons
- structured geometry over soft blobs
- calm confidence over hype
- precise product language over futurist claims

## Personality

- Calm
- Exact
- Trustworthy
- Technical
- Intentional

Avoid:
- gimmicky AI puns
- sci-fi glow aesthetics
- "magic" language
- generic brain / chip / node-graph iconography

## Visual System

### Logo Direction

Preferred logo family:
- custom `AIKB` wordmark
- compact mark built from routed line segments
- subtle emphasis on the `K` to make the acronym feel designed rather than default typeset
- a routed circuit spine that can connect the letters without turning the logo into a busy diagram

Files:
- [`aikb-wordmark.svg`](aikb-wordmark.svg)
- [`aikb-mark.svg`](aikb-mark.svg)
- [`../preview/wordmark-exploration.html`](../preview/wordmark-exploration.html)

Current wordmark choice:
- Direction A editorial wordmark
- serif-led `AIKB` lockup with a subtle accent on the `K`
- chosen palette: Mineral cobalt, using a midnight base with a softened cobalt accent for a more authored feel
- chosen posture: Balanced spacing, intended as the default lockup across README, docs, and previews

### Color Palette

| Token | Hex | Use |
|-------|-----|-----|
| Midnight | `#0C1522` | Backgrounds, headers, primary dark surfaces |
| Mineral | `#F6F1E9` | Wordmark tone, light surfaces, warm text moments |
| Mineral Cobalt | `#7DD3FC` | Primary accent, key brand signature |
| Steel Mist | `#94A3B8` | Secondary text, dividers, supporting UI |
| Deep Night | `#070D16` | Rich dark backing tone for gradients and panels |

Rules:
- Lead with Midnight + Mineral + Mineral Cobalt
- Keep cobalt clean and restrained; it should feel precise rather than loud
- Avoid purple as a primary accent
- Use gradients only as subtle atmosphere, never as the main identity

### Typography

Recommended stack:
- Headings: `Space Grotesk`
- Body: `Inter`
- Technical accents: `IBM Plex Mono`

Fallback intent:
- geometric but readable headings
- highly legible documentation body copy
- restrained monospace for commands and diagrams

## Voice

Write like:
- the product understands the pain
- the mechanism is clear
- the trust model is explicit

Good patterns:
- "Your AI tools should not start from zero."
- "AIKB keeps shared context in a repo you control."
- "Local-first, Git-backed, fully inspectable."

Avoid:
- "revolutionary"
- "supercharge"
- "AI-powered platform"
- "unlock the future"

## Hero Copy

Preferred hero:

```md
# AIKB

> Persistent memory for your AI tools.

AIKB gives your agents shared context that survives across sessions, tools, and machines.
It stays local-first, Git-backed, and fully inspectable, so your memory system feels like infrastructure you control instead of a black box you hope is right.
```

## Usage Notes

Use this identity system for:
- GitHub README
- launch screenshots and social previews
- temporary landing pages
- future docs site or product page

If future branding work conflicts with this document, update this file first so the repo keeps one source of truth.
