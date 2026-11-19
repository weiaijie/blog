"""Replay frozen historical models and export chart data after daily ledger reconciliation."""
import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from compare_three_markets import GROUPS, ROOT, evidence, metrics, run, simulate, verified_inputs
from etf_research.baselines import STRATEGIES

MARKETS = ROOT / 'reports/2026-11-08-three-markets'
DOMESTIC = ROOT / 'reports/2026-11-05-long-history'


def reconcile(rows, reference):
    if len(rows) != len(reference):
        raise ValueError('Different number of account closes')
    for row, saved in zip(rows, reference, strict=True):
        if str(row['date']) != saved['date'] or any(
            row[k] != Decimal(saved[k]) for k in row if k != 'date'
        ):
            raise ValueError(f"Historical ledger mismatch on {row['date']}")


def chart_account(rows):
    result = metrics(rows)
    return {
        'equity': [float(r['equity']) for r in rows],
        'total': float(result['total_return']),
        'annual': float(result['annualized_return']),
        'drawdown': float(result['max_drawdown']),
        'peak': str(result['peak']), 'trough': str(result['trough']),
        'recovered': result['recovery'] and str(result['recovery']),
        'sessionsToRecover': result['peak_to_recovery_sessions'],
    }


def build():
    domestic, calendar, bars, halts = verified_inputs(evidence())
    reference = defaultdict(list)
    with (MARKETS / 'daily.csv').open(encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            reference[int(row['years']), row['group']].append(row)
    periods = {}
    for years in (1, 2, 3):
        end = calendar[-1]
        start = end.replace(year=end.year-years)
        days = tuple(d for d in calendar if d >= start)
        accounts = {}
        for group, weights in GROUPS.items():
            rows, _ = simulate(days, bars, domestic.dividends, halts, weights)
            reconcile(rows, reference[years, group])
            accounts[group] = chart_account(rows)
        periods[str(years)] = {'dates': list(map(str, days)), 'accounts': accounts}
    accounts = {}
    for strategy in STRATEGIES:
        rows = run(domestic, strategy, 'base')['daily']
        path = DOMESTIC / f'{strategy}_base_100000_d1_daily.csv'
        with path.open(encoding='utf-8', newline='') as f:
            reconcile(rows, list(csv.DictReader(f)))
        accounts[strategy] = chart_account(rows)
    periods['full'] = {'dates': list(map(str, domestic.sessions)), 'accounts': accounts}
    return periods


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    data = build()
    args.output.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n',
                           encoding='utf-8', newline='\n')
    print(sum(len(p['dates'])*len(p['accounts']) for p in data.values()), 'historical account closes reconciled')
