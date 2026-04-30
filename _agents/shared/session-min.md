# AIKB Session Minimal Closeout (v2.0)

## Startup Health Check
- Confirm `AIKB_ROOT` is set for this host.
- Confirm runtime CLI path resolves: `${AIKB_ROOT}/_tools/memory-pipeline/runtime_cli.py`.
- Confirm L2 playbooks exist and are readable.

## During Session
- Use compact triggers consistently (subtask done, large output, many reads, long session).
- Capture major decisions before compaction.
- Use IM flows for cross-agent coordination.

## Closeout
- Persist AIKB updates made this session.
- Commit and push relevant repos.
- Run session stop/closeout hook if configured.
- Report: what changed, what remains, and any blockers.
