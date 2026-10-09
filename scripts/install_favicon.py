#!/usr/bin/env python3
"""Publish a stable, legible music-rental favicon to every canonical HTML page.

SVG and ICO are predesigned assets, not runtime-generated images.
Technical redirects are not modified.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
MARKER = "<!-- INSTRUMENT-FUND-FAVICON -->"
LINKS = '''\n<!-- INSTRUMENT-FUND-FAVICON -->
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
'''
HEAD_CLOSE = re.compile(r"</head\s*>", re.I)
REFRESH = re.compile(r'<meta\b[^>]*\bhttp-equiv\s*=\s*["\']?refresh\b', re.I)
FOREIGN_ICON = re.compile(r'<link\b[^>]*\brel\s*=\s*["\'](?:shortcut\s+)?icon["\']', re.I)


def verify_assets() -> dict[str, bytes]:
    svg = (ASSETS / "favicon.svg").read_bytes()
    ico = (ASSETS / "favicon.ico").read_bytes()
    tree = ET.fromstring(svg)
    if tree.tag != "{http://www.w3.org/2000/svg}svg":
        raise ValueError("Favicon SVG root is invalid")
    if ico[:4] != b"\x00\x00\x01\x00" or len(ico) < 40:
        raise ValueError("Favicon ICO header is invalid")
    return {"favicon.svg": svg, "favicon.ico": ico}


def publish(site: Path, *, check: bool = False) -> dict:
    if not site.is_dir():
        raise ValueError(f"Missing built site: {site}")
    assets = verify_assets()
    for name, content in assets.items():
        path = site / name
        if check:
            if not path.exists() or path.read_bytes() != content:
                raise ValueError(f"Incorrect published icon: {name}")
        elif not path.exists() or path.read_bytes() != content:
            shutil.copyfile(ASSETS / name, path)

    documents, redirects, changed = 0, 0, 0
    for path in sorted(site.rglob("*.html")):
        original = path.read_text(encoding="utf-8")
        if REFRESH.search(original):
            redirects += 1
            if MARKER in original:
                raise ValueError(f"Redirect has favicon markup: {path}")
            continue
        documents += 1
        if original.count(MARKER) == 1:
            if original.count('href="/favicon.ico"') != 1 or original.count('href="/favicon.svg"') != 1:
                raise ValueError(f"Incomplete favicon links: {path}")
            continue
        if check:
            raise ValueError(f"Missing favicon links: {path.relative_to(site)}")
        if MARKER in original or FOREIGN_ICON.search(original):
            raise ValueError(f"Existing conflicting favicon: {path.relative_to(site)}")
        if len(HEAD_CLOSE.findall(original)) != 1:
            raise ValueError(f"Expected exactly one head end: {path.relative_to(site)}")
        updated = HEAD_CLOSE.sub(lambda m: LINKS + m.group(0), original, count=1)
        path.write_text(updated, encoding="utf-8")
        changed += 1
    if documents == 0:
        raise ValueError("No canonical documents found")
    return {
        "mode": "check" if check else "publish",
        "documents": documents,
        "redirects_unchanged": redirects,
        "titles_or_bodies_modified": False,
        "html_with_new_favicon": changed,
        "favicon_files": list(assets),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(publish(args.site, check=args.check), ensure_ascii=False))


if __name__ == "__main__":
    main()
