#!/usr/bin/env python3
from pathlib import Path
from html import escape
import re

SITE = Path("_site")

EXCLUDED_PREFIXES = (
    "archive/",
    "synthesis/",
    "synthesis-02/",
    "synthesis-03/",
    "lab/",
    "lite/",
)

EXCLUDED_FILES = {
    "404.html",
}

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

def original_url(rel: Path) -> str:
    p = rel.as_posix()
    if p == "index.html":
        return "/"
    if p.endswith("/index.html"):
        return "/" + p[:-len("index.html")]
    return "/" + p

def should_include(rel: Path) -> bool:
    p = rel.as_posix()
    if p in EXCLUDED_FILES:
        return False
    if any(p.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    return p.endswith(".html")

def render(title: str, detail_url: str) -> str:
    title = escape(title)
    detail_url = escape(detail_url, quote=True)
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="robots" content="noindex,follow">
  <title>{title} | ONTOS.RENT</title>
  <link rel="stylesheet" href="/styles.css?v=20261003-minimal-02">
</head>
<body class="minimal-signal-page">
  <main class="minimal-signal">
    <p class="minimal-kicker">ПРОСТОЙ МУЗЫКАЛЬНЫЙ ПРОКАТ</p>
    <h1>{title}</h1>

    <div class="minimal-contact">
      <a class="minimal-phone" href="tel:+79690532096">+7 (969) 053-20-96</a>
      <div class="minimal-channels">
        <a href="https://t.me/MUZPROKATMOSCOW" rel="noopener">Telegram</a>
        <span>·</span>
        <a href="https://wa.me/79690532096" rel="noopener">WhatsApp</a>
      </div>
    </div>

    <p class="minimal-foot">
      Инструментальный фонд исполнительской музыки ·
      <a href="{detail_url}" style="color:inherit">Подробнее</a>
    </p>
  </main>
</body>
</html>
"""

count = 0
for source in SITE.rglob("*.html"):
    rel = source.relative_to(SITE)
    if not should_include(rel):
        continue

    html = source.read_text(encoding="utf-8", errors="ignore")
    title = title_for(html)
    target = SITE / "lite" / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(title, original_url(rel)), encoding="utf-8")
    count += 1

print(f"Built {count} lightweight entry pages under /lite/")
