---
context: personal
tags: [project, terminal, ssh, sftp, macos, linux, session-management, automation, macros, remote-ops]
status: planning
last_updated: 2026-03-31
---

# Project: Remote Operator Workbench

**Last Updated:** 2026-03-31
**Status:** Planning
**Summary:** Cross-platform remote-ops workspace for macOS and Linux inspired by the MobaXterm workflow: saved sessions, grouped multi-exec, secure credential handling, drag/drop file transfer, and reusable macros without requiring Windows.

---

## Why This Exists

MobaXterm is valuable less because of any single protocol and more because it bundles several operator workflows into one place:

- saved connection/session management
- fast multi-host command broadcast
- built-in password and key handling
- drag/drop file transfer during SSH work
- macro/snippet replay

Current tools on macOS and Linux cover slices of this well, but not the whole operator experience in one cohesive surface. This project exists to close that gap for daily infrastructure work.

## Problem Statement

The main pain is not "I need another terminal emulator." The pain is context switching:

- terminal in one app
- host list in another place
- secrets in a separate tool with no workflow glue
- file transfer in Finder/CLI or a second app
- repeated command sequences in notes or shell history
- multi-host actions handled ad hoc and with too much risk

The goal is a workspace that makes common remote-ops loops feel deliberate, fast, and safe on macOS and Linux.

## Required Capabilities

### Must-have
- SSH session management with folders/tags/groups
- Grouped multi-exec / broadcast with visible safety state
- Secure credential references and autofill flows
- Drag/drop upload and download during SSH sessions
- Macros/snippets for repeatable terminal actions
- Cross-platform support on macOS and Linux

### Strongly desired
- SFTP browser and remote file editing
- Jump host / proxy support
- SSH key + agent integration
- Port forwarding management
- Host metadata, notes, and environment labels
- Session restore / pinned workspaces

### Explicit non-goals for MVP
- Building a full terminal emulator from scratch
- Replacing every protocol MobaXterm supports
- X11 server parity
- RDP/VNC in v1
- Team collaboration and cloud sync in the first cut

## What Existing Tools Already Cover

### iTerm2
- Strong macOS-only operator ergonomics
- Broadcast input
- Automatic profile switching based on host/user/path
- Shell integration supports drag/drop upload and click-to-download over SSH
- Password manager exists, but the product is not cross-platform

### WezTerm
- Excellent cross-platform terminal foundation
- Native SSH client and multiplexing
- SSH domains can auto-populate from `~/.ssh/config`
- Strong scripting and workspace potential
- Missing the higher-level operator surface: session library, file manager, macro UX, credential workflows

### Termius
- Closest polished commercial fit
- Strong vault/credential story, snippets, SFTP, and cross-device sync
- Good benchmark for UX and scope
- Less appealing if the goal is self-hosted / local-first / fully ownable workflows

### Tabby
- Strong open-source baseline
- SSH/SFTP connection manager, encrypted secrets container, plugins, login scripts, quick commands
- Likely the strongest open-source comparison target
- Still feels terminal-first rather than workflow-first for the exact MobaXterm replacement gap

### Termora / Electerm
- Both validate demand for integrated SSH + transfer + session tooling
- Useful reference points for feature packaging
- Good landscape checks before committing to architecture

## Project Direction

Build an **operator workbench**, not just another terminal.

The differentiator should be:

1. **Host-centric workflow**
   - sessions, groups, tags, notes, environment coloring, recent activity
2. **Safer multi-host execution**
   - explicit broadcast groups, preview state, protected hosts, confirmation gates
3. **Credential workflow glue**
   - system keychain/libsecret integration and optional Vaultwarden references
4. **Integrated transfer surface**
   - remote/local file pane and drag/drop SCP/SFTP flows
5. **Macros that understand operator intent**
   - snippets, parameterized macros, and host/group targeting

## Product Shape Options

### Option A — VS Code extension suite

This is a credible path if the product is primarily for people who already live in VS Code.

**What VS Code gives us well**
- Tree/activity-bar views for hosts, groups, macros, and saved workspaces
- Commands, keybindings, status bar items, and context menus
- Secret storage via `ExtensionContext.secrets`
- Local/global extension storage
- Webviews for custom panes when the standard APIs are not enough
- Immediate leverage from Remote-SSH instead of building the entire remote editing story ourselves

**What makes it attractive**
- Lowest time-to-first-usable-tool
- Easy way to validate session trees, snippets, host metadata, and broadcast workflows
- Natural distribution model if the first users are developers/operators
- Can piggyback on VS Code terminals and remote workspaces

**What it does poorly**
- It is not a general terminal replacement
- UX is constrained by VS Code extension boundaries and layout rules
- Drag/drop file transfer can be built, but it will feel more like an extension pane than a native remote file manager
- Multi-exec/broadcast across arbitrary terminals is possible, but less "own the whole workspace" than a dedicated app
- Extension behavior becomes more complex across local vs remote extension hosts

**Best interpretation**
- Great **wedge/MVP path**
- Weakest fit if the real dream is "MobaXterm for Mac/Linux" as a primary daily remote-ops cockpit outside the editor

### Option B — Standalone desktop app

This is the better long-term fit if the product should feel like an operator-native workspace rather than an editor add-on.

**What it gives us**
- Full control of session/file/macro layout
- Cleaner drag/drop SCP/SFTP UX
- Stronger identity as a cross-platform remote-ops product
- Useful even when no code workspace is open

**What it costs**
- More infrastructure to build
- More packaging and update work
- More responsibility for terminal/session behavior from day one

### Recommended stance right now

Use the **VS Code extension suite as the incubation path**, not necessarily the final destination.

That means:
- validate the host tree, macro model, credential references, and multi-exec UX inside VS Code first
- keep the domain model portable so it can later move into a standalone app
- avoid coupling the whole concept to editor-only assumptions

If the extension proves that the real value is mostly:
- saved hosts
- grouped commands
- snippets/macros
- remote file actions

then the extension suite may be enough.

If the value proves to be:
- terminal-first daily ops
- workspace restore
- drag/drop remote file flow
- all-day multi-host orchestration

then the extension should become the prototype, not the endpoint.

## Recommended Architecture

### Product shape
- Incubate first as a VS Code extension suite or focused extension pack
- Preserve a path to a desktop app for the long-term product form
- Local-first data model
- Single-user focused MVP

### Technical direction
- **Incubation path:** VS Code extension(s) with Tree View + commands + webview where needed
- **Long-term standalone path:** Tauri + React frontend with Rust core/backend
- **Transport:** OpenSSH compatibility first; prefer existing SSH config/agent behavior over inventing a parallel auth model
- **Storage:** SQLite or portable JSON+SQLite hybrid for hosts, groups, macros, recent sessions, and audit history
- **Secrets:** VS Code secret storage in extension mode; OS keychain/libsecret in standalone mode; optional Vaultwarden integration later

### Why this direction
- VS Code drastically lowers MVP cost for session trees, commands, metadata, and remote-workspace integration
- A portable domain model avoids betting the entire project on one shell/editor surface too early
- If the concept escapes editor boundaries, Tauri/Rust is still the cleanest long-term destination

## Reuse Opportunities From Existing Work

### AI Hub sessions
- `ai-hub/apps/sessions` already uses a session-registry model with persisted metadata and tmux-backed lifecycle ideas
- Useful pattern for session inventory, resumability, and audit logging

### AI Session Manager TUI
- Reinforces the idea that the real gap is orchestration and visibility, not raw terminal rendering
- Some of its concepts (session sidebar, safety controls, stats/metadata pane) map well here

## MVP Proposal

### Phase 0 — Product-shape spike
- Prototype the extension route before committing to the desktop route
- Confirm whether the center of gravity is "editor companion" or "operator cockpit"
- Document friction points that only a standalone app can solve

### Phase 1 — VS Code incubation MVP
- Activity bar/tree view for hosts, groups, and saved workspaces
- Command palette actions for connect, open terminal, run macro, add to broadcast group
- Macro/snippet model with prompts/variables
- Host metadata, notes, environment coloring, and protected-host warnings
- Secret references using VS Code secret storage

### Phase 2 — Hard-feature validation
- Prove grouped multi-exec UX inside VS Code
- Prototype remote file actions and drag/drop-adjacent flows
- Decide whether integrated file transfer feels good enough in extension form
- Decide whether VS Code terminal APIs are sufficient for the desired control model

### Phase 3 — Standalone decision gate
- If extension UX is good enough, harden and expand the extension suite
- If extension UX feels boxed in, promote the validated model into the desktop app

### Standalone track, if needed
- Validate feature gap against Termius, Tabby, WezTerm, iTerm2, and Termora
- Decide whether the app should embed SSH directly or shell out to OpenSSH where practical
- Decide whether file transfer is a side panel or a first-class split mode
- Session library with folders/tags
- SSH connect/disconnect and tabbed sessions
- Broadcast groups with obvious visual warning state
- Snippets/macros with variable prompts
- Basic local persistence via SQLite
- SFTP browser
- Drag/drop upload and download
- Credential storage via OS keychain/libsecret
- Import from `~/.ssh/config`
- Environment badges and danger coloring
- Protected-host confirmation rules
- Session restore / saved workspaces
- Port forwarding UI

## Opinionated Product Bets

- The project should win on **workflow density**, not protocol count.
- The killer feature is not "supports SSH"; it is "lets me work across 8 boxes with confidence."
- Cross-platform matters more than perfect macOS-native aesthetics.
- Local-first and self-owned state are better aligned with the intended use case than SaaS sync.
- Broadcast/multi-exec safety UX should be treated as a flagship feature, not a checkbox.

## Protocol Strategy

The product should be designed around a generic connection-profile model, but only a subset of protocols should be first-class in the early versions.

### First-class in v1
- SSH
- SFTP / SCP
- Port forwarding
- Serial

These fit the same operator mental model and justify deep workflow support.

### Compatible / pass-through
- X11 forwarding
- SSH agent forwarding
- ProxyJump / jump hosts
- MOSH

These should be supported where they naturally fit the SSH workflow, but they should not dictate the architecture or become flagship subsystems.

### External-launch first
- RDP
- VNC

These matter, but they belong to a different interaction model. Early versions should be able to store them as connection profiles, tag them, and launch preferred external clients without owning full protocol/rendering stacks.

### Not a v1 priority
- Broad multi-protocol parity chasing
- Full native remote-desktop stack ownership
- X11 as a primary product pillar

### Guiding rule
- Be an **SSH-first operator workbench** with adjacent protocol awareness.
- Do not become a universal remote-client super app by accident.

## Open Questions

- Working name: keep `Remote Operator Workbench`, or rename once a sharper brand appears?
- Should the first release support only SSH/SFTP, or also serial from day one?
- Should Vaultwarden integration be first-party or deferred behind OS-keychain-first design?
- Should macros be plain text snippets first, or full expect-like interactive flows?
- Is a tree/sidebar model enough, or does the app want workspace presets as the primary abstraction?

## Immediate Next Steps

1. Decide whether to start with a VS Code extension repo or a framework-agnostic core repo.
2. Lock the initial protocol support policy:
   - first-class: SSH, SFTP/SCP, port forwarding, serial
   - pass-through: X11, agent forwarding, jump hosts, MOSH
   - external-launch: RDP, VNC
3. If choosing the extension route, build a tiny spike with:
   - host tree
   - command palette actions
   - secret storage
   - one webview-backed details pane
4. Build a clickable UX sketch for the main workspace:
   - left host tree
   - center terminal tabs
   - right file/macro/details pane
5. Write the data model for:
   - hosts
   - groups
   - credentials references
   - macros
   - workspaces
6. Decide the connection backend approach:
   - native SSH library
   - OpenSSH subprocess orchestration
   - hybrid
7. Prototype the two hardest interactions early:
   - safe multi-exec
   - drag/drop file transfer

## Reference Links

- MobaXterm features: https://mobaxterm.mobatek.net/features.html
- MobaXterm documentation: https://mobaxterm.mobatek.net/documentation.html
- iTerm2 shell integration: https://iterm2.com/documentation-shell-integration.html
- iTerm2 automatic profile switching: https://iterm2.com/documentation-automatic-profile-switching.html
- iTerm2 broadcast input: https://iterm2.com/documentation-menu-items.html
- WezTerm features: https://wezterm.org/features.html
- WezTerm SSH: https://wezterm.org/ssh.html
- WezTerm multiplexing / SSH domains: https://wezterm.org/multiplexing.html
- Tabby: https://github.com/Eugeny/tabby
- Termius vault / credentials: https://termius.com/documentation/secure-credentials-sync
- Termius SFTP: https://termius.com/documentation/connect-with-sftp
- Termora: https://github.com/TermoraDev/termora
- Electerm: https://github.com/electerm/electerm
