#!/usr/bin/env python3
"""Notify Yandex about the freshly deployed canonical URLs via IndexNow."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = 'https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai'
ENDPOINT = 'https://yandex.com/indexnow'
NS = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}


def fetch(url: str, attempts: int = 6) -> bytes:
    error = None
    for attempt in range(attempts):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'ONTOS.RENT IndexNow/1.0'}), timeout=25) as response:
                if response.status != 200:
                    raise RuntimeError(f'{url}: HTTP {response.status}')
                return response.read()
        except (HTTPError, URLError, RuntimeError) as exc:
            error = exc
            if attempt + 1 < attempts:
                time.sleep(min(5 * (attempt + 1), 20))
    raise RuntimeError(f'Unable to fetch {url}: {error}')


def sitemap_urls(data: bytes) -> list[str]:
    root = ET.fromstring(data)
    urls = [node.text.strip() for node in root.findall('sm:url/sm:loc', NS) if node.text and node.text.strip()]
    host = urlsplit(DOMAIN).hostname
    if not urls or any(urlsplit(url).scheme != 'https' or urlsplit(url).hostname != host for url in urls):
        raise ValueError('Sitemap contains no URLs or a foreign/non-HTTPS URL')
    return urls


def submit(urls: list[str], key: str) -> int:
    key_location = f'{DOMAIN}/{key}.txt'
    live_key = fetch(key_location).decode('utf-8').strip()
    if live_key != key:
        raise RuntimeError('Published IndexNow key does not match repository key')
    payload = json.dumps({
        'host': urlsplit(DOMAIN).hostname,
        'key': key,
        'keyLocation': key_location,
        'urlList': urls,
    }).encode('utf-8')
    request = Request(ENDPOINT, data=payload, headers={
        'Content-Type': 'application/json; charset=utf-8',
        'User-Agent': 'ONTOS.RENT IndexNow/1.0',
    }, method='POST')
    try:
        with urlopen(request, timeout=30) as response:
            status = response.status
    except HTTPError as exc:
        status = exc.code
        if status not in {200, 202}:
            raise
    if status not in {200, 202}:
        raise RuntimeError(f'IndexNow returned HTTP {status}')
    print(json.dumps({'status': status, 'urls': len(urls), 'keyLocation': key_location}, ensure_ascii=False))
    return status


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--sitemap-url', default=DOMAIN + '/sitemap.xml')
    parser.add_argument('--key-file', type=Path, default=ROOT / 'content/indexnow-key.txt')
    args = parser.parse_args()
    key = args.key_file.read_text(encoding='utf-8').strip()
    if not (8 <= len(key) <= 128) or any(not (ch.isalnum() or ch == '-') for ch in key):
        raise ValueError('Invalid IndexNow key')
    submit(sitemap_urls(fetch(args.sitemap_url)), key)


if __name__ == '__main__':
    main()
