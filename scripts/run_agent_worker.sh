#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required." >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

REPO="${REPO:-}"
AGENT="${AGENT:-codex}"
ASSIGNEE="${ASSIGNEE:-}"
POLL_SECONDS="${POLL_SECONDS:-90}"
MAX_TASKS_PER_CYCLE="${MAX_TASKS_PER_CYCLE:-1}"
INCLUDE_EITHER="${INCLUDE_EITHER:-1}"
START_COMMAND="${START_COMMAND:-}"
DRY_RUN="${DRY_RUN:-0}"

if [[ -z "$ASSIGNEE" ]]; then
  if command -v gh >/dev/null 2>&1; then
    ASSIGNEE="$(gh api user --jq '.login')"
  else
    echo "ASSIGNEE is not set and gh is not available to auto-detect it." >&2
    exit 2
  fi
fi

if [[ -z "$REPO" ]]; then
  if command -v gh >/dev/null 2>&1; then
    REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
  else
    echo "REPO is not set and gh is not available to auto-detect it." >&2
    exit 2
  fi
fi

ARGS=(
  "--repo" "$REPO"
  "--agent" "$AGENT"
  "--assignee" "$ASSIGNEE"
  "--poll-seconds" "$POLL_SECONDS"
  "--max-tasks-per-cycle" "$MAX_TASKS_PER_CYCLE"
)

if [[ "$INCLUDE_EITHER" == "1" ]]; then
  ARGS+=("--include-either")
fi

if [[ "$DRY_RUN" == "1" ]]; then
  ARGS+=("--dry-run")
fi

if [[ -n "$START_COMMAND" ]]; then
  ARGS+=("--start-command" "$START_COMMAND")
fi

exec python3 scripts/agent_queue_worker.py "${ARGS[@]}"
