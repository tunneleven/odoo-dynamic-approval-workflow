#!/usr/bin/env python3
"""Lightweight parser for ITM markdown YAML blocks.

This avoids external dependencies (e.g., PyYAML) in local/dev environments.
It supports the subset used by itm_dynamic_approval_workflow.md.
"""

from __future__ import annotations

import re
from pathlib import Path


def _strip_inline_comment(raw: str) -> str:
    """Strip YAML-style inline comments from scalar/list values."""
    value = raw
    if " #" in value:
        value = value.split(" #", 1)[0]
    return value.strip()


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _parse_scalar(value: str):
    val = _unquote(_strip_inline_comment(value))
    if val == "":
        return ""
    if val == "true":
        return True
    if val == "false":
        return False
    if re.fullmatch(r"-?\d+", val):
        return int(val)
    return val


def _split_inline_list(inner: str) -> list[str]:
    items = []
    current = []
    quote = None
    for char in inner:
        if quote is None and char in {"'", '"'}:
            quote = char
            current.append(char)
            continue
        if quote is not None and char == quote:
            quote = None
            current.append(char)
            continue
        if quote is None and char == ",":
            item = "".join(current).strip()
            if item:
                items.append(item)
            current = []
            continue
        current.append(char)
    if current:
        item = "".join(current).strip()
        if item:
            items.append(item)
    return [_unquote(_strip_inline_comment(item)) for item in items]


def _parse_inline_value(raw: str):
    value = _strip_inline_comment(raw)
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return _split_inline_list(inner)
    return _parse_scalar(value)


def parse_yaml_like_block(block: str) -> dict:
    data: dict = {}
    lines = block.splitlines()
    idx = 0

    while idx < len(lines):
        line = lines[idx]
        if not line.strip():
            idx += 1
            continue
        if line.startswith(" "):
            idx += 1
            continue

        match = re.match(r"^([A-Za-z_][\w]*):\s*(.*)$", line)
        if not match:
            idx += 1
            continue

        key = match.group(1)
        rest = match.group(2)

        if rest == "|":
            idx += 1
            buf = []
            while idx < len(lines):
                next_line = lines[idx]
                if next_line.startswith("  "):
                    buf.append(next_line[2:])
                    idx += 1
                    continue
                if not next_line.strip():
                    buf.append("")
                    idx += 1
                    continue
                break
            data[key] = "\n".join(buf).rstrip("\n")
            continue

        if rest == "":
            idx += 1
            items = []
            while idx < len(lines):
                next_line = lines[idx]
                if next_line.startswith("  - "):
                    items.append(_parse_inline_value(next_line[4:]))
                    idx += 1
                    continue
                if not next_line.strip():
                    idx += 1
                    continue
                break
            data[key] = items
            continue

        data[key] = _parse_inline_value(rest)
        idx += 1

    return data


def parse_itm(path: Path) -> list[dict]:
    content = path.read_text(encoding="utf-8")
    blocks = re.findall(r"```yaml\n(.*?)\n```", content, flags=re.DOTALL)
    tasks: list[dict] = []
    for block in blocks:
        payload = parse_yaml_like_block(block)
        if isinstance(payload, dict) and payload.get("task_id") and payload.get("title"):
            tasks.append(payload)
    return tasks
