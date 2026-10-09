#!/usr/bin/env python3
"""Compile access/editorial pairs from preserved copy and authored records.

Legacy HTML supplies content, not competing layouts. Every active output uses
one frame, contact, footer and stylesheet. Internal sources are never published.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass, field
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup, Tag
from source_policy import public_sources

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = 'https://xn-----6kcabnjhfrnvokgficcuyowyell3c0le3a.xn--p1ai'
BRAND = 'ONTOS.RENT'
FUND = 'Инструментальный фонд исполнительской музыки'
PHONE = '+7 (969) 053-20-96'
TEL = 'tel:+79690532096'
TG = 'https://t.me/MUZPROKATMOSCOW'
WA = 'https://wa.me/79690532096'
INTERNAL = {'docs', 'data', 'scripts', 'tests', 'content', 'tools', 'ops', 'node_modules', 'prompts'}
EXPERIMENTS = {'archive', 'synthesis', 'synthesis-02', 'synthesis-03', 'lab', 'lite', 'plain-rental-01', 'details'}
RENT = re.compile(r'аренд|прокат|напрокат', re.I)
GUIDE = re.compile(r'^(?:как\b|какое\b|какой\b|что\b)|купить|выбрать|волчий тон', re.I)

@dataclass
class Page:
    slug: str
    search_title: str
    editorial_title: str
    description: str
    kicker: str
    intro: list[str] = field(default_factory=list)
    blocks: list[dict] = field(default_factory=list)
    quote: str = ''
    links: list[dict] = field(default_factory=list)
    parent: str = ''
    kind: str = 'entity'
    sources: list[dict] = field(default_factory=list)
    provenance: str = ''
    reviewed: bool = False

    @property
    def entry(self) -> str:
        return '/' if not self.slug else f'/{self.slug}/'

    @property
    def deep(self) -> str:
        return '/details/' if not self.slug else f'/details/{self.slug}/'


def text(node) -> str:
    return node.get_text(' ', strip=True) if node else ''


def fragment(node) -> str:
    return ''.join(str(x) for x in node.contents) if node else ''


def soup(value: str) -> BeautifulSoup:
    return BeautifulSoup(value, 'html.parser')


def meta(doc, name: str) -> str:
    item = doc.find('meta', attrs={'name': name})
    return str(item.get('content', '')).strip() if item else ''


def clean_title(value: str) -> str:
    return re.split(r'\s*\|\s*|\s*[—–]\s*ONTOS', value, maxsplit=1)[0].strip()


def url_slug(url: str) -> str:
    return urlsplit(url).path.strip('/').removeprefix('details/').removesuffix('/index.html')


def read_json(path: Path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def links_from(container) -> list[dict]:
    if container is None:
        return []
    result = []
    for item in container.find_all(['a', 'span'], recursive=False):
        label = text(item)
        if label:
            result.append({'label': label, 'href': item.get('href', '')})
    return result


def read_legacy(root: Path, metadata: dict) -> dict[str, Page]:
    pages = {}
    paths = [root / 'index.html', *sorted(root.glob('*/index.html'))]
    for path in paths:
        slug = '' if path.parent == root else path.parent.name
        if slug.startswith(('_', '.')) or slug in INTERNAL | EXPERIMENTS or slug == 'fond':
            continue
        doc = soup(path.read_text(encoding='utf-8'))
        if doc.find('meta', attrs={'http-equiv': re.compile('refresh', re.I)}):
            continue
        main = doc.find('main')
        if not main:
            raise ValueError(f'{path}: no content main')
        override = metadata.get(slug, {})
        declared = override.get('search_title') or meta(doc, 'search-title')
        original_title = clean_title(text(doc.title))
        if not declared:
            if len(original_title) <= 112 and (RENT.search(original_title) or GUIDE.search(original_title)):
                declared = original_title
            else:
                raise ValueError(f'{slug}: explicit search_title required: {original_title}')
        heading = main.select_one('h1') or main.select_one('h2')
        editorial = override.get('editorial_title') or text(heading)
        if not editorial:
            raise ValueError(f'{slug}: no editorial heading')
        kicker = text(main.select_one('.kicker, .query-kicker'))
        intro = []
        query_text = main.select_one('.query-text')
        if query_text:
            intro = [str(x) for x in query_text.children if isinstance(x, Tag)]
        else:
            deck = main.select_one('.deck')
            if deck:
                intro.append('<p>' + fragment(deck) + '</p>')
            thesis = main.select_one('.home-rent-thesis')
            if thesis:
                intro.extend(str(x) for x in thesis.find_all('p', recursive=False))
        blocks = []
        arguments = main.select_one('.cluster-arguments, .piano-arguments, .home-principles')
        if arguments:
            for item in arguments.find_all('article', recursive=False):
                blocks.append({'label': text(item.find('span')), 'title': text(item.find('h3')),
                               'paragraphs': [fragment(p) for p in item.find_all('p', recursive=False)]})
        nav = main.select_one('.cluster-family-grid, .home-family-grid')
        parent = override.get('parent', '')
        if not parent:
            parent_link = doc.select_one('.query-brand nav a[href]')
            if parent_link:
                parent = url_slug(parent_link['href'])
                if parent in EXPERIMENTS or parent.startswith('EasyMusicRent'):
                    parent = ''
        pages[slug] = Page(slug, declared, editorial, meta(doc, 'description'), kicker, intro,
                           blocks, text(main.find('blockquote')), links_from(nav), parent,
                           'guide' if GUIDE.search(declared) and not RENT.search(declared) else 'entity',
                           provenance=str(path.relative_to(root)))
    return pages


def merge_records(root: Path, pages: dict[str, Page]) -> None:
    for path in sorted((root / 'content' / 'sections').glob('*.json')):
        document = read_json(path, {})
        for record in document.get('pages', []):
            slug = record['slug']
            if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', slug):
                raise ValueError(f'invalid slug: {slug}')
            existing = pages.get(slug)
            if existing and record.get('mode') == 'enrich':
                for key in ('search_title', 'editorial_title', 'description', 'kicker', 'intro', 'blocks', 'quote', 'parent', 'sources'):
                    if key in record:
                        setattr(existing, key, record[key])
                existing.intro.extend(record.get('append_intro', []))
                existing.blocks.extend(record.get('append_blocks', []))
                existing.reviewed = True
                existing.provenance += ' + ' + str(path.relative_to(root))
            else:
                if existing:
                    raise ValueError(f'{path}: existing subject {slug} requires mode=enrich')
                required = ('search_title', 'editorial_title', 'description', 'kicker', 'intro', 'blocks')
                for key in required:
                    if not record.get(key):
                        raise ValueError(f'{slug}: missing authored {key}')
                pages[slug] = Page(**{k: record[k] for k in Page.__dataclass_fields__ if k in record and k not in {'provenance', 'reviewed'}},
                                   provenance=str(path.relative_to(root)), reviewed=True)
        for parent, replacements in document.get('navigation_replace', {}).items():
            if parent not in pages:
                raise ValueError(f'{path}: missing navigation parent {parent}')
            pages[parent].links = replacements
        for parent, additions in document.get('navigation', {}).items():
            if parent not in pages:
                raise ValueError(f'{path}: missing navigation parent {parent}')
            pages[parent].links.extend(additions)


def merge_legacy_navigation(root: Path, pages: dict[str, Page]) -> None:
    # Preserve the mature scene/model lists before retiring their old URLs.
    for path in sorted(root.glob('*/karta/index.html')):
        parent = path.parts[-3]
        if parent not in pages:
            continue
        doc = soup(path.read_text(encoding='utf-8'))
        for a in doc.select('.fund-scenes a[href]'):
            label = text(a.select_one('.fund-scene-title')) or text(a)
            pages[parent].links.append({'label': label, 'href': a['href']})


def normal_href(value: str) -> str:
    if value.startswith('/EasyMusicRent/'):
        value = value[len('/EasyMusicRent'):]
    return value


def connect(pages: dict[str, Page], aliases: dict[str, str]) -> None:
    for page in pages.values():
        if page.parent and page.parent not in pages:
            raise ValueError(f'{page.slug}: missing parent {page.parent}')
        unique = {}
        for item in page.links:
            href = normal_href(item.get('href', ''))
            if not href:
                unique['label:' + item['label']] = item
                continue
            slug = aliases.get(url_slug(href), url_slug(href))
            if slug not in pages:
                raise ValueError(f'{page.slug}: missing linked subject {href}')
            if slug == page.slug:
                continue
            unique[slug] = {'href': pages[slug].entry, 'label': item['label']}
        page.links = list(unique.values())
    for page in pages.values():
        if page.parent:
            parent = pages[page.parent]
            if not any(url_slug(x.get('href', '')) == page.slug for x in parent.links if x.get('href')):
                parent.links.append({'href': page.entry, 'label': page.search_title})
    for page in pages.values():
        active = {text(soup(x['label'])).casefold() for x in page.links if x.get('href')}
        page.links = [x for x in page.links if x.get('href') or x['label'].casefold() not in active]


def icon_paths(root: Path) -> tuple[str, str]:
    doc = soup((root / 'index.html').read_text(encoding='utf-8'))
    result = []
    for href in (TG, WA):
        link = doc.find('a', href=href)
        svg = link.find('svg') if link else None
        if not svg:
            raise ValueError('Approved source contact icons missing')
        svg.attrs = {'viewBox': '0 0 48 48', 'aria-hidden': 'true', 'focusable': 'false'}
        result.append(str(svg))
    return result[0], result[1]


def contact(icons: tuple[str, str], ruled: bool = False) -> str:
    cls = 'contact-block contact-block--ruled' if ruled else 'contact-block'
    return f'''<div class="{cls}"><div class="contact" aria-label="Связаться с нами">
<a class="contact-phone" href="{TEL}">{PHONE}</a><div class="contact-icons">
<a href="{TG}" aria-label="Telegram" rel="noopener">{icons[0]}</a>
<a href="{WA}" aria-label="WhatsApp" rel="noopener">{icons[1]}</a></div></div></div>'''


def footer(href: str, label: str, detail: str = '') -> str:
    more = f'<small>{escape(detail)}</small>' if detail else ''
    return f'''<footer class="site-footer"><span>{FUND}</span><a href="{escape(href, quote=True)}"><span>{escape(label)}</span>{more}</a></footer>'''


def masthead() -> str:
    return f'''<header class="masthead"><div class="meta"><a href="/">АРЕНДА-МУЗЫКАЛЬНЫХ-ИНСТРУМЕНТОВ.РФ</a><span>МОСКВА</span></div>
<div class="wordmark" aria-label="ONTOS.RENT">ONTOS<span>.</span>RENT</div><p class="tagline">{FUND}</p></header>'''


def title_style(value: str) -> str:
    # Bound the longest whole word rather than break it at arbitrary letters.
    words = re.findall(r'[^\s]+', value)
    widest = max((sum(1.02 if c in 'ЖШЩМЮЫW@' else .83 if c.isupper() else .75 if c in 'жшщмюы' else .64 for c in word) for word in words), default=1)
    return f'--word-em:{widest:.2f};--title-vw:{9.8 if len(value)>100 else 11.6 if len(value)>65 else 13}'


def frame(title: str, description: str, url: str, body: str, css_version: str, *, deep: bool, noindex: bool = False) -> str:
    robots = '<meta name="robots" content="noindex,follow">' if noindex else ''
    return f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title><meta name="description" content="{escape(description, quote=True)}">{robots}
<link rel="canonical" href="{DOMAIN}{url}"><link rel="stylesheet" href="/assets/canon.css?v={css_version}"></head>
<body class="{'deep-page' if deep else 'entry-page'}"><div class="page">{body}</div></body></html>'''


def grid(items: list[dict], pages: dict[str, Page]) -> str:
    def cell(item: dict) -> str:
        href = item.get('href')
        label = item['label']
        if href:
            target = pages.get(url_slug(href))
            if target and len(label)>72:
                label = target.search_title
            return f'<a href="{escape(href, quote=True)}"><span style="{title_style(label)}">{escape(label)}</span></a>'
        return f'<span class="pending"><span style="{title_style(label)}">{escape(label)}</span></span>'
    if not items:
        return ''
    if len(items)<=16:
        return '<nav id="razdely" class="category-grid" aria-label="Инструменты и варианты">' + ''.join(cell(x) for x in items) + '</nav>'
    groups = {}
    for item in items:
        label = item['label']
        brand = next((x for x in ('Yamaha','Casio','Roland','Kawai') if x.casefold() in label.casefold()), '')
        key = brand or ('Размеры и удобство' if re.search(r'размер|рост|рук|мензур|[124]/[2486]',label,re.I) else 'Практика и выбор')
        groups.setdefault(key, []).append(item)
    return '<section id="razdely" class="category-groups" aria-label="Инструменты и варианты">' + ''.join('<details><summary>'+escape(name)+'</summary><nav class="category-grid">'+''.join(cell(x) for x in values)+'</nav></details>' for name,values in groups.items())+'</section>'


def render_deep(page: Page, pages: dict[str, Page], icons, version: str) -> str:
    heading = f'<p class="kicker">{escape(page.kicker)}</p><h1 style="{title_style(page.editorial_title)}">{escape(page.editorial_title)}</h1>'
    intro = '<div class="intro">' + ''.join(page.intro) + '</div>'
    nav = grid(page.links, pages)
    cards = ''.join('<article><p class="kicker">'+escape(x['label'])+'</p><h2>'+escape(x['title'])+'</h2>'+''.join('<p>'+p+'</p>' for p in x['paragraphs'])+'</article>' for x in page.blocks)
    quote = '<blockquote>'+escape(page.quote)+'</blockquote>' if page.quote else ''
    sources = ''
    documentation = public_sources(page.sources)
    if documentation:
        sources = '<details class="sources"><summary>Документация</summary><ul>'+''.join(f'<li><a href="{escape(x["url"],quote=True)}" rel="noopener">{escape(x["title"])}</a></li>' for x in documentation)+'</ul></details>'
    if page.parent:
        parent = pages[page.parent]
        link = footer(parent.deep, parent.editorial_title)
    elif page.slug:
        link = footer('/details/#razdely', 'Все инструменты')
    else:
        link = footer('#razdely', 'Инструменты', 'Подробнее')
    body = masthead()+'<main class="editorial">'+heading+intro+nav+('<section class="arguments">'+cards+'</section>' if cards else '')+quote+contact(icons)+'</main>'+link+sources
    return frame(page.editorial_title, page.description, page.deep, body, version, deep=True)


def render_entry(page: Page, icons, version: str) -> str:
    ranges = [('/usloviya/ot-pervogo-zanyatiya-do-solnoy-stseny/','Ученические и профессиональные'),('/usloviya/ot-odnogo-instrumenta-do-komplektatsii-orkestra/','От единицы до комплектации оркестра'),('/usloviya/srok-arendy/','Любой срок: от дня до года'),('/usloviya/stsena-zapis-semki/','Сцена · запись<br>Фото · реквизит')]
    utilities = [('/usloviya/bez-zaloga/','Без залога'),('/usloviya/dostavka-po-moskve/','Доставка по Москве'),('/usloviya/dostavka-po-rossii/','Доставка по России'),('/usloviya/samovyvoz/','Самовывоз')]
    body = '<main><p class="kicker">ПРОСТОЙ МУЗЫКАЛЬНЫЙ ПРОКАТ</p><h1 style="'+title_style(page.search_title)+'">'+escape(page.search_title)+'</h1>'+contact(icons,True)
    body += '<nav class="range-grid" aria-label="Диапазон проката">'+''.join(f'<a href="{u}"><span>{v}</span></a>' for u,v in ranges)+'</nav>'
    body += '<nav class="utilities" aria-label="Условия и способы получения">'+''.join(f'<a href="{u}">{v}</a>' for u,v in utilities)+'</nav></main>'+footer(page.deep,'Подробнее')
    return frame(page.search_title, page.search_title+'. '+page.description, page.entry, body, version, deep=False)


def redirect(target: str) -> str:
    safe = escape(target, quote=True)
    return f'<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="robots" content="noindex,follow"><meta http-equiv="refresh" content="0; url={safe}"><link rel="canonical" href="{DOMAIN}{safe}"><title>Переход | {BRAND}</title></head><body><a href="{safe}">Перейти в раздел</a></body></html>'


def write(output: Path, url: str, value: str) -> None:
    path = output / url.lstrip('/') / 'index.html'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding='utf-8')


def build(root: Path, output: Path) -> dict:
    if output.resolve()==root.resolve() or output.resolve()==Path('/'):
        raise ValueError('Build output must be separate from sources')
    metadata = read_json(root/'content/legacy-metadata.json',{})
    aliases = read_json(root/'content/aliases.json',{})
    pages = read_legacy(root, metadata)
    merge_records(root,pages)
    merge_legacy_navigation(root,pages)
    for alias, target in aliases.items():
        if target not in pages:
            raise ValueError(f'Alias {alias}: missing target {target}')
        pages.pop(alias,None)
    connect(pages,aliases)
    icons = icon_paths(root)
    output.mkdir(parents=True,exist_ok=True)
    (output/'.nojekyll').write_text('',encoding='utf-8')
    for directory in INTERNAL | (EXPERIMENTS - {'details'}):
        shutil.rmtree(output/directory,ignore_errors=True)
    for artifact in ('README.md', 'Gemfile', 'Gemfile.lock', 'requirements-site.txt'):
        (output/artifact).unlink(missing_ok=True)
    asset = root/'assets/canon.css'
    (output/'assets').mkdir(exist_ok=True)
    shutil.copyfile(asset,output/'assets/canon.css')
    version = sha256(asset.read_bytes()).hexdigest()[:12]
    for page in pages.values():
        if len(page.search_title)>120:
            raise ValueError(f'{page.slug}: search title is not a short request')
        write(output,page.entry,render_entry(page,icons,version))
        write(output,page.deep,render_deep(page,pages,icons,version))
    for path in root.glob('usloviya/*/index.html'):
        if path.parent.name in {'masshtab','dostavka'}:
            target='/usloviya/'+('ot-odnogo-instrumenta-do-komplektatsii-orkestra' if path.parent.name=='masshtab' else 'dostavka-po-rossii')+'/'
            write(output,'/usloviya/'+path.parent.name+'/',redirect(target))
            continue
        doc=soup(path.read_text(encoding='utf-8'))
        heading=text(doc.find('h1'))
        content=fragment(doc.select_one('.deck'))
        url='/usloviya/'+path.parent.name+'/'
        body='<main><p class="kicker">'+escape(text(doc.select_one('.minimal-kicker')))+'</p><h1 style="'+title_style(heading)+'">'+escape(heading)+'</h1><div class="intro"><p>'+content+'</p></div>'+contact(icons,True)+'</main>'+footer('/','На главную')
        write(output,url,frame(heading,meta(doc,'description'),url,body,version,deep=False))
    for path in root.glob('*/karta/index.html'):
        slug=path.parts[-3]
        if slug in pages:
            target=pages[slug].deep+('#razdely' if pages[slug].links else '')
            write(output,'/'+slug+'/karta/',redirect(target))
            write(output,'/details/'+slug+'/karta/',redirect(target))
    write(output,'/fond/',redirect('/details/#razdely'))
    write(output,'/details/fond/',redirect('/details/#razdely'))
    for alias,target in aliases.items():
        write(output,'/'+alias+'/',redirect(pages[target].entry))
        write(output,'/details/'+alias+'/',redirect(pages[target].deep))
    namespace='http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('',namespace)
    sitemap=ET.Element('{'+namespace+'}urlset')
    for page in pages.values():
        for url in (page.entry, page.deep):
            node=ET.SubElement(sitemap,'{'+namespace+'}url')
            ET.SubElement(node,'{'+namespace+'}loc').text=DOMAIN+url
    ET.ElementTree(sitemap).write(output/'sitemap.xml',encoding='utf-8',xml_declaration=True)
    (output/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+DOMAIN+'/sitemap.xml\n',encoding='utf-8')
    return {'source_pages':len(pages),'public_pair_pages':len(pages)*2,'conditions':len(list(root.glob('usloviya/*/index.html')))-2,'css_version':version,'authored_records':sum(p.reviewed for p in pages.values()),'pages':[{'slug':p.slug,'entry_title':p.search_title,'editorial_title':p.editorial_title,'parent':p.parent,'links':len(p.links),'source':p.provenance} for p in pages.values()]}


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--output',type=Path,default=ROOT/'_site')
    parser.add_argument('--report',type=Path,default=ROOT/'_audit/build.json')
    args=parser.parse_args()
    result=build(args.root,args.output)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='pages'},ensure_ascii=False))

if __name__=='__main__':
    main()
