#!/usr/bin/env python3
"""Compare a released build with the two-indexable-document candidate.

The only normalized HTML changes are the prior N1 noindex tag, the single
stylesheet version, and the old/new documentation blocks. No other visible or
head content is normalized away. Redirects must be identical bytes.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha1, sha256
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit

from bs4 import BeautifulSoup


EXPECTED_PATH_DIGEST = 'e0218c941f2e41e29e0f6ab8a0211641c2747cd99eabd05ea2bd7a68f3b1f24c'
BASE_COMMIT = 'f9789a41743221af9758374c216fc39fffcfd6a6'
FIELDS = ('title', 'h1', 'description', 'canonical', 'body', 'navigation', 'contact', 'head')
SOURCE_CSS = re.compile(r'\.sources(?:\s+(?:summary|ul|li|a))?\{[^{}]*\}')


def digest(value):
    if not isinstance(value, bytes):
        value = value.encode('utf-8')
    return sha256(value).hexdigest()


def json_digest(value):
    return digest(json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True))


def git(repository, *arguments):
    return subprocess.run(['git', '-C', str(repository), *arguments], check=True, capture_output=True).stdout


def field_values(doc):
    return {
        'title': [str(node) for node in doc.find_all('title')],
        'h1': [str(node) for node in doc.find_all('h1')],
        'description': [str(node) for node in doc.find_all('meta', attrs={'name': 'description'})],
        'canonical': [str(node) for node in doc.find_all('link', rel='canonical')],
        'body': str(doc.body),
        'navigation': [str(node) for node in doc.find_all('nav')],
        'contact': [str(node) for node in doc.select('.contact-block')],
        'head': str(doc.head),
    }


def source_items(blocks):
    return [(link.get('href', ''), link.get_text(' ', strip=True)) for block in blocks for link in block.select('a[href]')]


def ordered_subset(candidate, baseline):
    iterator = iter(baseline)
    return all(any(item == original for original in iterator) for item in candidate)


def normalize(doc, relative, side, css_version, errors):
    details = relative.startswith('details/')
    robots = doc.find_all('meta', attrs={'name': 'robots'})
    removed_robot = 0
    if details and side == 'before':
        if len(robots) != 1 or robots[0].attrs != {'name': 'robots', 'content': 'noindex,follow'}:
            errors.append(f'{relative}: baseline N1 robots differs from the permitted old tag')
        else:
            robots[0].decompose()
            removed_robot = 1
    elif details and robots:
        errors.append(f'{relative}: candidate N1 has an unexpected robots tag')
    sheets = doc.find_all('link', rel='stylesheet')
    if len(sheets) != 1 or sheets[0].get('href') != '/assets/canon.css?v=' + css_version:
        errors.append(f'{relative}: {side} stylesheet is not the expected versioned canonical asset')
    else:
        sheets[0]['href'] = '/assets/canon.css?v=ALLOWED_VERSION_CHANGE'
    blocks = doc.select('.sources')
    items = source_items(blocks)
    if blocks:
        if not details or len(blocks) != 1 or blocks[0].name != 'details':
            errors.append(f'{relative}: {side} documentation is not one N1 details block')
        if side == 'after':
            for block in blocks:
                summary = block.find('summary', recursive=False)
                wrapper = doc.select_one('.page')
                children = wrapper.find_all(recursive=False) if wrapper else []
                if (block.has_attr('open') or not summary or summary.get_text(' ', strip=True) != 'Документация'
                        or block.parent is not wrapper or len(children) < 2
                        or children[-1] is not block or children[-2] is not doc.select_one('.site-footer')):
                    errors.append(f'{relative}: candidate documentation does not follow the approved footer policy')
        for block in blocks:
            block.decompose()
    values = field_values(doc)
    return str(doc), values, items, len(blocks), removed_robot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    errors = []
    paths_before = sorted(path.relative_to(args.before).as_posix() for path in args.before.rglob('*.html'))
    paths_after = sorted(path.relative_to(args.after).as_posix() for path in args.after.rglob('*.html'))
    path_digest_before = json_digest(paths_before)
    path_digest_after = json_digest(paths_after)
    if paths_before != paths_after:
        errors.append('HTML path sets differ')
    if len(paths_before) != 4046 or len(paths_after) != 4046:
        errors.append('HTML count is not the expected 4046 on both sides')
    if path_digest_before != EXPECTED_PATH_DIGEST or path_digest_after != EXPECTED_PATH_DIGEST:
        errors.append('HTML path digest differs from the released 4046-route manifest')
    css_before = (args.before / 'assets/canon.css').read_bytes()
    css_after = (args.after / 'assets/canon.css').read_bytes()
    css_versions = (digest(css_before)[:12], digest(css_after)[:12])
    css_remainder_before = SOURCE_CSS.sub('', css_before.decode('utf-8'))
    css_remainder_after = SOURCE_CSS.sub('', css_after.decode('utf-8'))
    if css_remainder_before != css_remainder_after:
        errors.append('CSS changed outside documentation selectors')
    page_records = []
    field_records = {side: {name: [] for name in FIELDS} for side in ('before', 'after')}
    raw_manifests = {side: [] for side in ('before', 'after')}
    normalized_manifests = {side: [] for side in ('before', 'after')}
    redirect_manifests = {side: [] for side in ('before', 'after')}
    counts = Counter()
    for index, relative in enumerate(sorted(set(paths_before) & set(paths_after)), 1):
        payloads = [(root / relative).read_bytes() for root in (args.before, args.after)]
        hashes = [digest(payload) for payload in payloads]
        docs = [BeautifulSoup(payload.decode('utf-8'), 'html.parser') for payload in payloads]
        redirects = [bool(doc.find('meta', attrs={'http-equiv': re.compile('^refresh$', re.I)})) for doc in docs]
        for side, hash_value in zip(('before', 'after'), hashes):
            raw_manifests[side].append([relative, hash_value])
        counts['byte_identical_html' if payloads[0] == payloads[1] else 'changed_html'] += 1
        if redirects[0] or redirects[1]:
            counts['redirects'] += 1
            if not all(redirects):
                errors.append(f'{relative}: redirect/document role changed')
            if payloads[0] != payloads[1]:
                errors.append(f'{relative}: redirect bytes changed')
            for side, hash_value in zip(('before', 'after'), hashes):
                redirect_manifests[side].append([relative, hash_value])
            page_records.append({'path': relative, 'role': 'redirect', 'before_sha256': hashes[0], 'after_sha256': hashes[1], 'equal': payloads[0] == payloads[1]})
            continue
        counts['ordinary_documents'] += 1
        counts['editorial_documents' if relative.startswith('details/') else 'entry_or_condition_documents'] += 1
        normalized = [normalize(doc, relative, side, version, errors) for doc, side, version in zip(docs, ('before', 'after'), css_versions)]
        counts['baseline_noindex_tags_removed'] += normalized[0][4]
        for side, item in zip(('before', 'after'), normalized):
            counts[side + '_source_blocks'] += item[3]
            counts[side + '_source_links'] += len(item[2])
        if not ordered_subset(normalized[1][2], normalized[0][2]):
            errors.append(f'{relative}: public documentation adds/reorders/rewrites an original source')
        equal = normalized[0][0] == normalized[1][0]
        counts['normalized_documents_equal'] += equal
        if not equal:
            errors.append(f'{relative}: normalized document differs outside the allowed change set')
        changed_fields = []
        for name in FIELDS:
            left, right = (item[1][name] for item in normalized)
            if left != right:
                changed_fields.append(name)
                errors.append(f'{relative}: {name} changed')
            for side, value in zip(('before', 'after'), (left, right)):
                field_records[side][name].append([relative, json_digest(value)])
        normalized_hashes = [digest(item[0]) for item in normalized]
        for side, hash_value in zip(('before', 'after'), normalized_hashes):
            normalized_manifests[side].append([relative, hash_value])
        page_records.append({'path': relative, 'role': 'editorial' if relative.startswith('details/') else 'entry_or_condition', 'before_sha256': hashes[0], 'after_sha256': hashes[1], 'normalized_before_sha256': normalized_hashes[0], 'normalized_after_sha256': normalized_hashes[1], 'changed_fields': changed_fields, 'sources_before': len(normalized[0][2]), 'sources_after': len(normalized[1][2]), 'equal_after_allowed_changes': equal})
        if index % 250 == 0:
            print(json.dumps({'compared_html': index, 'errors': len(errors)}, ensure_ascii=False), flush=True)
    if counts['redirects'] != 78 or counts['ordinary_documents'] != 3968 or counts['editorial_documents'] != 1980:
        errors.append('Page-role counts differ from 78 redirects, 3968 documents and 1980 editorials')
    non_html = []
    files_before = {p.relative_to(args.before).as_posix() for p in args.before.rglob('*') if p.is_file() and p.suffix != '.html'}
    files_after = {p.relative_to(args.after).as_posix() for p in args.after.rglob('*') if p.is_file() and p.suffix != '.html'}
    if files_before != files_after:
        errors.append('Non-HTML file set changed')
    for relative in sorted(files_before & files_after):
        left, right = ((root / relative).read_bytes() for root in (args.before, args.after))
        allowed = relative in {'assets/canon.css', 'sitemap.xml'}
        if left != right and not allowed:
            errors.append(f'{relative}: unrelated non-HTML artifact changed')
        non_html.append({'path': relative, 'before_sha256': digest(left), 'after_sha256': digest(right), 'equal': left == right, 'change_allowed': allowed})
    protected_paths = ['content/sections', 'content/legacy-metadata.json', 'content/aliases.json']
    changed_content = git(args.repository, 'diff', '--name-only', BASE_COMMIT, '--', *protected_paths).decode().splitlines()
    untracked_content = git(args.repository, 'ls-files', '--others', '--exclude-standard', '--', *protected_paths).decode().splitlines()
    source_records = []
    for row in git(args.repository, 'ls-tree', '-r', BASE_COMMIT, '--', *protected_paths).decode().splitlines():
        header, relative = row.split('\t', 1)
        expected_blob = header.split()[-1]
        path = args.repository / relative
        if not path.exists():
            errors.append(f'{relative}: protected source absent')
            continue
        payload = path.read_bytes()
        blob = sha1(b'blob ' + str(len(payload)).encode() + b'\0' + payload).hexdigest()
        source_records.append({'path': relative, 'expected_git_blob': expected_blob, 'actual_git_blob': blob, 'sha256': digest(payload)})
        if expected_blob != blob:
            errors.append(f'{relative}: protected source differs from {BASE_COMMIT}')
    if changed_content or untracked_content:
        errors.append('Protected source scope has changed or untracked files')
    records_path = args.output.with_name(args.output.stem + '-pages.json')
    records_path.write_text(json.dumps(page_records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    result = {
        'schema': 'ontos-dual-index-preservation-v1',
        'checked_at_utc': datetime.now(timezone.utc).isoformat(),
        'script': str(Path(__file__).resolve()),
        'script_sha256': digest(Path(__file__).read_bytes()),
        'baseline': str(args.before.resolve()), 'candidate': str(args.after.resolve()),
        'baseline_commit': BASE_COMMIT,
        'current_head': git(args.repository, 'rev-parse', 'HEAD').decode().strip(),
        'status': 'pass' if not errors else 'fail',
        'allowed_html_changes': ['Remove the exact prior N1 noindex,follow meta tag', 'Change only the canonical CSS version', 'Remove, relocate and filter original .sources documentation'],
        'html_paths': {'before': len(paths_before), 'after': len(paths_after), 'removed': sorted(set(paths_before) - set(paths_after)), 'added': sorted(set(paths_after) - set(paths_before)), 'before_sha256': path_digest_before, 'after_sha256': path_digest_after, 'expected_sha256': EXPECTED_PATH_DIGEST},
        'counts': dict(counts),
        'raw_html_manifest_sha256': {side: json_digest(value) for side, value in raw_manifests.items()},
        'normalized_html_manifest_sha256': {side: json_digest(value) for side, value in normalized_manifests.items()},
        'redirect_manifest_sha256': {side: json_digest(value) for side, value in redirect_manifests.items()},
        'field_manifest_sha256': {name: {side: json_digest(field_records[side][name]) for side in ('before', 'after')} for name in FIELDS},
        'css': {'before_version': css_versions[0], 'after_version': css_versions[1], 'outside_documentation_equal': css_remainder_before == css_remainder_after, 'outside_documentation_sha256': digest(css_remainder_before)},
        'non_html': non_html,
        'protected_sources': {'scope': protected_paths, 'tracked_files_checked': len(source_records), 'changed_files': changed_content, 'untracked_files': untracked_content, 'manifest_sha256': json_digest(source_records), 'all_git_blobs_equal': all(row['expected_git_blob'] == row['actual_git_blob'] for row in source_records)},
        'page_records': {'path': str(records_path.resolve()), 'sha256': digest(records_path.read_bytes()), 'records': len(page_records)},
        'errors': errors,
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('status', 'counts', 'html_paths', 'protected_sources', 'errors')}, ensure_ascii=False), flush=True)
    raise SystemExit(0 if not errors else 1)


if __name__ == '__main__':
    main()
