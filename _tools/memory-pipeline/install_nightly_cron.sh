#!/usr/bin/env bash
set -euo pipefail

# Idempotently installs nightly + @reboot cron jobs for AIKB maintenance.

SCHEDULE_MINUTE="${SCHEDULE_MINUTE:-15}"
SCHEDULE_HOUR="${SCHEDULE_HOUR:-2}"

if [[ -n "${AIKB_ROOT:-}" ]]; then
  ROOT="$AIKB_ROOT"
else
  for p in "$HOME/code/AIKB" "$HOME/Code/AIKB" "/home/svc_ansible/AIKB" "/home/mcglothi/AIKB"; do
    if [[ -d "$p/.git" ]]; then
      ROOT="$p"
      break
    fi
  done
fi

if [[ -z "${ROOT:-}" ]]; then
  echo "Could not locate AIKB root. Set AIKB_ROOT=/path/to/AIKB and retry." >&2
  exit 1
fi

PY_BIN="${PY_BIN:-$(command -v python3)}"
if [[ -z "$PY_BIN" ]]; then
  echo "python3 not found in PATH." >&2
  exit 1
fi

LOG_DIR="$ROOT/_runtime/maintenance"
mkdir -p "$LOG_DIR"

MARKER_NIGHTLY="# AIKB_NIGHTLY_MAINTENANCE"
MARKER_REBOOT="# AIKB_BOOT_CATCHUP"
CMD_NIGHTLY="cd $ROOT && $PY_BIN $ROOT/_tools/memory-pipeline/nightly_maintenance.py --run-search-eval >> $LOG_DIR/cron-nightly.log 2>&1"
CMD_REBOOT="cd $ROOT && $PY_BIN $ROOT/_tools/memory-pipeline/nightly_maintenance.py >> $LOG_DIR/cron-reboot.log 2>&1"
ENTRY_NIGHTLY="$SCHEDULE_MINUTE $SCHEDULE_HOUR * * * $CMD_NIGHTLY $MARKER_NIGHTLY"
ENTRY_REBOOT="@reboot $CMD_REBOOT $MARKER_REBOOT"

TMP="$(mktemp)"
(crontab -l 2>/dev/null || true) | sed '/AIKB_NIGHTLY_MAINTENANCE/d;/AIKB_BOOT_CATCHUP/d' > "$TMP"
printf '%s\n' "$ENTRY_NIGHTLY" >> "$TMP"
printf '%s\n' "$ENTRY_REBOOT" >> "$TMP"
crontab "$TMP"
rm -f "$TMP"

echo "Installed cron entries for AIKB maintenance"
echo "Host: $(hostname)"
echo "Schedule: ${SCHEDULE_HOUR}:${SCHEDULE_MINUTE} daily"
echo "Schedule: @reboot catch-up"
echo "Repo: $ROOT"
echo "Nightly command: $CMD_NIGHTLY"
echo "Reboot command : $CMD_REBOOT"
