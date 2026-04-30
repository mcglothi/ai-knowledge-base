#!/usr/bin/env bash
set -euo pipefail

# AIKB v2 instruction trial runner
# Usage:
#   bash _tools/validation/run_v2_trial.sh [agent]
# Example:
#   bash _tools/validation/run_v2_trial.sh claude-code

AGENT="${1:-claude-code}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

export AIKB_ROOT="${AIKB_ROOT:-$ROOT}"

echo "[v2-trial] AIKB_ROOT=$AIKB_ROOT"
echo "[v2-trial] Agent=$AGENT"

# 1) Structural readiness check
python3 "$ROOT/_tools/validation/check_v2_instruction_readiness.py"

# 2) Agent overlay existence
OVERLAY="$ROOT/_agents/v2/${AGENT}.overlay.md"
if [[ ! -f "$OVERLAY" ]]; then
  echo "[v2-trial] ERROR: Missing overlay $OVERLAY"
  echo "[v2-trial] Available overlays:"
  ls -1 "$ROOT/_agents/v2" || true
  exit 2
fi

echo "[v2-trial] Using overlay: $OVERLAY"
DISPATCH="$ROOT/_agents/v2/dispatch.yaml"
[[ -r "$DISPATCH" ]] || { echo "[v2-trial] ERROR: missing dispatch registry $DISPATCH"; exit 4; }
echo "[v2-trial] Using dispatch: $DISPATCH"

# 3) Playbook reachability check
for f in \
  "$ROOT/docs/playbooks/im.md" \
  "$ROOT/docs/playbooks/token-economy.md" \
  "$ROOT/docs/playbooks/closeout.md" \
  "$ROOT/docs/playbooks/git-checkpointing.md" \
  "$ROOT/docs/playbooks/cross-agent-mind-meld.md"
do
  [[ -r "$f" ]] || { echo "[v2-trial] ERROR: unreadable $f"; exit 3; }
  echo "[v2-trial] OK playbook: ${f#$ROOT/}"
done

# 4) Emit session bootstrap packet path hints
cat <<BOOT

[v2-trial] READY

Bootstrap packet for trial session:
1) Load: _agents/shared/core-min.md
2) Load: _agents/v2/${AGENT}.overlay.md
3) Keep on deck: _agents/shared/session-min.md
4) Load L2 on demand via dispatch registry + table:
   - IM: docs/playbooks/im.md
   - Token economy: docs/playbooks/token-economy.md
   - Closeout: docs/playbooks/closeout.md
   - Git checkpointing: docs/playbooks/git-checkpointing.md
   - Cross-agent: docs/playbooks/cross-agent-mind-meld.md

Pilot logging file:
- _runtime/scratchpads/agent-instructions-v2-ab-pilot-checklist-2026-04-29.md
BOOT
