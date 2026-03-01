#!/usr/bin/env python3
"""Create GitHub issues from exported ITM task JSON via gh CLI.

Default mode is dry-run. Use --apply to execute.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path


def _phase_to_milestone(phase_value: int | str) -> str:
    value = str(phase_value)
    mapping = {
        "1": "Phase 1: Core Models + Security",
        "2": "Phase 2: Binding + Enforcement",
        "3": "Phase 3: BPMN + Runtime",
        "4": "Phase 4: Approver + Tasks + Signature",
        "5": "Phase 5: Access + Notifications + Webhooks",
        "6": "Phase 6: Ops + Contracts + Tests",
    }
    return mapping.get(value, f"Phase {value}")


def _normalize_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _build_body(task: dict) -> str:
    lines = []
    lines.append(f"Task ID: `{task.get('task_id', 'UNKNOWN')}`")
    lines.append("")
    lines.append("## Objective")
    lines.append(task.get("title", ""))
    lines.append("")

    depends_on = _normalize_list(task.get("depends_on"))
    lines.append("## Dependencies")
    if depends_on:
        for dep in depends_on:
            lines.append(f"- [ ] {dep}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Acceptance Criteria")
    for item in _normalize_list(task.get("acceptance_criteria")):
        lines.append(f"- [ ] {item}")
    lines.append("")

    lines.append("## Files")
    lines.append("Create:")
    for item in _normalize_list(task.get("files_to_create")):
        lines.append(f"- `{item}`")
    lines.append("Modify:")
    for item in _normalize_list(task.get("files_to_modify")):
        lines.append(f"- `{item}`")
    lines.append("")

    lines.append("## Verification")
    lines.append("```bash")
    lines.append(str(task.get("verification_command", "")).strip())
    lines.append("```")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--in",
        dest="in_file",
        type=Path,
        default=Path("dynamic_approval_workflow/docs/design/itm_tasks.json"),
        help="Exported ITM task JSON path.",
    )
    parser.add_argument("--repo", required=True, help="GitHub repo in owner/name format.")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of created issues (0 = all).")
    parser.add_argument("--apply", action="store_true", help="Execute gh issue create commands.")
    args = parser.parse_args()

    if not args.in_file.exists():
        print(f"Task JSON not found: {args.in_file}", file=sys.stderr)
        return 2

    tasks = json.loads(args.in_file.read_text(encoding="utf-8"))
    if args.limit > 0:
        tasks = tasks[: args.limit]

    for task in tasks:
        title = task.get("issue_title", task.get("title", "Untitled task"))
        labels = set(_normalize_list(task.get("labels")))
        labels.update({"type:task", "needs-triage", "status:todo"})

        agent = str(task.get("agent", "either")).strip().lower()
        labels.add(f"agent:{agent}")

        milestone = _phase_to_milestone(task.get("phase", ""))
        body = _build_body(task)

        cmd = [
            "gh",
            "issue",
            "create",
            "--repo",
            args.repo,
            "--title",
            title,
            "--body",
            body,
            "--milestone",
            milestone,
        ]
        for label in sorted(labels):
            cmd.extend(["--label", label])

        if args.apply:
            subprocess.run(cmd, check=True)
            print(f"Created issue: {title}")
        else:
            print("DRY-RUN:", shlex.join(cmd))

    if not args.apply:
        print("\nDry-run complete. Re-run with --apply to create issues.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
