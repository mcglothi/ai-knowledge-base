#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

echo "[guardrail] scanning staged + working-tree text for obvious secret patterns"
# NOTE: keep '-' last inside any bracket expression. A backslash is literal
# inside brackets, so '[...\-_]' parses as the collation range '\'..'_' and
# grep aborts with "invalid character range" in some locales. Paired with a
# bare '|| true' that turned grep's error into an empty result, this silently
# disabled the entire scan — so treat grep exit >1 as a hard failure.
PAT='(AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY|xox[baprs]-|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{35}|password\s*=\s*"[^"]+")'
DIFF=$(git diff -- . ':(exclude)_runtime/**')
HITS=$(printf '%s\n' "$DIFF" | grep -E "$PAT" -n) && GREP_RC=0 || GREP_RC=$?
if [[ $GREP_RC -gt 1 ]]; then
  echo "[guardrail] FAIL: secret-pattern scan could not run (grep exit $GREP_RC)"
  exit 2
fi
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
