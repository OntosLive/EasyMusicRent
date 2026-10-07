#!/usr/bin/env python3
"""Audit page-role links and rental-language distribution across the built site."""
from __future__ import annotations
import argparse, json, re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup

RENT = re.compile(r'\b(?:аренд\w*|прокат\w*|напрокат)\b', re.I)
RENT_A = re.compile(r'\bаренд\w*\b', re.I)
RENT_P = re.compile(r'\b(?:прокат\w*|напрокат)\b', re.I)
TEMP = re.compile(r'\b(?:временн\w*|срок\w*|период\w*|взять|берём|берут|доступ\w*)\b', re.I)

def clean_text(node):
    if node is None:
        return ''
    for tag in node.select('script,style,details.sources'):
        tag.decompose()
    return node.get_text(' ', strip=True)

def route_for(path: Path, site: Path) -> str:
    rel=path.relative_to(site).as_posix()
    if rel=='index.html': return '/'
    return '/'+rel[:-len('index.html')]

def normalized_target(current: str, href: str) -> tuple[str,str]:
    parsed=urlsplit(href)
    if parsed.scheme or parsed.netloc:
        return '', parsed.fragment
    path=parsed.path
    if not path:
        path=current
    elif not path.startswith('/'):
        base=current.rsplit('/',2)[0]+'/'
        path=base+path
    while '//' in path: path=path.replace('//','/')
    return path, parsed.fragment

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--site',type=Path,required=True)
    ap.add_argument('--report',type=Path,required=True)
    args=ap.parse_args()
    site=args.site
    rows=[]
    self_links=[]
    layer_counts=Counter()
    sitemap=ET.parse(site/'sitemap.xml').getroot()
    namespace={'sm':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    detail_routes=sorted(
        urlsplit(loc.text.strip()).path
        for loc in sitemap.findall('sm:url/sm:loc', namespace)
        if loc.text and urlsplit(loc.text.strip()).path.startswith('/details/')
    )
    for route in detail_routes:
        path = site / route.strip('/') / 'index.html'
        doc=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
        main_node=doc.select_one('main.editorial') or doc.find('main')
        body=clean_text(main_node)
        h1=(doc.find('h1').get_text(' ',strip=True) if doc.find('h1') else '')
        entry_route='/' if route=='/details/' else route.replace('/details/','/',1)
        entry_path=site/entry_route.strip('/')/'index.html'
        if entry_route=='/': entry_path=site/'index.html'
        entry_title=''
        if entry_path.exists():
            edoc=BeautifulSoup(entry_path.read_text(encoding='utf-8'),'html.parser')
            if edoc.find('h1'): entry_title=edoc.find('h1').get_text(' ',strip=True)
        links=[]
        for a in doc.find_all('a',href=True):
            href=a['href']
            target,fragment=normalized_target(route,href)
            if not target: continue
            if target==route:
                self_links.append({'route':route,'href':href,'label':a.get_text(' ',strip=True)})
            if target.startswith('/details/'): layer_counts['deep_to_deep']+=1
            elif target.startswith('/usloviya/'): layer_counts['deep_to_conditions']+=1
            elif target.startswith('/'): layer_counts['deep_to_entry_or_other']+=1
            links.append(href)
        rows.append({
            'route':route,'entry_route':entry_route,'entry_title':entry_title,'editorial_title':h1,
            'words':len(body.split()),'rental_mentions':len(RENT.findall(body)),
            'arenda_mentions':len(RENT_A.findall(body)),'prokat_mentions':len(RENT_P.findall(body)),
            'temporary_mentions':len(TEMP.findall(body)),
            'rental_in_h1':bool(RENT.search(h1)),
            'entry_uses_arenda':bool(RENT_A.search(entry_title)),
            'entry_uses_prokat':bool(RENT_P.search(entry_title)),
        })
    summary={
        'detail_pages':len(rows),
        'with_any_rental_word':sum(r['rental_mentions']>0 for r in rows),
        'without_rental_word':sum(r['rental_mentions']==0 for r in rows),
        'without_rental_but_with_temporary_language':sum(r['rental_mentions']==0 and r['temporary_mentions']>0 for r in rows),
        'without_rental_or_temporary_language':sum(r['rental_mentions']==0 and r['temporary_mentions']==0 for r in rows),
        'with_arenda':sum(r['arenda_mentions']>0 for r in rows),
        'with_prokat':sum(r['prokat_mentions']>0 for r in rows),
        'with_both':sum(r['arenda_mentions']>0 and r['prokat_mentions']>0 for r in rows),
        'rental_in_editorial_h1':sum(r['rental_in_h1'] for r in rows),
        'entry_title_arenda':sum(r['entry_uses_arenda'] for r in rows),
        'entry_title_prokat':sum(r['entry_uses_prokat'] for r in rows),
        'self_links':len(self_links),
        'layer_links':dict(layer_counts),
    }
    report={
        'summary':summary,
        'self_links':self_links,
        'no_rental_or_temporary':[r for r in rows if r['rental_mentions']==0 and r['temporary_mentions']==0],
        'rental_in_editorial_h1':[r for r in rows if r['rental_in_h1']],
        'rows':rows,
    }
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print('SELF_LINKS')
    for x in self_links[:50]:
        print(json.dumps(x,ensure_ascii=False))
    print('NO_RENTAL_OR_TEMPORARY_SAMPLE')
    for x in report['no_rental_or_temporary'][:80]:
        print(json.dumps({k:x[k] for k in ('route','entry_title','editorial_title','words')},ensure_ascii=False))
if __name__=='__main__': main()
