#!/usr/bin/env python3
from pathlib import Path
from html import escape
import re
import shutil

SITE = Path("_site")

EXCLUDED_PREFIXES = (
    "archive/",
    "synthesis/",
    "synthesis-02/",
    "synthesis-03/",
    "lab/",
    "lite/",
    "details/",
    "usloviya/",
)

EXCLUDED_FILES = {"404.html"}

def clean_html_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", value).strip()

def title_for(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    title = clean_html_text(m.group(1)) if m else ""
    if "|" in title:
        title = title.split("|", 1)[0].strip()
    if "— ONTOS" in title:
        title = title.split("— ONTOS", 1)[0].strip()
    if title:
        return title
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    return clean_html_text(m.group(1)) if m else "Музыкальный прокат"

def public_url(rel: Path) -> str:
    p = rel.as_posix()
    if p == "index.html":
        return "/"
    if p.endswith("/index.html"):
        return "/" + p[:-len("index.html")]
    return "/" + p

def detail_url(rel: Path) -> str:
    p = rel.as_posix()
    if p == "index.html":
        return "/details/"
    if p.endswith("/index.html"):
        return "/details/" + p[:-len("index.html")]
    return "/details/" + p

def should_include(rel: Path) -> bool:
    p = rel.as_posix()
    if p in EXCLUDED_FILES:
        return False
    if any(p.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    return p.endswith(".html")

def add_noindex(html: str) -> str:
    if re.search(r'<meta[^>]+name=["\']robots["\']', html, re.I):
        return re.sub(
            r'<meta[^>]+name=["\']robots["\'][^>]*>',
            '<meta name="robots" content="noindex,follow">',
            html,
            count=1,
            flags=re.I,
        )
    return re.sub(
        r'(<meta[^>]+name=["\']viewport["\'][^>]*>)',
        r'\1\n  <meta name="robots" content="noindex,follow">',
        html,
        count=1,
        flags=re.I,
    )

def scale_link(href: str, icon: str, label: str) -> str:
    return f'<a class="minimal-scale-link" href="{href}"><span class="minimal-scale-icon" aria-hidden="true">{icon}</span><span>{label}</span></a>'

def utility_link(href: str, icon: str, label: str) -> str:
    return f'<a class="minimal-utility-link" href="{href}"><span class="minimal-utility-icon" aria-hidden="true">{icon}</span><span>{label}</span></a>'

def render(title: str, deep_url: str) -> str:
    title = escape(title)
    deep_url = escape(deep_url, quote=True)
    scale = "".join([
        scale_link("/usloviya/ot-pervogo-zanyatiya-do-solnoy-stseny/", "↗", "Ученические и профессиональные"),
        scale_link("/usloviya/ot-odnogo-instrumenta-do-komplektatsii-orkestra/", "◎", "От одного инструмента до комплектации оркестра"),
        scale_link("/usloviya/srok-arendy/", "◷", "Любой срок — от часа до года"),
        scale_link("/usloviya/stsena-zapis-semki/", "●", "Сцена, запись, съёмки"),
    ])
    utilities = "".join([
        utility_link("/usloviya/bez-zaloga/", "○", "Без залога"),
        utility_link("/usloviya/dostavka-po-moskve/", "⌂", "Доставка по Москве"),
        utility_link("/usloviya/dostavka-po-rossii/", "→", "Доставка по России"),
        utility_link("/usloviya/samovyvoz/", "⌖", "Самовывоз"),
    ])
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="{title}. Музыкальный прокат. Телефон, Telegram и WhatsApp.">
  <title>{title} | ONTOS.RENT</title>
  <link rel="stylesheet" href="/styles.css?v=20261003-minimal-03">
</head>
<body class="minimal-signal-page">
  <main class="minimal-signal">
    <p class="minimal-kicker">ПРОСТОЙ МУЗЫКАЛЬНЫЙ ПРОКАТ</p>
    <h1>{title}</h1>

    <div class="minimal-contact">
      <a class="minimal-channel-side" href="https://t.me/MUZPROKATMOSCOW" rel="noopener" aria-label="Telegram"><svg viewBox="0 0 48 48" aria-hidden="true"><path d="M7 23.5 39.5 9.8c1.6-.7 3 .4 2.5 2.2l-6.2 27.7c-.4 1.9-1.7 2.3-3.3 1.4l-9.6-7.1-4.7 4.5c-.5.5-1 .9-1.9.9l.7-9.8 17.9-16.2c.8-.7-.2-1.1-1.2-.4L11.6 26.9l-9.5-3c-2.1-.7-2.1-2 .4-3z"/></svg></a>
      <a class="minimal-phone" href="tel:+79690532096">+7 (969) 053-20-96</a>
      <a class="minimal-channel-side" href="https://wa.me/79690532096" rel="noopener" aria-label="WhatsApp"><svg viewBox="0 0 48 48" aria-hidden="true"><path d="M24 6C14.1 6 6 13.6 6 23c0 3.3 1 6.4 2.8 9.1L6 42l10.2-2.6A18.7 18.7 0 0 0 24 41c9.9 0 18-7.6 18-17S33.9 6 24 6zm0 31.7c-2.7 0-5.2-.7-7.4-2l-.5-.3-6 1.6 1.6-5.6-.3-.5A13.5 13.5 0 0 1 9.2 23c0-7.6 6.6-13.8 14.8-13.8S38.8 15.4 38.8 23 32.2 37.7 24 37.7zm8.1-10.3c-.4-.2-2.5-1.2-2.9-1.3-.4-.1-.7-.2-1 .2-.3.5-1.1 1.3-1.4 1.6-.3.3-.5.4-1 .1-2.7-1.2-4.5-2.2-6.3-5-.5-.8.5-.8 1.5-2.5.2-.3.1-.6 0-.9l-1.3-3c-.3-.7-.7-.7-1-.7h-.8c-.3 0-.8.1-1.2.6-.4.5-1.6 1.5-1.6 3.7s1.6 4.3 1.8 4.6c.2.3 3.2 5 7.9 6.8 4.7 1.8 4.7 1.2 5.6 1.1.9-.1 2.5-1 2.9-2 .4-1 .4-1.9.3-2-.1-.3-.5-.4-.9-.6z"/></svg></a>
    </div>

    <nav class="minimal-scale" aria-label="Диапазон проката">{scale}</nav>
    <nav class="minimal-utilities" aria-label="Условия и способы получения">{utilities}</nav>

    <p class="minimal-foot">
      Инструментальный фонд исполнительской музыки ·
      <a href="{deep_url}" style="color:inherit">Подробнее</a>
    </p>
  </main>
</body>
</html>
"""

sources = [p for p in SITE.rglob("*.html") if should_include(p.relative_to(SITE))]
count = 0
for source in sources:
    rel = source.relative_to(SITE)
    html = source.read_text(encoding="utf-8", errors="ignore")

    # Preserve the full page as the optional deep layer.
    deep_target = SITE / "details" / rel
    deep_target.parent.mkdir(parents=True, exist_ok=True)
    deep_target.write_text(add_noindex(html), encoding="utf-8")

    # Keep the original public URL, but replace its rendered artifact with the focused entry page.
    title = title_for(html)
    source.write_text(render(title, detail_url(rel)), encoding="utf-8")
    count += 1

print(f"Converted {count} public pages to focused entry pages; full versions preserved under /details/")
