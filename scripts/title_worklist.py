#!/usr/bin/env python3
"""Inventory every public title and track model-authored functional continuations.

This tool NEVER writes titles or editorial phrases. It audits the finished
static site against source titles, the authored manifest, and source evidence.
"""
from __future__ import annotations

import argparse
import csv
from html import unescape
import json
from pathlib import Path
import re
from bs4 import BeautifulSoup

from apply_authored_titles import DEFAULT_MANIFEST, validate_manifest

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEWS = ROOT / "content" / "title-editorial-evidence.json"
TITLE = re.compile(r"<title\b[^>]*>([\s\S]*?)</title\s*>", re.I)
REFRESH = re.compile(r'<meta\b[^>]*\bhttp-equiv\s*=\s*["\']?refresh\b', re.I)
ROLES = ("n0", "n1")


def normalize(text: str) -> str:
    return " ".join(str(text).split()).casefold()


def extract_title(html: str, where: Path) -> str:
    matches = TITLE.findall(html)
    if len(matches) != 1:
        raise ValueError(f"Expected one title in {where}")
    return unescape(BeautifulSoup(matches[0], "html.parser").get_text()).strip()


def validate_reviews(pairs: dict, reviews_path: Path, root: Path) -> dict:
    document = json.loads(reviews_path.read_text(encoding="utf-8"))
    if document.get("schema_version") != 1 or not isinstance(document.get("reviews"), dict):
        raise ValueError("Invalid functional-title review manifest")
    reviews = document["reviews"]
    if set(reviews) != set(pairs):
        raise ValueError(f"Title / evidence topics differ: missing {sorted(set(pairs)-set(reviews))}; "
                         f"extra {sorted(set(reviews)-set(pairs))}")
    for slug, roles in reviews.items():
        if set(roles) != set(ROLES):
            raise ValueError(f"{slug}: review must cover N.0 and N.1 independently")
        for role, review in roles.items():
            if not isinstance(review, dict):
                raise ValueError(f"{slug}/{role}: review must be a record")
            for field in ("source_path", "source_quote", "decision", "next_action"):
                if not isinstance(review.get(field), str) or len(review[field].strip()) < 12:
                    raise ValueError(f"{slug}/{role}: missing meaningful {field}")
            source = (root / review["source_path"]).resolve()
            if not source.is_relative_to(root.resolve()) or not source.is_file():
                raise ValueError(f"{slug}/{role}: source document not found or outside project")
            raw = source.read_text(encoding="utf-8")
            content = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
            if normalize(review["source_quote"]) not in normalize(content):
                raise ValueError(f"{slug}/{role}: evidence fragment not found in {review['source_path']}")
    return reviews


def build_worklist(report: dict, site: Path, manifest: Path, reviews_path: Path,
                   root: Path = ROOT) -> dict:
    pages = report.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("Missing compiled source-page inventory")
    pairs = validate_manifest(manifest)
    reviews = validate_reviews(pairs, reviews_path, root)
    topic_slugs = [p["slug"] for p in pages]
    if len(set(topic_slugs)) != len(pages):
        raise ValueError("Duplicate topic slugs in source report")
    if set(pairs) - set(topic_slugs):
        raise ValueError(f"Authored titles for absent topics: {sorted(set(pairs)-set(topic_slugs))}")

    records = []
    for topic in pages:
        slug = topic["slug"]
        for role in ROLES:
            route = ("/details/" if role == "n1" else "/") + (slug + "/" if slug else "")
            html_file = site / route.lstrip("/") / "index.html"
            if not html_file.is_file():
                raise ValueError(f"Missing compiled page: {route}")
            html = html_file.read_text(encoding="utf-8")
            if REFRESH.search(html):
                raise ValueError(f"Unexpected redirect in title inventory: {route}")
            current = extract_title(html, html_file)
            original = topic["entry_title"] if role == "n0" else topic["editorial_title"]
            expected = pairs.get(slug, {}).get(role, original)
            if current != expected:
                raise ValueError(f"{route}: title differs from reviewed original/approved wording "
                                 f"({current!r} versus {expected!r})")
            review = reviews.get(slug, {}).get(role, {})
            records.append({
                "url": route, "role": role, "slug": slug,
                "topic_source": topic.get("source", ""),
                "parent": topic.get("parent", ""),
                "search_or_editorial_heading": original,
                "published_title": current,
                "review_state": "model_reviewed_pilot" if review else "pending_functional_review",
                "source_path": review.get("source_path", ""),
                "source_quote": review.get("source_quote", ""),
                "functional_decision": review.get("decision", ""),
                "functional_next_action": review.get("next_action", ""),
            })

    conditions = 0
    for html_file in sorted((site / "usloviya").glob("*/index.html")):
        html = html_file.read_text(encoding="utf-8")
        if REFRESH.search(html):
            continue
        conditions += 1
        route = "/" + html_file.relative_to(site).parent.as_posix() + "/"
        records.append({
            "url": route, "role": "condition", "slug": html_file.parent.name,
            "topic_source": "published conditions",
            "parent": "usloviya",
            "search_or_editorial_heading": "",
            "published_title": extract_title(html, html_file),
            "review_state": "pending_functional_review",
            "source_path": "", "source_quote": "",
            "functional_decision": "", "functional_next_action": "",
        })
    expected_conditions = report.get("conditions", conditions)
    if conditions != expected_conditions:
        raise ValueError(f"Conditions: compiled {conditions} versus report {expected_conditions}")
    summary = {
        "source_topics": len(pages),
        "paired_titles": len(pages) * 2,
        "conditions": conditions,
        "total_html_titles": len(records),
        "model_reviewed_topics": len(pairs),
        "model_reviewed_titles": len(pairs) * 2,
        "pending_topic_titles": 2 * (len(pages) - len(pairs)),
        "pending_all_titles": len(records) - len(pairs) * 2,
        "mechanically_generated_title_wording": False,
    }
    return {"schema_version": 1, "summary": summary, "records": records}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=Path("_audit/build.json"))
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--reviews", type=Path, default=DEFAULT_REVIEWS)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=Path("_audit/title-worklist.json"))
    parser.add_argument("--csv", type=Path, default=Path("_audit/title-worklist.csv"))
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    result = build_worklist(report, args.site, args.manifest, args.reviews, args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with args.csv.open("w", encoding="utf-8-sig", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(result["records"][0]))
        writer.writeheader()
        writer.writerows(result["records"])
    print(json.dumps(result["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
