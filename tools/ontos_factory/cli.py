"""CLI for candidate selection and safe preview/publish compilation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import build_from_json
from .portfolio import read_portfolio, report
from .briefs import draft_assignment


def main() -> None:
    parser = argparse.ArgumentParser(description='ONTOS Factory: niche hypotheses and static sites')
    sub = parser.add_subparsers(dest='cmd', required=True)
    top = sub.add_parser('top', help='Rank hypothesis seeds, no site publication')
    top.add_argument('--data', type=Path, required=True)
    top.add_argument('--output', type=Path, required=True)
    top.add_argument('--limit', type=int, default=10)
    top.add_argument('--expected-count', type=int, default=None)
    brief = sub.add_parser('brief', help='Generate an editorial assignment, not a published site')
    brief.add_argument('--data', type=Path, required=True)
    brief.add_argument('--id', required=True)
    brief.add_argument('--output', type=Path, required=True)
    build = sub.add_parser('build', help='Compile one explicitly reviewed site brief')
    build.add_argument('--config', type=Path, required=True)
    build.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.cmd == 'top':
        rows = read_portfolio(args.data, expected_count=args.expected_count)
        if args.limit < 1 or args.limit > len(rows):
            raise ValueError('limit out of bounds')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(report(rows,args.limit),encoding='utf-8')
        print(json.dumps({'hypotheses':len(rows),'shortlisted':args.limit,'report':str(args.output)},ensure_ascii=False))
    elif args.cmd == 'brief':
        rows = read_portfolio(args.data)
        match = next((row for row in rows if row['id'] == args.id), None)
        if match is None:
            raise ValueError('Unknown niche ID')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(draft_assignment(match), encoding='utf-8')
        print(json.dumps({'niche':args.id,'output':str(args.output),'published':False},ensure_ascii=False))
    else:
        print(json.dumps(build_from_json(args.config,args.output),ensure_ascii=False))


if __name__ == '__main__':
    main()
