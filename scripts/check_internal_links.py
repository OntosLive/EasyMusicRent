#!/usr/bin/env python3
"""Report all broken authored parent/link references before the full site build."""
from __future__ import annotations

from site_core import (
    ROOT, merge_legacy_navigation, merge_records, normal_href,
    read_json, read_legacy, url_slug,
)


def main() -> int:
    metadata = read_json(ROOT / "content" / "legacy-metadata.json", {})
    aliases = read_json(ROOT / "content" / "aliases.json", {})
    pages = read_legacy(ROOT, metadata)
    merge_records(ROOT, pages)
    merge_legacy_navigation(ROOT, pages)

    errors: list[str] = []

    for alias, target in aliases.items():
        if target not in pages:
            errors.append(f"alias {alias}: missing target {target}")
        pages.pop(alias, None)

    for page in pages.values():
        if page.parent and page.parent not in pages:
            errors.append(f"{page.slug}: missing parent {page.parent}")

        for item in page.links:
            href = normal_href(item.get("href", ""))
            if not href:
                continue
            raw_slug = url_slug(href)
            slug = aliases.get(raw_slug, raw_slug)
            if slug not in pages:
                errors.append(f"{page.slug}: missing linked subject {href}")

    if errors:
        for error in sorted(set(errors)):
            print(error)
        print(f"broken_reference_count={len(set(errors))}")
        return 1

    print(f"subjects={len(pages)}")
    print("broken_reference_count=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
