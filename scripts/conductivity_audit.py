#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import site_core as core  # noqa: E402


def percentile(values, p):
    if not values:
        return 0
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * p
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


def load_pages(root: Path):
    metadata = core.read_json(root / "content" / "legacy-metadata.json", {})
    aliases = core.read_json(root / "content" / "aliases.json", {})
    pages = core.read_legacy(root, metadata)
    core.merge_records(root, pages)
    core.merge_legacy_navigation(root, pages)
    for alias, target in aliases.items():
        if target not in pages:
            raise ValueError(f"Alias {alias}: missing target {target}")
        pages.pop(alias, None)
    core.connect(pages, aliases)
    return pages


def main():
    pages = load_pages(ROOT)
    slugs = set(pages)
    children = defaultdict(set)
    for slug, page in pages.items():
        if page.parent:
            children[page.parent].add(slug)

    explicit = defaultdict(set)
    for slug, page in pages.items():
        for item in page.links:
            href = item.get("href", "")
            if not href:
                continue
            target = core.url_slug(href)
            if target in slugs and target != slug:
                explicit[slug].add(target)

    # connect() automatically injects parent -> child navigation. Separate that
    # structural tree from lateral/authored cross-links.
    structural = defaultdict(set)
    for slug, page in pages.items():
        if page.parent:
            structural[slug].add(page.parent)
        structural[slug].update(children.get(slug, set()))

    lateral = {
        slug: set(explicit.get(slug, set())) - structural.get(slug, set())
        for slug in pages
    }

    adjacency = {
        slug: structural.get(slug, set()) | lateral.get(slug, set())
        for slug in pages
    }
    inbound = Counter()
    lateral_inbound = Counter()
    for slug, targets in adjacency.items():
        for target in targets:
            inbound[target] += 1
    for slug, targets in lateral.items():
        for target in targets:
            lateral_inbound[target] += 1

    outdegrees = [len(adjacency[s]) for s in pages]
    lateral_degrees = [len(lateral[s]) for s in pages]
    child_counts = [len(children[s]) for s in pages]

    def depth(slug):
        seen = set()
        d = 0
        cur = slug
        while cur in pages and pages[cur].parent:
            if cur in seen:
                return None
            seen.add(cur)
            cur = pages[cur].parent
            d += 1
            if d > 100:
                return None
        return d

    depths = {s: depth(s) for s in pages}
    valid_depths = [d for d in depths.values() if d is not None]

    leaf_slugs = [s for s in pages if not children.get(s)]
    lateral_covered = [s for s in pages if lateral[s]]
    lateral_leaf = [s for s in leaf_slugs if lateral[s]]
    vertical_only = [s for s in pages if not lateral[s]]
    isolated_lateral = [s for s in pages if not lateral[s] and not children.get(s) and pages[s].parent]

    provenance = Counter()
    provenance_lateral = Counter()
    for slug, page in pages.items():
        provenance[page.provenance] += 1
        if lateral[slug]:
            provenance_lateral[page.provenance] += 1

    parent_rows = []
    for parent, kids in children.items():
        if not kids:
            continue
        lateral_kids = sum(bool(lateral[k]) for k in kids)
        leaf_kids = sum(not children.get(k) for k in kids)
        thin_leaf_kids = sum((not children.get(k) and not lateral[k]) for k in kids)
        parent_rows.append({
            "parent": parent,
            "children": len(kids),
            "leaf_children": leaf_kids,
            "children_with_lateral": lateral_kids,
            "thin_leaf_children": thin_leaf_kids,
            "thin_leaf_share": round(thin_leaf_kids / len(kids), 3),
            "parent_lateral": len(lateral[parent]),
            "parent_title": pages[parent].search_title if parent in pages else "",
        })

    hubs = sorted(
        (
            {
                "slug": s,
                "title": pages[s].search_title,
                "outdegree": len(adjacency[s]),
                "children": len(children.get(s, set())),
                "lateral_out": len(lateral[s]),
                "inbound": inbound[s],
                "lateral_in": lateral_inbound[s],
                "source": pages[s].provenance,
            }
            for s in pages
        ),
        key=lambda x: (x["outdegree"], x["inbound"]),
        reverse=True,
    )[:40]

    thin_clusters = sorted(
        [r for r in parent_rows if r["children"] >= 4],
        key=lambda r: (r["thin_leaf_share"], r["thin_leaf_children"], r["children"]),
        reverse=True,
    )[:50]

    lateral_sources = sorted(
        (
            {
                "source": src,
                "pages": count,
                "pages_with_lateral": provenance_lateral[src],
                "lateral_coverage": round(provenance_lateral[src] / count, 3),
            }
            for src, count in provenance.items()
            if count >= 4
        ),
        key=lambda x: (x["lateral_coverage"], -x["pages"]),
    )

    thin_samples = sorted(
        (
            {
                "slug": s,
                "title": pages[s].search_title,
                "parent": pages[s].parent,
                "depth": depths[s],
                "source": pages[s].provenance,
            }
            for s in isolated_lateral
        ),
        key=lambda x: (x["parent"], x["slug"]),
    )[:120]

    result = {
        "subjects": len(pages),
        "edges": sum(len(v) for v in adjacency.values()),
        "structural_edges": sum(len(v) for v in structural.values()),
        "lateral_edges": sum(len(v) for v in lateral.values()),
        "lateral_coverage_pages": len(lateral_covered),
        "lateral_coverage_share": round(len(lateral_covered) / len(pages), 4),
        "vertical_only_pages": len(vertical_only),
        "vertical_only_share": round(len(vertical_only) / len(pages), 4),
        "leaf_pages": len(leaf_slugs),
        "leaf_share": round(len(leaf_slugs) / len(pages), 4),
        "leaf_with_lateral": len(lateral_leaf),
        "leaf_with_lateral_share": round(len(lateral_leaf) / len(leaf_slugs), 4) if leaf_slugs else 0,
        "thin_leaf_pages": len(isolated_lateral),
        "thin_leaf_share_all": round(len(isolated_lateral) / len(pages), 4),
        "outdegree": {
            "min": min(outdegrees),
            "median": statistics.median(outdegrees),
            "p90": round(percentile(outdegrees, .90), 2),
            "p99": round(percentile(outdegrees, .99), 2),
            "max": max(outdegrees),
        },
        "lateral_degree": {
            "median": statistics.median(lateral_degrees),
            "p90": round(percentile(lateral_degrees, .90), 2),
            "p99": round(percentile(lateral_degrees, .99), 2),
            "max": max(lateral_degrees),
        },
        "depth": {
            "median": statistics.median(valid_depths),
            "p90": round(percentile(valid_depths, .90), 2),
            "max": max(valid_depths),
            "cycles_or_invalid": sum(v is None for v in depths.values()),
        },
        "hubs": hubs,
        "thin_clusters": thin_clusters,
        "sources_by_lateral_coverage": lateral_sources[:80],
        "thin_leaf_samples": thin_samples,
        "thin_members_top_clusters": {
            row["parent"]: [
                {
                    "slug": kid,
                    "title": pages[kid].search_title,
                    "source": pages[kid].provenance,
                }
                for kid in sorted(children[row["parent"]])
                if not children.get(kid) and not lateral[kid]
            ][:80]
            for row in thin_clusters[:20]
        },
    }

    print("CONDUCTIVITY_AUDIT_JSON_BEGIN")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("CONDUCTIVITY_AUDIT_JSON_END")


if __name__ == "__main__":
    main()
