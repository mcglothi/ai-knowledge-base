#!/usr/bin/env bash
set -euo pipefail

# Installs a systemd shutdown hook for fast AIKB finalize tasks.

if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemd not available on this host." >&2
  exit 1
fi

ROOT="${AIKB_ROOT:-$HOME/code/AIKB}"
if [[ ! -d "$ROOT/.git" ]]; then
  for p in "$HOME/Code/AIKB" "/home/mcglothi/code/AIKB" "/home/mcglothi/code/AIKB"; do
    if [[ -d "$p/.git" ]]; then
      ROOT="$p"
      break
    fi
  done
fi

SCRIPT="$ROOT/_tools/memory-pipeline/shutdown_finalize.sh"
if [[ ! -f "$SCRIPT" ]]; then
  echo "Missing script: $SCRIPT" >&2
  exit 1
fi

SERVICE_USER="${SUDO_USER:-$USER}"
SERVICE_HOME="$(eval echo "~$SERVICE_USER")"
if [[ -z "$SERVICE_HOME" || ! -d "$SERVICE_HOME" ]]; then
  echo "Could not resolve home directory for service user: $SERVICE_USER" >&2
  exit 1
fi

sudo install -m 0755 "$SCRIPT" /usr/local/sbin/aikb-shutdown-finalize.sh

cat <<EOF | sudo tee /etc/systemd/system/aikb-shutdown-finalize.service >/dev/null
[Unit]
Description=AIKB fast maintenance before shutdown
DefaultDependencies=no
Before=shutdown.target reboot.target halt.target

[Service]
Type=oneshot
User=$SERVICE_USER
Group=$SERVICE_USER
Environment=HOME=$SERVICE_HOME
ExecStart=/usr/local/sbin/aikb-shutdown-finalize.sh
TimeoutStartSec=25
RemainAfterExit=yes

[Install]
WantedBy=shutdown.target reboot.target halt.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable aikb-shutdown-finalize.service

echo "Installed systemd shutdown finalize service"
systemctl is-enabled aikb-shutdown-finalize.service
