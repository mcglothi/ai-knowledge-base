# ChatGPT — Agent Instructions

**Config:** Settings → Personalization → Custom Instructions
**Source of truth:** `{{LOCAL_PATH}}/_agents/chatgpt.md`

ChatGPT has a ~1,500 character limit per Custom Instructions field. This file contains two sections — one for each field.

---

## Field 1: "What would you like ChatGPT to know about you?"

Paste the content between the markers:

<!-- FIELD 1 START -->
I maintain a private GitHub knowledge base called AIKB at `{{GITHUB_USERNAME}}/{{REPO_NAME}}`. It contains my project notes, machine profiles, and work context. When I start a session about a specific project, I'll paste the relevant `_index.md` content. Use it to orient yourself without re-asking for context I've already written down.

My machines: see dev-environment notes I'll provide per session. Never assume a tool is installed without confirmation.

Credentials are in {{SECRETS_MANAGER}} — never store them in notes or outputs.
<!-- FIELD 1 END -->

---

## Field 2: "How would you like ChatGPT to respond?"

Paste the content between the markers:

<!-- FIELD 2 START -->
Be concise. When I share AIKB context, use it — don't ask questions I've already answered. Suggest AIKB updates when you learn something I'd want to remember. Format updates as ready-to-paste Markdown matching the file template. Never include credentials in outputs.
<!-- FIELD 2 END -->

---

## Using ChatGPT with AIKB (session workflow)

Since ChatGPT cannot read files directly, paste relevant context at the start of sessions:

1. Open the relevant project file from your AIKB clone
2. Paste the content into the chat with: "Here's my current context for [project]:"
3. ChatGPT can then provide suggested AIKB updates at the end of the session for you to paste back

This is less automated than file-based tools but still useful for capturing decisions and gotchas.
