"""Independently reconcile the published daily rows against constant-unit holding blocks."""
import argparse
import csv
import json
from datetime import datetime, timedelta
from decimal import Decimal as D
from itertools import groupby
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'reports/2026-11-08-nav-fx'


def rows(path):
    with path.open(encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def mark(row, method):
    if method in ('iopv', 'documented_nav'):
        return D(row[method]) if row[method] else None
    before, after = row[method + '_close'], row[method + '_us']
    if before and after:
        return D(row['expost_nav']) * D(before) / D(after)
    return None


def near(a, b):
    if abs(a - D(b)) > D('0.00000001'):
        raise ValueError(f'Reconciliation failed: {a} vs {b}')


def verify(out):
    obs = rows(out / 'close_observations.csv')
    days = {r['date']: r for r in obs}
    base = rows(BASE / 'drawdown.csv')
    segments = rows(out / 'intervals.csv')
    summary = json.loads((out / 'summary.json').read_text())
    expected = {r['date'] for r in rows(BASE / 'market.csv')
                if r['symbol'] == '513500' and D(r['premium_pct']) > 5}
    assert len(expected) == 257 and len(obs) == len(days) == 291
    assert set(days) == expected | {base[0]['previous']} | {r['date'] for r in base}
    assert {d for d, r in days.items() if r['high_expost'] == 'True'} == expected
    for r in obs:
        cutoff = datetime.fromisoformat(r['cn_close'])
        assert cutoff.hour == 15 and cutoff.minute == 0 and cutoff == datetime.fromisoformat(r['utc'])
        assert cutoff == datetime.fromisoformat(r['new_york'])
        assert r['documented_nav_date'] < r['date'] and not r['latest_across_all_channels']
        issuer = days[r['referenced_pcf_day']]
        assert issuer['pcf_nav'] == r['documented_nav'] and issuer['pcf_nav_date'] == r['documented_nav_date']
        assert datetime.fromisoformat(issuer['pcf_last_modified']) <= cutoff
        assert not r['iopv_tick_time'] and D(r['iopv']) > 0 and not r['expiry_verified']
        for field, minutes in [('es_hour_start', 60), ('es_short_start', 3 if r['es_3m_close'] else 1)]:
            if r[field]:
                assert cutoff - datetime.fromisoformat(r[field]) == timedelta(minutes=minutes)
    for old, new in zip(base, segments, strict=True):
        assert (old['previous'], old['date'], old['opening_stock_units']) == (new['previous'], new['date'], new['units'])
        near(D(old['premium_gap']), new['original_gap_pnl'])
    for period, batch in [('all', segments), ('february', [r for r in segments if r['date'].startswith('2025-02')])]:
        s = summary[period]
        assert len(batch) == s['intervals'] and s['causal_timing_amount'] is None
        near(sum(D(r['original_gap_pnl']) for r in batch), s['original_gap_pnl'])
        for method, data in s['methods'].items():
            timing = remaining = D(0)
            direct = 0
            for q, group in groupby(batch, key=lambda x: int(x['units'])):
                block = list(group)
                a, b = days[block[0]['previous']], days[block[-1]['date']]
                change = mark(b, method) - mark(a, method)
                timing += q * (change - (D(b['expost_nav']) - D(a['expost_nav'])))
                remaining += q * (D(b['close']) - D(a['close']) - change)
            for r in batch:
                a, b = days[r['previous']], days[r['date']]
                x, y = mark(a, method), mark(b, method)
                if x is None or y is None:
                    assert r[method + '_remaining'] == r[method + '_timing'] == ''
                else:
                    residual = int(r['units']) * (D(b['close']) - y - D(a['close']) + x)
                    near(residual, r[method + '_remaining'])
                    near(D(r['original_gap_pnl']) - residual, r[method + '_timing'])
                    direct += 1
            near(timing, data['timing_cny'])
            near(remaining, data['remaining_cny'])
            near(timing + remaining, s['original_gap_pnl'])
            assert direct == data['directly_valued_intervals']
    assert sum(line.startswith('| 2025-02-') for line in (out/'february.md').read_text(encoding='utf8').splitlines()) == 18
    print('Verified 291 dated observations, 72 frozen intervals and 8 holding-block decompositions.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('report', type=Path)
    verify(parser.parse_args().report)
