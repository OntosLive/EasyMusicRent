#!/usr/bin/env python3
"""Inventory source-defined routes, including pages that have no source folder.

Run before publishing a content layer. Exact duplicate checks do not establish
semantic uniqueness; review related entries returned by --match as well.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import site_core as core


def inspect(root: Path, candidates: list[Path] | None = None) -> dict:
    root = root.resolve()
    errors = []
    pages = core.read_legacy(root, core.read_json(root/'content/legacy-metadata.json', {}))
    records = {slug: {'slug':slug, 'search_title':p.search_title,
                        'parent':p.parent, 'source':p.provenance} for slug,p in pages.items()}
    paths = sorted((root/'content/sections').glob('*.json'))
    for candidate in candidates or []:
        candidate = candidate.resolve()
        if candidate not in [p.resolve() for p in paths]:
            paths.append(candidate)
    for path in paths:
        label = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        document = core.read_json(path, {})
        for record in document.get('pages', []):
            slug = record.get('slug', '')
            if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', slug):
                errors.append(f'{label}: invalid slug {slug!r}')
                continue
            if record.get('mode') == 'enrich':
                if slug not in records:
                    errors.append(f'{label}: enrich has no prior subject {slug}')
                    continue
                for key in ('search_title', 'parent'):
                    if key in record: records[slug][key] = record[key]
            elif slug in records:
                errors.append(f'{slug}: duplicate declarations: {records[slug]["source"]} / {label}')
            else:
                records[slug] = {'slug':slug, 'search_title':record.get('search_title',''),
                                 'parent':record.get('parent',''), 'source':label}
    aliases = core.read_json(root/'content/aliases.json', {})
    active = {s:r for s,r in records.items() if s not in aliases}
    titles = {}
    for slug, record in active.items():
        title = re.sub(r'\s+', ' ', record['search_title']).strip().casefold()
        if not title:
            errors.append(f'{slug}: missing request title')
        elif title in titles:
            errors.append(f'duplicate request: {title}: {titles[title]} / {slug}')
        titles[title] = slug
        parent = record['parent']
        if parent and parent not in active:
            errors.append(f'{slug}: missing active parent {parent}')
    return {'subjects':len(active), 'errors':errors,
            'pages':sorted(active.values(), key=lambda r:r['slug'])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=core.ROOT)
    parser.add_argument('--candidate', type=Path, action='append', default=[])
    parser.add_argument('--match', help='Case-insensitive search over slug, title and parent')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = inspect(args.root, args.candidate)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if args.match:
        q=args.match.casefold()
        print(json.dumps([p for p in result['pages'] if q in ' '.join(p.values()).casefold()],ensure_ascii=False,indent=2))
    else:
        print(json.dumps({k:v for k,v in result.items() if k!='pages'},ensure_ascii=False))
    raise SystemExit(bool(result['errors']))

if __name__ == '__main__':
    main()
