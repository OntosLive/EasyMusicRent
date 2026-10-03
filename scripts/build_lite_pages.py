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
    return f'<a class="minimal-scale-link" href="{href}"><span>{label}</span></a>'

def utility_link(href: str, icon: str, label: str) -> str:
    return f'<a class="minimal-utility-link" href="{href}"><span>{label}</span></a>'

def render(title: str, deep_url: str) -> str:
    title = escape(title)
    deep_url = escape(deep_url, quote=True)
    scale = "".join([
        scale_link("/usloviya/ot-pervogo-zanyatiya-do-solnoy-stseny/", "↗", "Ученические и профессиональные"),
        scale_link("/usloviya/ot-odnogo-instrumenta-do-komplektatsii-orkestra/", "◎", "От единицы до комплектации оркестра"),
        scale_link("/usloviya/srok-arendy/", "◷", "Любой срок — от дня до года"),
        scale_link("/usloviya/stsena-zapis-semki/", "●", "Сцена · запись<br>Фото · реквизит"),
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

    <div class="minimal-contact-text">
      <a class="minimal-phone-text" href="tel:+79690532096">+7 (969) 053-20-96</a>
      <div class="minimal-channels-text" aria-label="Другие каналы связи">
        <a href="https://t.me/MUZPROKATMOSCOW" rel="noopener">Telegram</a>
        <span aria-hidden="true">·</span>
        <a href="https://wa.me/79690532096" rel="noopener">WhatsApp</a>
      </div>
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
