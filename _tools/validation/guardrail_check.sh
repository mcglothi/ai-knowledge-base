#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

echo "[guardrail] scanning staged + working-tree text for obvious secret patterns"
PAT='(AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY|xox[baprs]-|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z\-_]{35}|password\s*=\s*"[^"]+")'
HITS=$(git diff -- . ':(exclude)_runtime/**' | grep -E "$PAT" -n || true)
if [[ -n "$HITS" ]]; then
  echo "[guardrail] FAIL: potential secret patterns found"
  echo "$HITS" | head -40
  exit 2
fi

echo "[guardrail] checking forbidden bitwarden command patterns in docs/scripts"
FW=$(grep -RInE 'bw (unlock|status)( |$)' _agents docs _tools 2>/dev/null | grep -v -- '--session' || true)
if [[ -n "$FW" ]]; then
  echo "[guardrail] WARN: found bw unlock/status without explicit --session reference"
  echo "$FW" | head -40
fi

echo "[guardrail] PASS"
