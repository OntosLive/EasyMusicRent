"""Compare representative public pairs and control files with the tested release."""
from __future__ import annotations
import argparse
import concurrent.futures
import datetime
import hashlib
import json
from pathlib import Path
import re
import urllib.request
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

DOMAIN = 'https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai'
FAMILIES = ['', 'arfy-liry', 'bayan-akkordeon', 'duhovye', 'elektronnye',
            'gitary', 'istoricheskie', 'klavishnye', 'redkie-eksperimentalnye',
            'shchipkovye', 'smychkovye', 'traditsionnye', 'udarnye', 'usiliteli-backline']
SOURCE_CASES = ['yamaha-clp735-v-arendu', 'shure-sm58-v-arendu',
                'weltmeister-perle-v-arendu', 'klavikord',
                'gitarnyy-kabinet-1x12-dlya-pervogo-opyta']


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def blocked(value):
    return bool({'noindex', 'none'} & set(re.split(r'[\s,;:]+', value.lower())))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--site', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--head-sha', required=True)
    parser.add_argument('--release-run', required=True)
    args = parser.parse_args()
    paths = []
    for slug in FAMILIES + SOURCE_CASES:
        paths.extend([(slug + '/' if slug else '') + 'index.html',
                      'details/' + (slug + '/' if slug else '') + 'index.html'])
    paths.extend(['usloviya/bez-zaloga/index.html', 'fond/index.html',
                  'robots.txt', 'sitemap.xml', 'assets/canon.css'])
    paths = list(dict.fromkeys(paths))
    assert all((args.site / path).is_file() for path in paths)
    started = utc()

    def get(relative):
        path = '/' + (relative.removesuffix('index.html') if relative.endswith('index.html') else relative)
        url = DOMAIN + path
        expected = (args.site / relative).read_bytes()
        result = {'path': relative, 'url': url, 'started_at': utc(),
                  'expected_sha256': hashlib.sha256(expected).hexdigest(), 'errors': []}
        try:
            request = urllib.request.Request(url, headers={
                'User-Agent': 'ONTOS.RENT publication verification', 'Cache-Control': 'no-cache'})
            with urllib.request.urlopen(request, timeout=25) as response:
                data = response.read()
                result.update(status=response.status, final_url=response.url,
                              content_type=response.headers.get('Content-Type'),
                              x_robots_tag=response.headers.get_all('X-Robots-Tag') or [],
                              bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                              byte_equal=data == expected)
            if result['status'] != 200:
                result['errors'].append('non-200 response')
            if not result['byte_equal']:
                result['errors'].append('public bytes differ from tested artifact')
                capture = args.output.parent / 'dual-index-live-mismatches' / relative
                capture.parent.mkdir(parents=True, exist_ok=True)
                capture.write_bytes(data)
                result['captured_mismatch'] = str(capture)
            if relative.endswith('.html'):
                doc = BeautifulSoup(data, 'html.parser')
                redirect = doc.find('meta', attrs={'http-equiv': re.compile('^refresh$', re.I)}) is not None
                canonicals = doc.find_all('link', rel='canonical')
                directives = [str(meta.get('content', '')) for meta in doc.find_all('meta')
                              if str(meta.get('name', '')).lower() in {'robots', 'googlebot', 'yandex', 'bingbot'}]
                source_blocks = doc.select('.sources')
                source = source_blocks[0] if source_blocks else None
                wrapper = doc.select_one('.page')
                children = wrapper.find_all(recursive=False) if wrapper else []
                placement = bool(source and len(children) > 1 and children[-1] is source
                                 and children[-2] is doc.select_one('.site-footer'))
                result.update(redirect=redirect, h1=doc.h1.get_text(' ', strip=True) if doc.h1 else None,
                              canonical=canonicals[0].get('href') if len(canonicals) == 1 else None,
                              own_canonical=len(canonicals) == 1 and canonicals[0].get('href') == url,
                              meta_robots=directives, sources_blocks=len(source_blocks),
                              documentation_links=[{'title': a.get_text(' ', strip=True), 'url': a['href']}
                                                   for a in source.select('a[href]')] if source else [],
                              documentation_at_bottom=placement if source else None,
                              documentation_collapsed=not source.has_attr('open') if source else None,
                              contact_present=doc.select_one('a[href="tel:+79690532096"]') is not None)
                if redirect:
                    if not any(blocked(value) for value in directives):
                        result['errors'].append('redirect lacks noindex')
                else:
                    if any(blocked(value) for value in directives + result['x_robots_tag']):
                        result['errors'].append('indexable page blocked by HTML or HTTP header')
                    if not result['own_canonical']:
                        result['errors'].append('invalid self canonical')
                    if not result['contact_present']:
                        result['errors'].append('missing contact')
                if source:
                    summary = source.find('summary', recursive=False)
                    if (len(source_blocks) != 1 or source.name != 'details' or source.has_attr('open')
                            or not summary or summary.get_text(' ', strip=True) != 'Документация'
                            or not placement or not path.startswith('/details/')):
                        result['errors'].append('documentation placement or state invalid')
            elif relative == 'sitemap.xml':
                sitemap = ET.fromstring(data)
                locations = [node.text for node in sitemap.iter() if node.tag.endswith('}loc')]
                result.update(sitemap_entries=len(locations), unique_entries=len(set(locations)),
                              editorial_entries=sum('/details/' in value for value in locations))
        except Exception as error:
            result.update(status=None, byte_equal=False, exception=str(error))
            result['errors'].append(str(error))
        result['finished_at'] = utc()
        return result

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(get, relative) for relative in paths]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            if len(results) % 10 == 0 or result['errors']:
                print(json.dumps({'checked': len(results), 'total': len(paths),
                                  'last': result['path'], 'errors': result['errors']}, ensure_ascii=False), flush=True)
    results.sort(key=lambda value: value['path'])
    failed = [value['path'] for value in results if value['errors']]
    report = {'head_sha': args.head_sha, 'release_run_id': args.release_run, 'started_at': started,
              'finished_at': utc(), 'domain': DOMAIN,
              'scope': 'Both pages of home and all 13 families; five documentation cases, one conditions page, '
                       'one redirect, and robots/sitemap/CSS. All local HTML is verified separately. '
                       'This is not an HTTP crawl of all 4046 HTML paths or a search-engine index inspection.',
              'requests': len(results), 'html_checked': sum(x['path'].endswith('.html') for x in results),
              'byte_equal': sum(bool(x.get('byte_equal')) for x in results), 'failed': failed,
              'all_passed': not failed, 'files': results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key != 'files'}, ensure_ascii=False), flush=True)
    raise SystemExit(bool(failed))


if __name__ == '__main__':
    main()
