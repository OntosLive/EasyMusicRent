"""Independent static-site compiler for verified specialist contact offers.

No API, CMS, forms or checkout. All strings come from an approved site brief.
Production requires explicit verification gates; drafts cannot be indexed.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
from urllib.parse import urlsplit
import json
import re
import shutil
import xml.etree.ElementTree as ET

SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
TEL = re.compile(r"\+\d{8,15}\Z")
ALLOWED_STATUS = {"draft", "publish"}
RELEASE_GATES = (
    "executor_verified",
    "contact_verified",
    "offer_reviewed",
    "legal_reviewed",
)


def _required_text(data: dict, name: str, min_chars: int = 12) -> str:
    value = data.get(name)
    if not isinstance(value, str) or len(value.strip()) < min_chars:
        raise ValueError(f"Required meaningful text: {name}")
    return value.strip()


def validate(config: dict) -> dict:
    """Validate actual capability and distinct human situations before building."""
    if not isinstance(config, dict):
        raise ValueError("Site config must be a JSON object")
    state = config.get("status")
    if state not in ALLOWED_STATUS:
        raise ValueError("status must be draft or publish")
    _required_text(config, "brand", 3)
    _required_text(config, "specialization", 15)
    _required_text(config, "intro", 40)
    _required_text(config, "limitations", 30)
    domain = _required_text(config, "domain", 12).rstrip("/")
    parsed = urlsplit(domain)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.port not in (None, 443)
            or parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password):
        raise ValueError("domain must be an https origin without path, query or credentials")
    contact = config.get("contact")
    if not isinstance(contact, dict):
        raise ValueError("contact must be an object")
    _required_text(contact, "display", 7)
    phone = _required_text(contact, "phone", 9)
    if not TEL.fullmatch(phone):
        raise ValueError("contact.phone must be E.164: + followed by 8-15 digits")
    for key in ("telegram", "whatsapp"):
        if contact.get(key):
            u = urlsplit(contact[key])
            allowed_hosts = {"t.me"} if key == "telegram" else {"wa.me", "api.whatsapp.com"}
            if u.scheme != "https" or u.hostname not in allowed_hosts:
                raise ValueError(f"Unsafe or unsupported {key} URL")
    pages = config.get("pages")
    if not isinstance(pages, list) or not 1 <= len(pages) <= 40:
        raise ValueError("Provide 1-40 distinct human situations, not keyword permutations")
    slugs = set()
    titles = set()
    situations = set()
    for page in pages:
        if not isinstance(page, dict):
            raise ValueError("pages must contain objects")
        slug = _required_text(page, "slug", 3)
        if not SLUG.fullmatch(slug) or slug in slugs:
            raise ValueError(f"Invalid or repeated slug: {slug}")
        slugs.add(slug)
        title = _required_text(page, "title", 12)
        if title.casefold() in titles:
            raise ValueError(f"Repeated page title: {title}")
        titles.add(title.casefold())
        for key, min_len in (("situation", 65), ("difference", 65),
                             ("route", 65), ("question", 20)):
            _required_text(page, key, min_len)
        scene = page["situation"].strip().casefold()
        if scene in situations:
            raise ValueError(f"Duplicate human situation: {slug}")
        situations.add(scene)
    if state == "publish":
        if parsed.hostname.endswith(".invalid") or parsed.hostname in {"localhost", "example.com"}:
            raise ValueError("A real verified domain is required for publication")
        for gate in RELEASE_GATES:
            if config.get(gate) is not True:
                raise ValueError(f"Publication gate not confirmed: {gate}")
        _required_text(config, "operator_name", 4)
        _required_text(config, "privacy_notice", 30)
    return config


def _link(href: str, label: str, css_class: str = "") -> str:
    return f'<a class="{escape(css_class, quote=True)}" href="{escape(href, quote=True)}">{escape(label)}</a>'


def _contact(data: dict) -> str:
    v = data["contact"]
    links = [_link(f'tel:{v["phone"]}', v["display"], "phone")]
    for key, label in (("telegram", "Telegram"), ("whatsapp", "WhatsApp")):
        if v.get(key):
            links.append(_link(v[key], label, "contact-secondary"))
    return '<nav class="contacts" aria-label="Связаться">' + "".join(links) + '</nav>'


def _frame(data: dict, title: str, route: str, body: str) -> str:
    state = data["status"]
    noindex = '<meta name="robots" content="noindex,nofollow">' if state == "draft" else ""
    canon = f'<link rel="canonical" href="{escape(data["domain"].rstrip("/") + route, quote=True)}">' if state == "publish" else ""
    heading = escape(title + " | " + data["brand"])
    return ('<!doctype html><html lang="ru"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{heading}</title>{noindex}{canon}'
            '<link rel="stylesheet" href="/assets/site.css"></head><body>'
            f'<div class="wrap"><header>{_link("/", data["brand"], "wordmark")}'
            f'<span class="specialization">{escape(data["specialization"])}</span></header>'
            + ('<p class="draft-banner">ПРОЕКТ: проверка предложения. Публикация и наличие исполнителя не подтверждены.</p>' if state == "draft" else '')
            + body + '<footer><p>Специализированный контакт. Конкретные условия уточняются напрямую.</p>'
            + (_link("/privacy/", "Обработка данных") if state == "publish" else "")
            + '</footer></div></body></html>')


def _homepage(data: dict) -> str:
    cards = []
    for page in data["pages"]:
        cards.append('<li><article><h2>' + _link('/' + page['slug'] + '/', page['title'])
                     + '</h2><p>' + escape(page['situation']) + '</p></article></li>')
    body = ('<main><p class="eyebrow">УЗКАЯ СПЕЦИАЛИЗАЦИЯ</p>'
            f'<h1>{escape(data["brand"])}</h1><p class="lead">{escape(data["intro"])}</p>'
            + _contact(data) + '<h2>С какими ситуациями обращаются</h2><ul class="cards">'
            + ''.join(cards) + '</ul><section><h2>Что важно уточнить</h2><p>'
            + escape(data['limitations']) + '</p></section></main>')
    return _frame(data, data['specialization'], '/', body)


def _scene(data: dict, page: dict) -> str:
    body = ('<main><p class="eyebrow">ЗАПРОС И ПОДБОР МАРШРУТА</p>'
            + f'<h1>{escape(page["title"])}</h1>'
            + f'<section><h2>Ситуация</h2><p>{escape(page["situation"])}</p></section>'
            + f'<section><h2>Что важно различить</h2><p>{escape(page["difference"])}</p></section>'
            + f'<section><h2>Как можно двигаться</h2><p>{escape(page["route"])}</p></section>'
            + f'<p class="question">{escape(page["question"])}</p>'
            + _contact(data)
            + f'<section class="limitations"><h2>Граница предложения</h2><p>{escape(data["limitations"])}</p></section>'
            + '<p>' + _link('/', 'Все направления') + '</p></main>')
    return _frame(data, page['title'], '/' + page['slug'] + '/', body)


def _write(root: Path, route: str, text: str) -> None:
    path = root / route.lstrip('/') / 'index.html'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def build(config: dict, output: Path, style: Path) -> dict:
    data = validate(config)
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output directory must be empty, to avoid stale published pages")
    output.mkdir(parents=True, exist_ok=True)
    (output / 'assets').mkdir(exist_ok=True)
    shutil.copyfile(style, output / 'assets' / 'site.css')
    _write(output, '/', _homepage(data))
    routes = ['/']
    for page in data['pages']:
        url = '/' + page['slug'] + '/'
        _write(output, url, _scene(data, page))
        routes.append(url)
    if data['status'] == 'publish':
        notice = ('<main><h1>Обработка данных</h1><p>'
                  + escape(data['privacy_notice']) + '</p><p>Оператор: '
                  + escape(data['operator_name']) + '</p></main>')
        _write(output, '/privacy/', _frame(data, 'Обработка данных', '/privacy/', notice))
        routes.append('/privacy/')
        ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
        urlset = ET.Element('urlset', {'xmlns': ns})
        for route in routes:
            ET.SubElement(ET.SubElement(urlset, 'url'), 'loc').text = data['domain'].rstrip('/') + route
        (output / 'sitemap.xml').write_bytes(ET.tostring(urlset, encoding='utf-8', xml_declaration=True))
        (output / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: ' + data['domain'].rstrip('/') + '/sitemap.xml\n', encoding='utf-8')
    else:
        (output / 'robots.txt').write_text('User-agent: *\nDisallow: /\n', encoding='utf-8')
    (output / '.nojekyll').write_text('', encoding='utf-8')
    return {'site': data['brand'], 'status': data['status'], 'html_pages': len(routes),
            'sitemap': data['status'] == 'publish', 'verified': data['status'] == 'publish',
            'contact_only': True}


def build_from_json(path: Path, output: Path) -> dict:
    config = json.loads(Path(path).read_text(encoding='utf-8'))
    return build(config, output, Path(__file__).with_name('site.css'))
