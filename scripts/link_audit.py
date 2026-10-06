#!/usr/bin/env python3
"""Fast link-graph preflight and conductivity metrics for ONTOS.RENT."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import site_core as core


def link_definitions(root: Path) -> dict[tuple[str, str, str], list[str]]:
    """Index matching source definitions for diagnostics, not graph construction.

    Several definitions can match an effective link, including an earlier
    replaced definition. Only core's merged Page.links determines active routes.
    """
    definitions: dict[tuple[str, str, str], list[str]] = defaultdict(list)

    def add(slug: str, links: list[dict], location: str) -> None:
        for index, item in enumerate(links):
            key = (slug, item.get("href", ""), item.get("label", ""))
            definitions[key].append(f"{location}/{index}")

    for path in sorted((root / "content/sections").glob("*.json")):
        document = core.read_json(path, {})
        source = str(path.relative_to(root))
        for index, record in enumerate(document.get("pages", [])):
            # Enrichment updates copy, not links (see core.merge_records).
            if record.get("mode") != "enrich":
                add(record["slug"], record.get("links", []), f"{source}#/pages/{index}/links")
        for field in ("navigation_replace", "navigation"):
            for slug, links in document.get(field, {}).items():
                add(slug, links, f"{source}#/{field}/{slug}")
    for path in sorted(root.glob("*/karta/index.html")):
        slug = path.parent.parent.name
        document = core.soup(path.read_text(encoding="utf-8"))
        for index, anchor in enumerate(document.select(".fund-scenes a[href]")):
            label = core.text(anchor.select_one(".fund-scene-title")) or core.text(anchor)
            key = (slug, anchor["href"], label)
            definitions[key].append(
                f"{path.relative_to(root)}:.fund-scenes a[href] item {index + 1}"
            )
    return definitions


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
    duplicate_routes: list[dict] = []
    self_links: list[dict] = []
    definitions = link_definitions(root)

    def describe(page: core.Page, index: int, slug: str) -> dict:
        item = page.links[index]
        return {
            "source_slug": page.slug,
            "page_source": page.provenance,
            "link_index": index,
            "href": item.get("href", ""),
            "label": item.get("label", ""),
            "canonical_target": slug,
            "matching_definitions": definitions.get(
                (page.slug, item.get("href", ""), item.get("label", "")), []
            ),
        }

    def location(diagnostic: dict) -> str:
        sources = diagnostic["matching_definitions"] or [diagnostic["page_source"]]
        return "; ".join(sources)

    for page in pages.values():
        targets: list[str] = []
        seen: dict[str, int] = {}
        for index, item in enumerate(page.links):
            href = core.normal_href(item.get("href", ""))
            if not href:
                continue
            raw_slug = core.url_slug(href)
            slug = aliases.get(raw_slug, raw_slug)
            if slug not in pages:
                errors.append(f"{page.slug}: missing linked subject {href}")
                continue
            if slug == page.slug:
                diagnostic = describe(page, index, slug)
                self_links.append(diagnostic)
                errors.append(
                    f"{page.slug or '/'}: self-link links[{index}] "
                    f"{diagnostic['href']!r} -> {slug or '/'} ({location(diagnostic)})"
                )
            if slug in seen:
                diagnostic = describe(page, index, slug)
                first = describe(page, seen[slug], slug)
                diagnostic["first_link"] = first
                duplicate_routes.append(diagnostic)
                errors.append(
                    f"{page.slug or '/'}: duplicate route links[{index}] "
                    f"{diagnostic['href']!r} -> {slug or '/'} ({location(diagnostic)}); "
                    f"first links[{seen[slug]}] {first['href']!r} ({location(first)})"
                )
                continue
            seen[slug] = index
            # core.connect removes self-links. They must not supply outgoing
            # coverage or inbound routes in either graph, even before cleanup.
            if slug == page.slug:
                continue
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
    thin_leaf_set = set(thin_leaf_slugs)
    model_thin_leaves = [slug for slug in model_slugs if slug in thin_leaf_set]

    root_slugs = sorted(slug for slug, page in pages.items() if not page.parent)

    def pct(n: int, d: int) -> float:
        return round((100.0 * n / d), 2) if d else 0.0

    strict_outgoing = {}
    strict_inbound: Counter[str] = Counter()
    for slug, page in pages.items():
        hierarchy = set(children.get(slug, []))
        if page.parent:
            hierarchy.add(page.parent)
        targets = [target for target in outgoing[slug] if target not in hierarchy]
        strict_outgoing[slug] = targets
        strict_inbound.update(targets)
    strict_with_links = sum(bool(targets) for targets in strict_outgoing.values())
    strict_thin_leaves = [slug for slug in leaf_slugs if not strict_outgoing[slug]]
    strict_model_with_links = [slug for slug in model_slugs if strict_outgoing[slug]]
    strict_thin_leaf_set = set(strict_thin_leaves)
    strict_model_thin_leaves = [slug for slug in model_slugs if slug in strict_thin_leaf_set]
    strict_no_inbound = sorted(slug for slug in pages if not strict_inbound[slug])

    return {
        "metric_definitions": {
            "top_level": (
                "Unique explicit subject routes after alias normalization, excluding "
                "self-links and duplicate targets. Direct parent/child routes remain; "
                "legacy lateral_* names are retained for comparison with earlier reports."
            ),
            "strict_lateral": (
                "Explicit routes excluding declared direct parents and direct children. "
                "Neither graph includes automatic child routes added by core.connect."
            ),
            "thin_leaf": "No declared children and no outgoing route in the measured graph.",
            "hygiene_counts": (
                "Every self-link occurrence and every duplicate after the first canonical "
                "target. A repeated self-link contributes to both counts; both block preflight."
            ),
            "model_pages": "Existing slug-based cohort: subjects ending in -v-arendu.",
        },
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
        "duplicate_route_count": len(duplicate_routes),
        "self_link_count": len(self_links),
        "strict_lateral": {
            "link_edges": sum(len(targets) for targets in strict_outgoing.values()),
            "pages_with_links": strict_with_links,
            "pages_without_links": subjects - strict_with_links,
            "lateral_coverage_pct": pct(strict_with_links, subjects),
            "thin_leaf_pages": len(strict_thin_leaves),
            "thin_leaf_pct": pct(len(strict_thin_leaves), subjects),
            "pages_without_lateral_inbound": len(strict_no_inbound),
            "model_pages_with_links": len(strict_model_with_links),
            "model_lateral_coverage_pct": pct(len(strict_model_with_links), len(model_slugs)),
            "model_thin_leaves": len(strict_model_thin_leaves),
        },
        "details": {
            "root_slugs": root_slugs,
            "thin_leaf_slugs": thin_leaf_slugs,
            "model_thin_leaf_slugs": model_thin_leaves,
            "pages_without_lateral_inbound_slugs": no_lateral_inbound_slugs,
            "duplicate_routes": duplicate_routes,
            "self_links": self_links,
            "strict_lateral": {
                "thin_leaf_slugs": strict_thin_leaves,
                "model_thin_leaf_slugs": strict_model_thin_leaves,
                "pages_without_lateral_inbound_slugs": strict_no_inbound,
            },
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
