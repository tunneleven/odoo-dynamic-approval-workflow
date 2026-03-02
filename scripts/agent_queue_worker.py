#!/usr/bin/env python3
"""Auto-claim ready issues for an agent and start work commands.

This worker is intended to run on a developer host or self-hosted runner where:
- `gh` is authenticated
- the repository is cloned
- a non-interactive task command is available (optional)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass

TASK_ID_RE = re.compile(r"TASK-P\d+-\d+[A-Za-z]?")


class WorkerError(RuntimeError):
    """Raised when the worker cannot continue safely."""


@dataclass(frozen=True)
class WorkerConfig:
    repo: str
    agent: str
    assignee: str
    poll_seconds: int
    max_tasks_per_cycle: int
    include_either: bool
    start_command: str
    dry_run: bool
    once: bool

    @property
    def agent_label(self) -> str:
        return f"agent:{self.agent}"


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, text=True, capture_output=True)


def _gh(*args: str, check: bool = True) -> str:
    cmd = ["gh", *args]
    try:
        result = _run(cmd, check=check)
    except subprocess.CalledProcessError as exc:
        raise WorkerError(
            f"Command failed: {shlex.join(cmd)}\n"
            f"stdout:\n{exc.stdout}\n"
            f"stderr:\n{exc.stderr}"
        ) from exc
    return result.stdout


def _gh_json(*args: str) -> list[dict] | dict:
    output = _gh(*args)
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise WorkerError(f"Failed to parse JSON from gh output: {output}") from exc


def _resolve_repo() -> str:
    return _gh("repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner").strip()


def _resolve_login() -> str:
    return _gh("api", "user", "--jq", ".login").strip()


def _fetch_issues(repo: str, *, labels: str, assignee: str | None = None) -> list[dict]:
    args = [
        "api",
        "--method",
        "GET",
        f"repos/{repo}/issues",
        "-f",
        "state=open",
        "-f",
        "sort=created",
        "-f",
        "direction=asc",
        "-f",
        "per_page=100",
        "-f",
        f"labels={labels}",
    ]
    if assignee:
        args.extend(["-f", f"assignee={assignee}"])
    data = _gh_json(*args)
    if isinstance(data, list):
        return data
    return []


def _has_label(issue: dict, label_name: str) -> bool:
    return any(label.get("name") == label_name for label in issue.get("labels", []))


def _is_candidate(issue: dict) -> bool:
    if issue.get("pull_request"):
        return False
    if issue.get("assignees"):
        return False
    if _has_label(issue, "state:blocked"):
        return False
    return True


def _issue_task_id(issue: dict) -> str:
    body = issue.get("body") or ""
    match = TASK_ID_RE.search(body)
    return match.group(0) if match else "UNKNOWN"


def _issue_marker_exists(repo: str, issue_number: int, marker_prefix: str) -> bool:
    comments = _gh_json(
        "api",
        "--method",
        "GET",
        f"repos/{repo}/issues/{issue_number}/comments",
        "-f",
        "per_page=100",
    )
    if not isinstance(comments, list):
        return False
    for comment in comments:
        body = comment.get("body") or ""
        if marker_prefix in body:
            return True
    return False


def _comment_issue(repo: str, issue_number: int, body: str, dry_run: bool) -> None:
    cmd = ["gh", "issue", "comment", str(issue_number), "--repo", repo, "--body", body]
    if dry_run:
        print(f"DRY-RUN: {shlex.join(cmd)}")
        return
    _run(cmd, check=True)


def _assign_issue(repo: str, issue_number: int, assignee: str, dry_run: bool) -> None:
    cmd = [
        "gh",
        "issue",
        "edit",
        str(issue_number),
        "--repo",
        repo,
        "--add-assignee",
        assignee,
    ]
    if dry_run:
        print(f"DRY-RUN: {shlex.join(cmd)}")
        return
    _run(cmd, check=True)


def _format_start_command(template: str, repo: str, issue: dict, mode: str) -> str:
    title = (issue.get("title") or "").strip()
    issue_number = int(issue["number"])
    issue_url = issue.get("html_url") or ""
    task_id = _issue_task_id(issue)
    mapping = {
        "repo": repo,
        "agent_mode": mode,
        "issue_number": str(issue_number),
        "issue_title": title,
        "issue_url": issue_url,
        "task_id": task_id,
        "issue_number_sh": shlex.quote(str(issue_number)),
        "issue_title_sh": shlex.quote(title),
        "issue_url_sh": shlex.quote(issue_url),
        "task_id_sh": shlex.quote(task_id),
    }
    try:
        return template.format(**mapping)
    except KeyError as exc:
        raise WorkerError(f"Unknown placeholder in --start-command: {exc}") from exc


def _post_start_marker(config: WorkerConfig, issue: dict, mode: str, command: str) -> None:
    issue_number = int(issue["number"])
    marker = f"<!-- agent-worker:start:{config.assignee}:{mode} -->"
    if _issue_marker_exists(config.repo, issue_number, marker):
        return
    body = "\n".join(
        [
            marker,
            f"Worker picked this task for `{config.agent}` as `{config.assignee}`.",
            f"Mode: `{mode}`",
            f"Task: `{_issue_task_id(issue)}`",
            "Command:",
            "```bash",
            command,
            "```",
        ]
    )
    _comment_issue(config.repo, issue_number, body, config.dry_run)


def _post_finish_marker(
    config: WorkerConfig,
    issue: dict,
    mode: str,
    exit_code: int,
    duration_s: float,
) -> None:
    issue_number = int(issue["number"])
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    marker = f"<!-- agent-worker:finish:{config.assignee}:{mode}:{timestamp} -->"
    status = "success" if exit_code == 0 else "failed"
    body = "\n".join(
        [
            marker,
            f"Worker command `{status}` for `{config.agent}`.",
            f"Mode: `{mode}`",
            f"Exit code: `{exit_code}`",
            f"Duration: `{duration_s:.1f}s`",
        ]
    )
    _comment_issue(config.repo, issue_number, body, config.dry_run)


def _run_command(command: str, dry_run: bool) -> int:
    if dry_run:
        print(f"DRY-RUN command: {command}")
        return 0
    result = subprocess.run(command, shell=True, check=False)
    return int(result.returncode)


def _process_issue(config: WorkerConfig, issue: dict, mode: str) -> None:
    command = _format_start_command(config.start_command, config.repo, issue, mode)
    _post_start_marker(config, issue, mode, command)
    start = time.time()
    exit_code = _run_command(command, config.dry_run)
    _post_finish_marker(config, issue, mode, exit_code, time.time() - start)


def _claim_next_ready_issue(config: WorkerConfig) -> dict | None:
    label_queue = [config.agent_label]
    if config.include_either and config.agent != "either":
        label_queue.append("agent:either")

    for label in label_queue:
        labels = f"{label},status:todo,state:ready"
        issues = _fetch_issues(config.repo, labels=labels)
        for issue in issues:
            if not _is_candidate(issue):
                continue
            issue_number = int(issue["number"])
            marker = f"<!-- agent-worker:claim:{config.assignee} -->"
            if _issue_marker_exists(config.repo, issue_number, marker):
                continue
            _assign_issue(config.repo, issue_number, config.assignee, config.dry_run)
            claim_note = "\n".join(
                [
                    marker,
                    f"Worker auto-claimed this task for `{config.agent}` as `{config.assignee}`.",
                    f"Routing label: `{label}`",
                ]
            )
            _comment_issue(config.repo, issue_number, claim_note, config.dry_run)
            return issue
    return None


def _assigned_review_fix_issues(config: WorkerConfig) -> list[dict]:
    labels = "status:in-progress,needs:review-fix"
    issues = _fetch_issues(config.repo, labels=labels, assignee=config.assignee)
    candidates: list[dict] = []
    for issue in issues:
        if issue.get("pull_request"):
            continue
        if _has_label(issue, config.agent_label) or _has_label(issue, "agent:either"):
            candidates.append(issue)
    return candidates


def _run_cycle(config: WorkerConfig) -> int:
    processed = 0
    if not config.start_command:
        print(
            "No --start-command configured. Worker will only auto-claim issues.",
            file=sys.stderr,
        )

    for issue in _assigned_review_fix_issues(config):
        if processed >= config.max_tasks_per_cycle:
            break
        if config.start_command:
            _process_issue(config, issue, mode="review-fix")
            processed += 1

    while processed < config.max_tasks_per_cycle:
        issue = _claim_next_ready_issue(config)
        if not issue:
            break
        if config.start_command:
            _process_issue(config, issue, mode="new-task")
        processed += 1
    return processed


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="GitHub repo in owner/name format.")
    parser.add_argument(
        "--agent",
        default="codex",
        choices=["codex", "copilot", "antigravity", "either"],
        help="Agent queue label to consume.",
    )
    parser.add_argument("--assignee", help="GitHub username used to claim issues.")
    parser.add_argument("--poll-seconds", type=int, default=120, help="Polling interval.")
    parser.add_argument(
        "--max-tasks-per-cycle",
        type=int,
        default=1,
        help="Max issues processed in one poll cycle.",
    )
    parser.add_argument(
        "--include-either",
        action="store_true",
        help="Also claim `agent:either` tasks.",
    )
    parser.add_argument(
        "--start-command",
        default="",
        help=(
            "Shell command template to start work. Placeholders: {repo}, {agent_mode}, "
            "{issue_number}, {issue_title}, {issue_url}, {task_id} and *_sh variants."
        ),
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions only.")
    parser.add_argument("--once", action="store_true", help="Run one cycle then exit.")
    return parser.parse_args()


def _build_config(args: argparse.Namespace) -> WorkerConfig:
    if shutil.which("gh") is None:
        raise WorkerError("`gh` CLI is required but not found in PATH.")

    repo = args.repo or _resolve_repo()
    assignee = args.assignee or _resolve_login()
    start_command = args.start_command or ""

    return WorkerConfig(
        repo=repo,
        agent=args.agent,
        assignee=assignee,
        poll_seconds=max(args.poll_seconds, 10),
        max_tasks_per_cycle=max(args.max_tasks_per_cycle, 1),
        include_either=bool(args.include_either),
        start_command=start_command.strip(),
        dry_run=bool(args.dry_run),
        once=bool(args.once),
    )


def main() -> int:
    args = _parse_args()
    config = _build_config(args)

    print(
        f"Worker started for repo={config.repo} agent={config.agent} assignee={config.assignee}",
        file=sys.stderr,
    )

    while True:
        try:
            processed = _run_cycle(config)
            print(f"Cycle complete. Processed: {processed}", file=sys.stderr)
        except WorkerError as exc:
            print(f"Worker error: {exc}", file=sys.stderr)
            return 2

        if config.once:
            return 0
        time.sleep(config.poll_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
