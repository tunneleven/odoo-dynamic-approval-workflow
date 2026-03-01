#!/usr/bin/env bash
set -euo pipefail

REPO=""
AGENT="codex"
ASSIGNEE=""
WATCH_SECONDS=0
LIMIT=10

usage() {
  cat <<'EOF'
Usage: monitor_agent_queue.sh [options]

Options:
  --repo <owner/name>     GitHub repo (default: current gh repo)
  --agent <name>          Agent queue label without prefix (default: codex)
  --assignee <login>      Assignee login (default: current gh login)
  --watch <seconds>       Refresh interval; 0 means one-shot (default: 0)
  --limit <n>             Max issues shown per section (default: 10)
  -h, --help              Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO="$2"
      shift 2
      ;;
    --agent)
      AGENT="$2"
      shift 2
      ;;
    --assignee)
      ASSIGNEE="$2"
      shift 2
      ;;
    --watch)
      WATCH_SECONDS="$2"
      shift 2
      ;;
    --limit)
      LIMIT="$2"
      shift 2
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

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not found in PATH." >&2
  exit 2
fi

if [[ -z "$REPO" ]]; then
  REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
fi

if [[ -z "$ASSIGNEE" ]]; then
  ASSIGNEE="$(gh api user --jq '.login')"
fi

count_issues() {
  gh issue list \
    --repo "$REPO" \
    --state open \
    "$@" \
    --json number \
    --jq 'length'
}

print_section() {
  local title="$1"
  shift
  echo
  echo "[$title]"
  gh issue list --repo "$REPO" --state open "$@" --limit "$LIMIT" \
    --json number,title,assignees,labels,url \
    --template '{{range .}}#{{.number}} {{.title}} {{if .assignees}}[{{range .assignees}}{{.login}} {{end}}]{{end}}{{"\n"}}{{.url}}{{"\n\n"}}{{end}}' || true
}

print_runs() {
  local workflow="$1"
  echo
  echo "[Workflow: $workflow]"
  if ! gh run list \
    --repo "$REPO" \
    --workflow "$workflow" \
    --limit 5 \
    --json databaseId,status,conclusion,createdAt,displayTitle,url \
    --template '{{range .}}#{{.databaseId}} {{.status}}/{{.conclusion}} {{.createdAt}} {{.displayTitle}}{{"\n"}}{{.url}}{{"\n\n"}}{{end}}' 2>/dev/null; then
    echo "Workflow not found or no access yet."
  fi
}

print_worker_process() {
  echo
  echo "[Local worker process]"
  local matches
  matches="$(pgrep -af "agent_queue_worker.py.*--agent $AGENT" || true)"
  if [[ -z "$matches" ]]; then
    echo "No local worker process matched agent '$AGENT'."
  else
    echo "$matches"
  fi
}

render() {
  echo "============================================================"
  echo "Agent Queue Monitor"
  echo "Timestamp: $(date -Iseconds)"
  echo "Repo: $REPO"
  echo "Agent: $AGENT"
  echo "Assignee: $ASSIGNEE"
  echo "============================================================"

  local ready_agent ready_either in_progress_assignee review_fix_assignee
  ready_agent="$(count_issues --label "status:todo" --label "state:ready" --label "agent:$AGENT")"
  ready_either="$(count_issues --label "status:todo" --label "state:ready" --label "agent:either")"
  in_progress_assignee="$(count_issues --label "status:in-progress" --assignee "$ASSIGNEE")"
  review_fix_assignee="$(count_issues --label "status:in-progress" --label "needs:review-fix" --assignee "$ASSIGNEE")"

  echo "Queue Summary:"
  echo "- Ready for agent:$AGENT: $ready_agent"
  echo "- Ready for agent:either: $ready_either"
  echo "- In progress assigned to $ASSIGNEE: $in_progress_assignee"
  echo "- Review-fix assigned to $ASSIGNEE: $review_fix_assignee"

  print_worker_process
  print_section "Ready (agent:$AGENT)" --label "status:todo" --label "state:ready" --label "agent:$AGENT"
  print_section "Ready (agent:either)" --label "status:todo" --label "state:ready" --label "agent:either"
  print_section "In-progress ($ASSIGNEE)" --label "status:in-progress" --assignee "$ASSIGNEE"
  print_section "Review fix ($ASSIGNEE)" --label "status:in-progress" --label "needs:review-fix" --assignee "$ASSIGNEE"
  print_runs "Agent Auto Pick"
  print_runs "Copilot Review Loop"
}

if [[ "$WATCH_SECONDS" -gt 0 ]]; then
  while true; do
    clear
    render
    sleep "$WATCH_SECONDS"
  done
else
  render
fi
