"""Simulate each eligible trading-day entry from cash and record anniversary outcomes."""
import argparse
import json
from bisect import bisect_left
from decimal import Decimal as D
from pathlib import Path

from compare_three_markets import GROUPS, anniversary, csv_out, evidence, simulate, verified_inputs

INITIAL = D('100000')
TARGET = D('.04')


def entry_schedule(days):
    for i, start in enumerate(days):
        endpoints = {y: bisect_left(days, anniversary(start, y)) for y in (1, 2)}
        if endpoints[1] == len(days):
            break
        eligible = {y: j-i for y, j in endpoints.items() if j < len(days)}
        yield days[i:i+max(eligible.values())+1], eligible


def measure_entry(ledger, endpoints, initial):
    start = ledger[0]['date']
    if ledger[0]['equity'] != initial or ledger[0]['available_cash'] != initial:
        raise ValueError(f'Unexpected opening account on {start}')
    for years, offset in endpoints.items():
        end = ledger[offset]['date']
        equity = ledger[offset]['equity']
        yield measure_outcome(start, end, years, equity, initial)


def measure_outcome(start, end, years, equity, initial):
    ratio = equity / initial
    annual = ratio ** (D('365.25') / (end-start).days) - 1
    return dict(years=years, start=start, end=end, ending_equity=equity,
                pnl=equity-initial, total_return=ratio-1, annualized_return=annual)


def outcomes():
    base, days, bars, halts = verified_inputs(evidence())
    results = []
    for sessions, endpoints in entry_schedule(days):
        for group, weights in GROUPS.items():
            ledger, _ = simulate(sessions, bars, base.dividends, halts, weights)
            for row in measure_entry(ledger, endpoints, INITIAL):
                results.append({'years': row['years'], 'group': group, **row})
    return days, results


def summarize(rows):
    worst = min(rows, key=lambda row: row['pnl'])
    return dict(count=len(rows), profitable=sum(row['pnl'] > 0 for row in rows),
                reached=sum(row['annualized_return'] >= TARGET for row in rows),
                worstPnl=float(worst['pnl']), worstReturn=float(worst['total_return']),
                worstStart=str(worst['start']), worstEnd=str(worst['end']),
                worstTies=sum(row['pnl'] == worst['pnl'] for row in rows))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New output directory')
    out = parser.parse_args().output
    days, rows = outcomes()
    summary = {}
    for years in (1, 2):
        cohorts = [row for row in rows if row['years'] == years]
        summary[years] = dict(firstStart=str(cohorts[0]['start']), lastStart=str(cohorts[-1]['start']),
                              groups={g: summarize([r for r in cohorts if r['group'] == g]) for g in GROUPS})
    out.mkdir(parents=True, exist_ok=False)
    csv_out(out/'entries.csv', rows)
    payload = dict(firstSession=str(days[0]), lastSession=str(days[-1]), periods=summary)
    (out/'entry-windows.json').write_text(json.dumps(payload, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(len(rows), 'matured historical outcomes')
