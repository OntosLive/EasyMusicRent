#!/usr/bin/env python3
"""Collect Yandex Wordstat queries for configured seeds.

Reads data/seeds.csv, calls Wordstat GetTop, and writes:
- data/wordstat_raw.csv: all returned phrases with source seed and relation
- data/query_candidates.csv: deduplicated phrases, keeping the strongest observed count

The script does not automatically promote candidates into data/queries.csv.
That file remains the curated backlog.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

API_URL = "https://searchapi.api.cloud.yandex.net/v2/wordstat/topRequests"


def truthy(value: str) -> bool:
    return value.strip().lower() not in {"", "0", "false", "no", "off"}


def read_seeds(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return [r for r in rows if truthy(r.get("enabled", "true"))]


def call_wordstat(api_key: str, folder_id: str, seed: dict) -> dict:
    max_results = int(seed.get("max_results") or 2000)
    max_results = max(1, min(max_results, 2000))
    body = {
        "phrase": seed["seed"].strip(),
        "numPhrases": str(max_results),
        "regions": [seed["region_id"].strip()] if seed.get("region_id", "").strip() else [],
        "devices": ["DEVICE_ALL"],
        "folderId": folder_id,
    }

    request = urllib.request.Request(
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
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Wordstat HTTP {exc.code} for seed {seed['seed']!r}: {detail}"
        ) from exc


def extract_rows(seed: dict, payload: dict) -> Iterable[dict]:
    base = {
        "seed": seed["seed"].strip(),
        "city": seed.get("city", "").strip(),
        "region_id": seed.get("region_id", "").strip(),
    }
    for relation_key, relation_name in (
        ("results", "result"),
        ("associations", "association"),
    ):
        for item in payload.get(relation_key, []) or []:
            phrase = str(item.get("phrase", "")).strip()
            if not phrase:
                continue
            yield {
                **base,
                "phrase": phrase,
                "count": int(item.get("count", 0) or 0),
                "relation": relation_name,
                "total_count": int(payload.get("totalCount", 0) or 0),
            }


def write_raw(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["seed", "city", "region_id", "phrase", "count", "relation", "total_count"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def dedupe_candidates(rows: List[dict]) -> List[dict]:
    # Distinguish the same phrase across cities, because the regional count differs.
    best: Dict[Tuple[str, str], dict] = {}
    seeds_seen: Dict[Tuple[str, str], set] = {}

    for row in rows:
        key = (row["city"], row["phrase"].casefold())
        seeds_seen.setdefault(key, set()).add(row["seed"])
        if key not in best or row["count"] > best[key]["count"]:
            best[key] = dict(row)

    out = []
    for key, row in best.items():
        out.append({
            "query": row["phrase"],
            "city": row["city"],
            "frequency": row["count"],
            "relation": row["relation"],
            "source_seeds": " | ".join(sorted(seeds_seen[key])),
            "status": "candidate",
            "notes": "",
        })

    out.sort(key=lambda r: (r["city"], -int(r["frequency"]), r["query"].casefold()))
    return out


def write_candidates(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["query", "city", "frequency", "relation", "source_seeds", "status", "notes"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="data/seeds.csv")
    parser.add_argument("--raw", default="data/wordstat_raw.csv")
    parser.add_argument("--candidates", default="data/query_candidates.csv")
    parser.add_argument("--delay", type=float, default=0.35)
    args = parser.parse_args()

    api_key = os.getenv("YANDEX_WORDSTAT_API_KEY", "").strip()
    folder_id = os.getenv("YANDEX_FOLDER_ID", "").strip()
    if not api_key or not folder_id:
        print(
            "Missing YANDEX_WORDSTAT_API_KEY or YANDEX_FOLDER_ID environment variable.",
            file=sys.stderr,
        )
        return 2

    seeds = read_seeds(Path(args.seeds))
    if not seeds:
        print("No enabled seeds found.", file=sys.stderr)
        return 3

    raw_rows: List[dict] = []
    for index, seed in enumerate(seeds, start=1):
        print(f"[{index}/{len(seeds)}] {seed['city']}: {seed['seed']}")
        payload = call_wordstat(api_key, folder_id, seed)
        raw_rows.extend(extract_rows(seed, payload))
        if index < len(seeds) and args.delay > 0:
            time.sleep(args.delay)

    write_raw(Path(args.raw), raw_rows)
    candidates = dedupe_candidates(raw_rows)
    write_candidates(Path(args.candidates), candidates)

    print(f"Wrote {len(raw_rows)} raw rows to {args.raw}")
    print(f"Wrote {len(candidates)} deduplicated candidates to {args.candidates}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
