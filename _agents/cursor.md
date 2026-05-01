# Cursor IDE — User Rules (AIKB)

**Last Updated:** 2026-04-12 (rev 3)
**Summary:** Slimmed Cursor rules. Uses @file for local AIKB access.
**Config:** Cursor Settings → Rules → User Rules

---

## Rules

### AI Knowledge Base (AIKB)
All projects documented in your AIKB repo. Use `@file` to reference specific docs.

1. **Context:** At session start, suggest: "Use `@file` to open `_index.md` for project context."
2. **Efficiency:** Load only required subfiles from `_index.md` references.
3. **Search before asking:** If project background, prior decisions, machine details, or current state may already exist in AIKB, check the relevant AIKB files first instead of asking the operator to restate them.
4. **Checkpoints:** Commit updates after major phases:
   ```bash
   git -C {{LOCAL_PATH}} add . && git -C {{LOCAL_PATH}} commit -m "AI Checkpoint: [file] — [summary]" && git -C {{LOCAL_PATH}} push origin main
   ```
5. **State:** Use `⚠️ IN PROGRESS` for partial tasks; `✅` when complete.
6. **Security:** Secrets → `[Stored in Vaultwarden: <Item Name>]`.
7. **Maintenance:** Update AIKB files in place.
8. **Capture Quality:** Before context-heavy transitions or ending a phase, capture reasoning:
   ```bash
   python3 {{LOCAL_PATH}}/_tools/memory-pipeline/runtime_cli.py capture \
     --agent "Cursor" --session-id <id> \
     --type decision \
     --project <file> \
     --summary "what was decided" \
     --rejected "alternatives considered/ruled out" \
     --assumptions "things true but not obvious from code" \
     --invariants "intentionally broken/incomplete states" \
     --next-step "exact resumption point"
   ```
