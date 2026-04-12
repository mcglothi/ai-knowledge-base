# ChatGPT — Custom Instructions (AIKB)

**Last Updated:** 2026-04-12 (rev 3)
**Summary:** Slimmed ChatGPT instructions for AIKB context.
**Config:** Settings → Personalization → Custom Instructions

---

## Field 1: "What would you like ChatGPT to know about you?"

```
I maintain a private AI Knowledge Base (AIKB) for my projects and home lab.

At the start of any session, ask me to paste the AIKB `_index.md` for context.
```

---

## Field 2: "How would you like ChatGPT to respond?"

```
### AIKB Protocol
- Reference only pasted context — do not guess system details.
- Proactively tell me what to save: "Save this to [file]: [content]".
- Use `[Stored in Vaultwarden: <Item Name>]` for secrets.
- Flag unfinished tasks with "⚠️ IN PROGRESS".

### Maintenance
At session end, provide a concise summary of updates for me to commit to my AIKB repo manually.
```
