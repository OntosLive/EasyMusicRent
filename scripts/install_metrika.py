#!/usr/bin/env python3
"""Add one visually invisible Yandex Metrika counter to each live HTML document.

This post-build step intentionally does not alter the canonical source compiler.
Technical HTML redirects are preserved exactly as generated.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

COUNTER_ID = 113536720
MARKER = '<!-- Yandex.Metrika counter -->'
TAG_INIT = f'ym({COUNTER_ID}, "init"'
FALLBACK_URL = f'https://mc.yandex.ru/watch/{COUNTER_ID}'

# No visible informer, session recording, or e-commerce collection.
HEAD_CODE = f'''\n{MARKER}
<script type="text/javascript">
(function(m,e,t,r,i,k,a){{
  m[i]=m[i]||function(){{(m[i].a=m[i].a||[]).push(arguments)}};
  m[i].l=1*new Date();
  for(var j=0;j<document.scripts.length;j++){{if(document.scripts[j].src===r){{return;}}}}
  k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
}})(window,document,"script","https://mc.yandex.ru/metrika/tag.js","ym");
{TAG_INIT},{{clickmap:true,trackLinks:true,accurateTrackBounce:true}});
</script>
<!-- /Yandex.Metrika counter -->
'''
FALLBACK = f'<noscript><div><img src="{FALLBACK_URL}" style="position:absolute;left:-9999px" alt=""></div></noscript>'
REFRESH = re.compile(r'<meta\b[^>]*\bhttp-equiv\s*=\s*["\']?refresh\b', re.I)
HEAD_CLOSE = re.compile(r'</head\s*>', re.I)
BODY_OPEN = re.compile(r'<body(?:\s[^>]*)?>', re.I)


def is_redirect(html: str) -> bool:
    return bool(REFRESH.search(html))


def counter_errors(html: str) -> list[str]:
    checks = (
        ('script marker', html.count(MARKER)),
        ('counter init', html.count(TAG_INIT)),
        ('fallback image', html.count(FALLBACK_URL)),
        ('tag loader', html.count('https://mc.yandex.ru/metrika/tag.js')),
    )
    return [f'{name}: expected 1, found {count}' for name, count in checks if count != 1]


def inject_html(html: str) -> str:
    """Insert analytics without changing any existing markup or visible text."""
    if is_redirect(html):
        return html
    if not counter_errors(html):
        return html
    if (MARKER in html or TAG_INIT in html or FALLBACK_URL in html
            or 'mc.yandex.ru/metrika/tag.js' in html):
        raise ValueError('Existing or incomplete Yandex Metrika installation')
    head = HEAD_CLOSE.search(html)
    body = BODY_OPEN.search(html)
    if not head or not body or head.start() > body.start():
        raise ValueError('Expected a complete HTML head and body')
    html = html[:head.start()] + HEAD_CODE + html[head.start():]
    body = BODY_OPEN.search(html)
    html = html[:body.end()] + FALLBACK + html[body.end():]
    if counter_errors(html):
        raise ValueError('Counter injection verification failed')
    return html


def process_site(site: Path, *, check: bool = False) -> dict:
    if not site.is_dir():
        raise ValueError(f'Site directory not found: {site}')
    documents = redirects = changed = 0
    problems = []
    for path in sorted(site.rglob('*.html')):
        original = path.read_text(encoding='utf-8')
        if is_redirect(original):
            redirects += 1
            if MARKER in original:
                problems.append(f'{path.relative_to(site)}: counter on redirect')
            continue
        documents += 1
        if check:
            errors = counter_errors(original)
            if errors:
                problems.append(f'{path.relative_to(site)}: {", ".join(errors)}')
        else:
            updated = inject_html(original)
            if updated != original:
                path.write_text(updated, encoding='utf-8')
                changed += 1
    if not documents:
        problems.append('No non-redirect HTML documents found')
    result = {
        'counter_id': COUNTER_ID,
        'documents': documents,
        'redirects': redirects,
        'changed': changed,
        'mode': 'check' if check else 'install',
        'errors': len(problems),
        'examples': problems[:10],
    }
    if problems:
        raise ValueError(json.dumps(result, ensure_ascii=False))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--site', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print(json.dumps(process_site(args.site, check=args.check), ensure_ascii=False))


if __name__ == '__main__':
    main()
