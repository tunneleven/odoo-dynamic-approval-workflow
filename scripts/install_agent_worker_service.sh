#!/usr/bin/env bash
set -euo pipefail

ENABLE_NOW=0

usage() {
  cat <<'EOF'
Usage: install_agent_worker_service.sh [--enable-now]

Installs/updates a user-level systemd service:
  agent-queue-worker.service

The script also creates:
  ~/.config/daw/agent-worker.env

Options:
  --enable-now   Enable and start the service immediately.
  -h, --help     Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --enable-now)
      ENABLE_NOW=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemctl not found." >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICE_TEMPLATE="$REPO_ROOT/deploy/systemd/agent-queue-worker.service.template"
ENV_TEMPLATE="$REPO_ROOT/deploy/systemd/agent-worker.env.example"

if [[ ! -f "$SERVICE_TEMPLATE" ]]; then
  echo "Missing template: $SERVICE_TEMPLATE" >&2
  exit 2
fi

if [[ ! -f "$ENV_TEMPLATE" ]]; then
  echo "Missing template: $ENV_TEMPLATE" >&2
  exit 2
fi

SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
DAW_CONFIG_DIR="$HOME/.config/daw"
SERVICE_FILE="$SYSTEMD_USER_DIR/agent-queue-worker.service"
ENV_FILE="$DAW_CONFIG_DIR/agent-worker.env"

mkdir -p "$SYSTEMD_USER_DIR" "$DAW_CONFIG_DIR"

if [[ ! -f "$ENV_FILE" ]]; then
  cp "$ENV_TEMPLATE" "$ENV_FILE"
  echo "Created env file: $ENV_FILE"
else
  echo "Env file already exists: $ENV_FILE"
fi

sed "s|__REPO_ROOT__|$REPO_ROOT|g" "$SERVICE_TEMPLATE" > "$SERVICE_FILE"
echo "Installed service file: $SERVICE_FILE"

systemctl --user daemon-reload
echo "systemd user daemon reloaded."

if [[ "$ENABLE_NOW" == "1" ]]; then
  systemctl --user enable --now agent-queue-worker.service
  echo "Service enabled and started."
else
  echo "Service installed. Start manually with:"
  echo "  systemctl --user enable --now agent-queue-worker.service"
fi

echo
echo "Check service status:"
echo "  systemctl --user status agent-queue-worker.service"
echo
echo "Follow logs:"
echo "  journalctl --user -u agent-queue-worker.service -f"
