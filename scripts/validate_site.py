#!/usr/bin/env python3
"""Fail publication on broken routes, missing canon or mixed page roles."""
from __future__ import annotations
import argparse
from collections import defaultdict, deque
from hashlib import sha256
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit, unquote
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

BAD = re.compile(r'\b(?:L[0-9]|N\.[0-9])\b|следующий уровень будет раскрыт|первый критерий различения внутри|второй слой показывает|поперечными сценариями|карта\s+(?:фонда|клавишных|скрипк|контрабас|виолончел|цифрового)|инструментальная карта', re.I)
CONTACTS = ('tel:+79690532096','https://t.me/MUZPROKATMOSCOW','https://wa.me/79690532096')


def read(path):
    return BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')


def route(path, root):
    value = path.relative_to(root).as_posix()
    return '/' + value.removesuffix('index.html') if value.endswith('index.html') else '/' + value


def target_path(root, url):
    value = unquote(urlsplit(url).path).lstrip('/')
    path = root / value
    return path / 'index.html' if not Path(value).suffix else path


def validate(root: Path, report: dict):
    errors = []
    signatures = set()
    count = 0
    all_urls = set()
    graph = defaultdict(set)
    redirects = {}
    titles = defaultdict(list)
    for path in sorted(root.rglob('*.html')):
        url = route(path, root)
        all_urls.add(url)
        doc = read(path)
        refresh = doc.find('meta', attrs={'http-equiv': re.compile('refresh', re.I)})
        if refresh:
            target = refresh.get('content', '').split('url=', 1)[-1]
            redirects[url] = target
            if not target_path(root, target).exists():
                errors.append(f'{url}: missing redirect {target}')
            continue
        count += 1
        if len(doc.find_all('h1')) != 1:
            errors.append(f'{url}: expected exactly one content H1')
        if len(doc.select('.site-footer')) != 1:
            errors.append(f'{url}: footer not canonical')
        if len(doc.select('.contact')) != 1:
            errors.append(f'{url}: contact not canonical')
        contact = doc.select_one('.contact')
        if contact:
            signatures.add(sha256(str(contact).encode()).hexdigest())
            for href in CONTACTS:
                a = contact.find('a', href=href)
                if not a:
                    errors.append(f'{url}: missing {href}')
                if a and href.startswith('https') and not a.find('svg'):
                    errors.append(f'{url}: messenger icon absent')
        sheets = doc.select('link[rel="stylesheet"]')
        if len(sheets) != 1 or not sheets[0].get('href', '').startswith('/assets/canon.css?v='):
            errors.append(f'{url}: legacy or absent stylesheet')
        visible = doc.body.get_text(' ', strip=True) if doc.body else ''
        found = BAD.search(visible)
        if found:
            errors.append(f'{url}: internal template phrase: {found[0]}')
        if '+7 ___' in visible:
            errors.append(f'{url}: placeholder phone')
        canonical = doc.find('link', rel='canonical')
        if not canonical or urlsplit(canonical.get('href', '')).path != url:
            errors.append(f'{url}: invalid self-canonical')
        if url.startswith('/details/'):
            wordmark = doc.select_one('.wordmark')
            if not wordmark or wordmark.get_text(strip=True) != 'ONTOS.RENT':
                errors.append(f'{url}: missing institutional masthead')
            robot = doc.find('meta', attrs={'name': 'robots'})
            if not robot or 'noindex' not in robot.get('content', ''):
                errors.append(f'{url}: editorial index review not recorded')
            nav = doc.select_one('#razdely')
            blocks = doc.select_one('.arguments')
            if nav and blocks:
                order = list(doc.descendants)
                if order.index(nav) > order.index(blocks):
                    errors.append(f'{url}: children below block 01')
        else:
            robot = doc.find('meta', attrs={'name': 'robots'})
            if robot and 'noindex' in robot.get('content', ''):
                errors.append(f'{url}: request accidentally noindex')
        for a in doc.select('a[href]'):
            href = a['href']
            parts = urlsplit(href)
            if parts.scheme or parts.netloc:
                continue
            if '/karta/' in href:
                errors.append(f'{url}: obsolete map link {href}')
            absolute = urljoin(url, href)
            dest = target_path(root, absolute)
            if not dest.exists():
                errors.append(f'{url}: broken link {href}')
                continue
            graph[url].add(route(dest, root))
            if parts.fragment:
                destination = doc if dest == path else read(dest)
                if not destination.find(id=parts.fragment):
                    errors.append(f'{url}: missing anchor {href}')
    if len(signatures) != 1:
        errors.append(f'{len(signatures)} contact implementations, expected one')
    for item in report['pages']:
        titles[item['entry_title'].casefold()].append(item['slug'])
        entry = root / item['slug'] / 'index.html'
        if not entry.exists():
            errors.append(f'{item["slug"]}: absent entry')
            continue
        doc = read(entry)
        if not doc.h1 or doc.h1.get_text(' ', strip=True) != item['entry_title']:
            errors.append(f'{item["slug"]}: search H1 mismatch')
        if item['entry_title'] == item['editorial_title']:
            errors.append(f'{item["slug"]}: search/editorial title not split')
    for title, slugs in titles.items():
        if len(slugs) > 1:
            errors.append(f'duplicate request title: {title}: {slugs}')
    visited = set()
    queue = deque(['/'])
    while queue:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        queue.extend(graph[url])
        if url in redirects:
            queue.append(urlsplit(redirects[url]).path)
    orphaned = sorted(url for url in all_urls if url not in visited and url not in redirects)
    if orphaned:
        errors.append(f'unreachable pages: {orphaned}')
    sitemap = ET.parse(root / 'sitemap.xml')
    locations = [n.text for n in sitemap.iter() if n.tag.endswith('loc')]
    for location in locations:
        path = target_path(root, location)
        if not path.exists():
            errors.append(f'sitemap missing {location}')
            continue
        doc = read(path)
        robots = doc.find('meta', attrs={'name': 'robots'})
        if robots and 'noindex' in robots.get('content', ''):
            errors.append(f'sitemap includes noindex {location}')
    for directory in ('docs', 'data', 'scripts', 'tests', 'content', 'prompts', 'synthesis', 'synthesis-02', 'synthesis-03', 'archive'):
        if (root / directory).exists():
            errors.append(f'internal/experimental directory published: {directory}')
    return {'documents_checked': count, 'redirects': len(redirects), 'contact_variants': len(signatures), 'unreachable': len(orphaned), 'sitemap_entries': len(locations), 'errors': errors}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--site', type=Path, default=Path('_site'))
    parser.add_argument('--report', type=Path, default=Path('_audit/build.json'))
    parser.add_argument('--output', type=Path, default=Path('_audit/validation.json'))
    args = parser.parse_args()
    result = validate(args.site, json.loads(args.report.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(1 if result['errors'] else 0)


if __name__ == '__main__':
    main()
