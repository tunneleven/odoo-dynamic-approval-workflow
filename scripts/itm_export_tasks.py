#!/usr/bin/env python3
"""Export ITM markdown task blocks into machine-readable task JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from itm_parser import parse_itm


def _task_sort_key(task_id: str) -> tuple[int, int]:
    match = re.match(r"^TASK-P(\d+)-(\d+[a-zA-Z]?)$", task_id)
    if not match:
        return (999, 999)
    phase = int(match.group(1))
    tail = match.group(2)
    digits = int(re.match(r"(\d+)", tail).group(1))
    return (phase, digits)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--itm",
        type=Path,
        default=Path("dynamic_approval_workflow/docs/design/itm_dynamic_approval_workflow.md"),
        help="Path to ITM markdown file.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("dynamic_approval_workflow/docs/design/itm_tasks.json"),
        help="Output JSON path.",
    )
    args = parser.parse_args()

    if not args.itm.exists():
        print(f"ITM file not found: {args.itm}", file=sys.stderr)
        return 2

    tasks = parse_itm(args.itm)
    for task in tasks:
        task_id = task.get("task_id")
        title = task.get("title")
        task["issue_title"] = f"[{task_id}] {title}"
    tasks.sort(key=lambda item: _task_sort_key(item["task_id"]))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(tasks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Exported {len(tasks)} tasks to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
