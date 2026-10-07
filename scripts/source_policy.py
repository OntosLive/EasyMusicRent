"""Select public documentation without changing the underlying research sources.

The reviewed host/URL rules are editorial data in content/source-publication-policy.json.
Host matches are exact: a brand-looking name or an unreviewed subdomain is not proof
of authorship. Mixed retailers and shared hosting are approved by exact URL only.
The policy does not fetch URLs or infer relevance from a source title; relevance is
established when the source is attached to the authored page.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
from urllib.parse import urlsplit


POLICY_PATH = Path(__file__).resolve().parents[1] / 'content/source-publication-policy.json'
_POLICY = json.loads(POLICY_PATH.read_text(encoding='utf-8'))
POLICY_VERSION = _POLICY['version']
CLASS_REASONS = {name: value['reason'] for name, value in _POLICY['classes'].items()}
PUBLIC_CLASSES = frozenset(name for name, value in _POLICY['classes'].items() if value['public'])
_HOST_CLASSES = {host: kind for kind, hosts in _POLICY['host_groups'].items() for host in hosts}
_EXACT_URL_CLASSES = _POLICY['exact_url_rules']
_UNSAFE_CHARACTERS = re.compile(r'[\s\x00-\x1f\x7f\\]')


def _valid_url(url: object) -> tuple[str, str] | None:
    """Return the exact URL and normalized host, never repair an ambiguous URL."""
    if not isinstance(url, str) or not url or _UNSAFE_CHARACTERS.search(url):
        return None
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in {'http', 'https'} or not parsed.netloc or not parsed.hostname:
            return None
        if parsed.username is not None or parsed.password is not None:
            return None
        # A nonstandard port is a different service, outside reviewed website scope.
        if parsed.port not in {None, 443 if parsed.scheme == 'https' else 80}:
            return None
        host = parsed.hostname.encode('idna').decode('ascii').lower()
        if not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?', host):
            return None
        if '..' in host:
            return None
        return url, host
    except (ValueError, UnicodeError):
        return None


def source_class(source: object) -> str:
    """Classify one record for publication and the separate research audit."""
    if not isinstance(source, dict):
        return 'invalid'
    title = source.get('title')
    if not isinstance(title, str) or not title.strip():
        return 'invalid'
    parsed = _valid_url(source.get('url'))
    if parsed is None:
        return 'invalid'
    url, host = parsed
    return _EXACT_URL_CLASSES.get(url, _HOST_CLASSES.get(host, 'unreviewed'))


def public_sources(sources: list[dict]) -> list[dict]:
    """Return public documentation in authored order, removing only exact URL repeats.

    No network, mutation, title heuristics, arbitrary link limit or replacement links.
    A fresh record dictionary is returned; the original sources remain available to
    the editor and research ledger whether or not they are displayed on the website.
    """
    result = []
    seen = set()
    for source in sources:
        if source_class(source) not in PUBLIC_CLASSES:
            continue
        url = source['url']
        if url not in seen:
            result.append(dict(source))
            seen.add(url)
    return result
