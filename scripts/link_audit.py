#!/usr/bin/env python3
"""Fast link-graph preflight and conductivity metrics for ONTOS.RENT."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
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

    children: dict[str, list[str]] = defaultdict(list)
    for page in pages.values():
        if page.parent:
            if page.parent not in pages:
                errors.append(f"{page.slug}: missing parent {page.parent}")
            else:
                children[page.parent].append(page.slug)

    outgoing: dict[str, list[str]] = {}
    inbound: Counter[str] = Counter()
    duplicate_route_count = 0
    self_link_count = 0

    for page in pages.values():
        targets: list[str] = []
        seen: set[str] = set()
        for item in page.links:
            href = core.normal_href(item.get("href", ""))
            if not href:
                continue
            raw_slug = core.url_slug(href)
            slug = aliases.get(raw_slug, raw_slug)
            if slug not in pages:
                errors.append(f"{page.slug}: missing linked subject {href}")
                continue
            if slug == page.slug:
                self_link_count += 1
            if slug in seen:
                duplicate_route_count += 1
                continue
            seen.add(slug)
            targets.append(slug)
            inbound[slug] += 1
        outgoing[page.slug] = targets

    unique_errors = list(dict.fromkeys(errors))
    subjects = len(pages)
    link_edges = sum(len(v) for v in outgoing.values())
    pages_with_links = sum(bool(v) for v in outgoing.values())
    pages_without_links = subjects - pages_with_links

    leaf_slugs = sorted(slug for slug in pages if not children.get(slug))
    thin_leaf_slugs = sorted(slug for slug in leaf_slugs if not outgoing.get(slug))
    no_lateral_inbound_slugs = sorted(slug for slug in pages if inbound[slug] == 0)

    model_slugs = sorted(slug for slug in pages if slug.endswith("-v-arendu"))
    model_with_links = [slug for slug in model_slugs if outgoing.get(slug)]
    model_thin_leaves = [slug for slug in model_slugs if slug in set(thin_leaf_slugs)]

    root_slugs = sorted(slug for slug, page in pages.items() if not page.parent)

    def pct(n: int, d: int) -> float:
        return round((100.0 * n / d), 2) if d else 0.0

    return {
        "subjects": subjects,
        "errors": unique_errors,
        "error_count": len(unique_errors),
        "link_edges": link_edges,
        "pages_with_links": pages_with_links,
        "pages_without_links": pages_without_links,
        "lateral_coverage_pct": pct(pages_with_links, subjects),
        "parent_edges": sum(1 for page in pages.values() if page.parent),
        "parents_with_children": len(children),
        "leaf_pages": len(leaf_slugs),
        "thin_leaf_pages": len(thin_leaf_slugs),
        "thin_leaf_pct": pct(len(thin_leaf_slugs), subjects),
        "pages_without_lateral_inbound": len(no_lateral_inbound_slugs),
        "model_pages": len(model_slugs),
        "model_pages_with_links": len(model_with_links),
        "model_lateral_coverage_pct": pct(len(model_with_links), len(model_slugs)),
        "model_thin_leaves": len(model_thin_leaves),
        "root_pages": len(root_slugs),
        "duplicate_route_count": duplicate_route_count,
        "self_link_count": self_link_count,
        "details": {
            "root_slugs": root_slugs,
            "thin_leaf_slugs": thin_leaf_slugs,
            "model_thin_leaf_slugs": model_thin_leaves,
            "pages_without_lateral_inbound_slugs": no_lateral_inbound_slugs,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=core.ROOT)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    report = audit(args.root)

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    summary = {k: v for k, v in report.items() if k != "details"}
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
