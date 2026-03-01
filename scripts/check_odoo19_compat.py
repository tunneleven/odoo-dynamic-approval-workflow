#!/usr/bin/env python3
"""Fail on known Odoo 19-incompatible XML patterns."""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _is_under_docs(path: Path) -> bool:
    return "docs" in path.parts


def _scan_xml(path: Path) -> list[str]:
    violations: list[str] = []
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return [f"{path}: XML parse error: {exc}"]

    root = tree.getroot()

    for record in root.iter("record"):
        record_id = record.get("id", "<no-id>")
        model = record.get("model")

        if model == "res.groups":
            if record.findall("./field[@name='category_id']"):
                violations.append(
                    f"{path}: record '{record_id}' (res.groups) uses forbidden field "
                    "'category_id'; use privilege_id in Odoo 19."
                )

        if model == "ir.cron":
            if record.findall("./field[@name='numbercall']"):
                violations.append(
                    f"{path}: record '{record_id}' (ir.cron) uses removed field "
                    "'numbercall' in Odoo 19."
                )

        if model == "ir.ui.view":
            for arch_field in record.findall("./field[@name='arch']"):
                for search_node in arch_field.iter("search"):
                    for group_node in search_node.iter("group"):
                        if "expand" in group_node.attrib:
                            violations.append(
                                f"{path}: view '{record_id}' search/group uses removed "
                                "attribute 'expand' in Odoo 19."
                            )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("dynamic_approval_workflow"),
        help="Root folder to scan for addon XML files.",
    )
    args = parser.parse_args()

    root = args.root
    if not root.exists():
        print(f"Root path does not exist: {root}", file=sys.stderr)
        return 2

    xml_files = sorted(path for path in root.rglob("*.xml") if not _is_under_docs(path))
    violations: list[str] = []
    for xml_file in xml_files:
        violations.extend(_scan_xml(xml_file))

    if violations:
        print("Odoo 19 compatibility check failed:")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print(f"Odoo 19 compatibility check passed ({len(xml_files)} XML files scanned).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
