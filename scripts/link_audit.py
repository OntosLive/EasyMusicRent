#!/usr/bin/env python3
"""Fast preflight for parent/link targets without mutating the canonical compiler."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import site_core as core


def audit(root: Path) -> dict:
    metadata = core.read_json(root / "content/legacy-metadata.json", {})
    aliases = core.read_json(root / "content/aliases.json", {})
    pages = core.read_legacy(root, metadata)
    core.merge_records(root, pages)
    core.merge_legacy_navigation(root, pages)

    errors: list[str] = []

    for alias, target in aliases.items():
        if target not in pages:
            errors.append(f"alias {alias}: missing target {target}")
        pages.pop(alias, None)

    for page in pages.values():
        if page.parent and page.parent not in pages:
            errors.append(f"{page.slug}: missing parent {page.parent}")
        for item in page.links:
            href = core.normal_href(item.get("href", ""))
            if not href:
                continue
            raw_slug = core.url_slug(href)
            slug = aliases.get(raw_slug, raw_slug)
            if slug not in pages:
                errors.append(f"{page.slug}: missing linked subject {href}")

    unique_errors = list(dict.fromkeys(errors))
    return {
        "subjects": len(pages),
        "errors": unique_errors,
        "error_count": len(unique_errors),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=core.ROOT)
    args = parser.parse_args()

    report = audit(args.root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
