#!/usr/bin/env python3
"""Publish complete, model-authored titles without generating any title language.

The JSON manifest owns all wording. This script only copies reviewed, complete
strings into the compiled HTML <title> element. Pages without authored titles
retain their existing title, and redirects are never retitled.
"""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "content" / "authored-title-responses.json"
TITLE = re.compile(r"<title\b[^>]*>[\s\S]*?</title\s*>", re.I)
REFRESH = re.compile(r'<meta\b[^>]*\bhttp-equiv\s*=\s*["\']?refresh\b', re.I)
SLUG = re.compile(r"[a-z0-9][a-z0-9-]*\Z")


def validate_manifest(path: Path) -> dict[str, dict[str, str]]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or not isinstance(manifest.get("pairs"), dict):
        raise ValueError("Unsupported title manifest schema")
    pairs = manifest["pairs"]
    if not pairs:
        raise ValueError("No authored title pairs")
    used_titles = set()
    for slug, titles in pairs.items():
        if slug != "" and not SLUG.fullmatch(slug):
            raise ValueError(f"Invalid topic slug: {slug!r}")
        if not isinstance(titles, dict) or set(titles) != {"n0", "n1"}:
            raise ValueError(f"{slug}: exactly two authored titles required")
        for role in ("n0", "n1"):
            title = titles[role]
            if not isinstance(title, str) or title.count(" | ") != 1:
                raise ValueError(f"{slug}/{role}: expected one authored question | response")
            question, response = title.split(" | ")
            if not (len(question.strip()) >= 2 and len(response.strip()) >= 14
                    and 30 <= len(title) <= 125):
                raise ValueError(f"{slug}/{role}: malformed or excessively long title")
            if any(character in title for character in "<>\r\n") or "ontos.rent" in title.casefold():
                raise ValueError(f"{slug}/{role}: markup or automatic brand name not allowed")
            if title.casefold() in used_titles:
                raise ValueError(f"{slug}/{role}: duplicate authored title")
            used_titles.add(title.casefold())
        if titles["n0"] == titles["n1"]:
            raise ValueError(f"{slug}: search and editorial roles must differ")
    return pairs


def destinations(site: Path, pairs: dict[str, dict[str, str]]) -> list[tuple[Path, str]]:
    targets: list[tuple[Path, str]] = []
    for slug, titles in pairs.items():
        for role, title in titles.items():
            part = (Path("details") / slug) if role == "n1" else Path(slug)
            path = site / part / "index.html"
            if not path.is_file():
                raise ValueError(f"Authored topic does not exist in compiled site: {role}/{slug}")
            html = path.read_text(encoding="utf-8")
            if REFRESH.search(html) or len(TITLE.findall(html)) != 1:
                raise ValueError(f"Redirect or malformed title: {path.relative_to(site)}")
            targets.append((path, title))
    return targets


def apply(site: Path, manifest: Path = DEFAULT_MANIFEST, *, check: bool = False) -> dict:
    if not site.is_dir():
        raise ValueError(f"Compiled site missing: {site}")
    pairs = validate_manifest(manifest)
    targets = destinations(site, pairs)  # Preflight every path before any write.
    modified = 0
    for path, authored in targets:
        original = path.read_text(encoding="utf-8")
        expected = f"<title>{escape(authored, quote=False)}</title>"
        if check:
            if expected not in original:
                raise ValueError(f"Authored title not installed: {path.relative_to(site)}")
            continue
        replacement, count = TITLE.subn(lambda _: expected, original, count=1)
        if count != 1:
            raise ValueError(f"Missing title: {path.relative_to(site)}")
        if replacement != original:
            path.write_text(replacement, encoding="utf-8")
            modified += 1
    return {
        "mode": "check" if check else "apply",
        "model_authored_topics": len(pairs),
        "model_authored_titles": len(targets),
        "modified": modified,
        "automatic_text_generation": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(apply(args.site, args.manifest, check=args.check),
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
