#!/usr/bin/env python3
"""Collect Yandex Wordstat query branches for ONTOS.RENT.

The collector intentionally ignores Wordstat associations/"similar queries".
We generate our own search branches from the site's instrument entities and
allowed scenes, ask Wordstat only for results containing those phrases, then
deduplicate the returned field.

Outputs:
- data/generated_seeds.csv
- data/wordstat_raw.csv
- data/query_candidates.csv

The curated backlog data/queries.csv is never overwritten automatically.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

API_URL = "https://searchapi.api.cloud.yandex.net/v2/wordstat/topRequests"


def truthy(value: str) -> bool:
    return str(value).strip().lower() not in {"", "0", "false", "no", "off"}


def norm(text: str) -> str:
    text = text.casefold().replace("ё", "е")
    text = re.sub(r"[^0-9a-zа-я]+", " ", text)
    return " ".join(text.split())


def read_entities(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def seed_row(entity: dict, seed: str, scene: str) -> dict:
    return {
        "seed": seed.strip(),
        "entity": entity["entity"].strip(),
        "cluster": entity["cluster"].strip(),
        "scene": scene,
        "city": entity["city"].strip(),
        "region_id": entity["region_id"].strip(),
        "max_results": "2000",
    }


def generate_seeds(entities: List[dict]) -> List[dict]:
    seeds: List[dict] = []

    for e in entities:
        x = e["entity"].strip()
        city = e["city"].strip()

        if truthy(e.get("allow_rent", "")):
            seeds += [
                seed_row(e, f"аренда {x}", "rent"),
                seed_row(e, f"{x} в аренду", "rent"),
                seed_row(e, f"аренда {x} {city}", "rent-city"),
            ]

        if truthy(e.get("allow_prokat", "")):
            seeds += [
                seed_row(e, f"прокат {x}", "prokat"),
                seed_row(e, f"{x} напрокат", "prokat"),
                seed_row(e, f"прокат {x} {city}", "prokat-city"),
            ]

        if truthy(e.get("allow_school", "")):
            seeds += [
                seed_row(e, f"{x} для музыкальной школы", "school"),
                seed_row(e, f"{x} для школы", "school"),
            ]

        if truthy(e.get("allow_learning", "")):
            seeds += [
                seed_row(e, f"{x} для обучения", "learning"),
                seed_row(e, f"какое {x} выбрать для обучения", "learning-choice"),
            ]

        if truthy(e.get("allow_concert", "")):
            seeds += [
                seed_row(e, f"аренда {x} на концерт", "concert"),
                seed_row(e, f"{x} на концерт", "concert"),
            ]

        if truthy(e.get("allow_orchestra", "")):
            seeds += [
                seed_row(e, f"аренда {x} для оркестра", "orchestra"),
                seed_row(e, f"{x} для оркестра", "orchestra"),
            ]

        if truthy(e.get("allow_shooting", "")):
            seeds += [
                seed_row(e, f"аренда {x} для съемки", "shooting"),
                seed_row(e, f"{x} для съемки", "shooting"),
            ]

        if truthy(e.get("allow_rider", "")):
            seeds += [
                seed_row(e, f"аренда {x} по райдеру", "rider"),
                seed_row(e, f"{x} по райдеру", "rider"),
            ]

    # Deduplicate exact seed+city combinations.
    seen = set()
    out = []
    for row in seeds:
        key = (row["city"], norm(row["seed"]))
        if key in seen:
            continue
        seen.add(key)
        out.append(row)

    # Wordstat currently allows 100 requests per hour for this quota.
    # Keep a safety margin and prefer the commercially strongest scenes.
    priority = {
        "rent": 0,
        "rent-city": 1,
        "prokat": 2,
        "prokat-city": 3,
        "school": 4,
        "learning": 5,
        "learning-choice": 6,
        "concert": 7,
        "orchestra": 8,
        "shooting": 9,
        "rider": 10,
    }
    out.sort(key=lambda r: (
        0 if r["city"] == "Москва" else 1,
        priority.get(r["scene"], 99),
        r["cluster"],
        r["entity"],
        r["seed"],
    ))
    return out


def write_generated_seeds(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["seed", "entity", "cluster", "scene", "city", "region_id", "max_results"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def call_wordstat(api_key: str, folder_id: str, seed: dict) -> dict:
    max_results = max(1, min(int(seed.get("max_results") or 2000), 2000))
    body = {
        "phrase": seed["seed"],
        "numPhrases": str(max_results),
        "regions": [seed["region_id"]] if seed.get("region_id") else [],
        "devices": ["DEVICE_ALL"],
        "folderId": folder_id,
    }

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Api-key {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Wordstat HTTP {exc.code} for seed {seed['seed']!r}: {detail}"
        ) from exc


def extract_results(seed: dict, payload: dict) -> Iterable[dict]:
    # Deliberately ignore payload["associations"].
    for item in payload.get("results", []) or []:
        phrase = str(item.get("phrase", "")).strip()
        if not phrase:
            continue
        yield {
            "seed": seed["seed"],
            "entity": seed["entity"],
            "cluster": seed["cluster"],
            "scene": seed["scene"],
            "city": seed["city"],
            "region_id": seed["region_id"],
            "phrase": phrase,
            "count": int(item.get("count", 0) or 0),
            "relation": "result",
            "total_count": int(payload.get("totalCount", 0) or 0),
        }


def write_raw(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "seed", "entity", "cluster", "scene", "city", "region_id",
        "phrase", "count", "relation", "total_count"
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def useful_for_entity(row: dict) -> bool:
    """Conservative first-pass filter.

    Wordstat result branches should contain the seed terms, but we additionally
    require the instrument/entity itself to remain visible in the phrase.
    This is intentionally conservative: final editorial acceptance happens
    after collection, not here.
    """
    phrase = norm(row["phrase"])
    entity = norm(row["entity"])

    # Every lexical token of the entity must survive in the phrase.
    return all(token in phrase.split() for token in entity.split())


def dedupe_candidates(rows: List[dict]) -> List[dict]:
    best: Dict[Tuple[str, str], dict] = {}
    sources: Dict[Tuple[str, str], set] = {}
    scenes: Dict[Tuple[str, str], set] = {}
    entities: Dict[Tuple[str, str], set] = {}

    for row in rows:
        if not useful_for_entity(row):
            continue

        key = (row["city"], norm(row["phrase"]))
        sources.setdefault(key, set()).add(row["seed"])
        scenes.setdefault(key, set()).add(row["scene"])
        entities.setdefault(key, set()).add(row["entity"])

        if key not in best or row["count"] > best[key]["count"]:
            best[key] = dict(row)

    out = []
    for key, row in best.items():
        out.append({
            "query": row["phrase"],
            "city": row["city"],
            "frequency": row["count"],
            "entity": " | ".join(sorted(entities[key])),
            "cluster": row["cluster"],
            "scenes": " | ".join(sorted(scenes[key])),
            "source_seeds": " | ".join(sorted(sources[key])),
            "status": "candidate",
            "notes": "",
        })

    out.sort(key=lambda r: (r["city"], -int(r["frequency"]), r["query"].casefold()))
    return out


def write_candidates(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "query", "city", "frequency", "entity", "cluster", "scenes",
        "source_seeds", "status", "notes"
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--entities", default="data/entities.csv")
    p.add_argument("--generated-seeds", default="data/generated_seeds.csv")
    p.add_argument("--raw", default="data/wordstat_raw.csv")
    p.add_argument("--candidates", default="data/query_candidates.csv")
    p.add_argument("--delay", type=float, default=0.35)
    p.add_argument("--batch", type=int, default=None,
                   help="0-based batch index; omit for the first quota-safe batch")
    p.add_argument("--batch-size", type=int, default=90,
                   help="requests per batch; keep below the hourly quota")
    args = p.parse_args()

    api_key = os.getenv("YANDEX_WORDSTAT_API_KEY", "").strip()
    folder_id = os.getenv("YANDEX_FOLDER_ID", "").strip()
    if not api_key or not folder_id:
        print("Missing YANDEX_WORDSTAT_API_KEY or YANDEX_FOLDER_ID.", file=sys.stderr)
        return 2

    entities = read_entities(Path(args.entities))
    all_seeds = generate_seeds(entities)

    batch_size = max(1, min(int(args.batch_size), 99))
    batch_index = 0 if args.batch is None else max(0, int(args.batch))
    start = batch_index * batch_size
    stop = start + batch_size
    seeds = all_seeds[start:stop]

    write_generated_seeds(Path(args.generated_seeds), seeds)

    if not seeds:
        print(f"No seeds in batch {batch_index}; total seeds: {len(all_seeds)}")
        return 0

    raw_rows: List[dict] = []
    for i, seed in enumerate(seeds, 1):
        print(f"[{i}/{len(seeds)}] {seed['city']} | {seed['entity']} | {seed['seed']}")
        payload = call_wordstat(api_key, folder_id, seed)
        raw_rows.extend(extract_results(seed, payload))
        if i < len(seeds) and args.delay > 0:
            time.sleep(args.delay)

    write_raw(Path(args.raw), raw_rows)
    candidates = dedupe_candidates(raw_rows)
    write_candidates(Path(args.candidates), candidates)

    print(f"Total generated seeds: {len(all_seeds)}")
    print(f"Batch {batch_index}: seeds {start + 1}-{min(stop, len(all_seeds))} ({len(seeds)} requests)")
    print(f"Wrote {len(raw_rows)} raw result rows")
    print(f"Wrote {len(candidates)} filtered candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
