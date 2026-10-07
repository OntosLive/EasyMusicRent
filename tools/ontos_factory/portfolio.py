"""A hypothesis portfolio, not a forecast of traffic, income or verified executors."""
from __future__ import annotations

import csv
from pathlib import Path

AXES = ('expertise_fit','executor_access','ticket_hypothesis','intent_clarity','low_ops_friction')
WEIGHTS = (6, 5, 4, 3, 2)  # max 100; entirely subjective initial assumptions


def read_portfolio(path: Path, *, expected_count: int | None = None) -> list[dict]:
    with Path(path).open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    if expected_count is not None and len(rows) != expected_count:
        raise ValueError(f'Expected {expected_count} hypotheses, found {len(rows)}')
    if not rows:
        raise ValueError('Empty portfolio')
    seen_id, seen_name = set(), set()
    for row in rows:
        for field in ('id','vertical','name','human_situation','economic_model','status'):
            if not row.get(field, '').strip():
                raise ValueError(f'Missing {field} for {row.get("id", "?")}')
        if row['id'] in seen_id or row['name'].casefold() in seen_name:
            raise ValueError('Duplicate niche ID or niche name')
        seen_id.add(row['id'])
        seen_name.add(row['name'].casefold())
        if row['status'] != 'гипотеза, не проверена':
            raise ValueError('Portfolio data must not masquerade as validated demand')
        for field in AXES:
            try:
                x = int(row[field])
            except (ValueError, KeyError) as e:
                raise ValueError(f'{row["id"]} missing numeric axis {field}') from e
            if x < 1 or x > 5:
                raise ValueError(f'{field} must be a subjective score from 1 to 5')
    return rows


def score(row: dict) -> int:
    return sum(int(row[axis])*weight for axis, weight in zip(AXES, WEIGHTS))


def prioritize(rows: list[dict], limit: int = 10) -> list[dict]:
    return sorted(rows, key=lambda r: (-score(r), r['id']))[:limit]


def report(rows: list[dict], limit: int = 10) -> str:
    best = prioritize(rows, limit)
    lines = ['# Фабрика ниш: предварительные первые десять', '',
             '**Статус:** гипотезы, не результаты исследования рынка. Оценки субъективны.',
             'Шкалы (1–5): предметная экспертиза ×6; доступ к исполнителям ×5;'
             ' потенциальный чек ×4; ясность намерения ×3; низкая операционная нагрузка ×2.',
             '100 баллов максимум. Наличие исполнителя, спрос и экономика сделки требуют проверки.', '',
             '| № | Ниша | Балл | Боль заказчика | Возможный доход |',
             '|---|---|---:|---|---|']
    for i, r in enumerate(best, 1):
        safe = [r[k].replace('|','/') for k in ('name','human_situation','economic_model')]
        lines.append(f'| {i} | {safe[0]} | {score(r)} | {safe[1]} | {safe[2]} |')
    lines.extend(['', '## Перед запуском любой из ниш', '',
                 '1. Подтвердить конкретного исполнителя и его профессиональные границы.',
                 '2. Проверить реальные формулировки спроса и существующие предложения.',
                 '3. Согласовать способ передачи контакта, вознаграждение и ответственность.',
                 '4. Создать один самостоятельный полезный выпуск; звонок/мессенджер вместо формы.',
                 '5. Измерить звонки, квалификацию обращений, исполнения и чистую отдачу.',
                 '6. Только после этого создавать новый домен и новые предметные страницы.', ''])
    return '\n'.join(lines)
