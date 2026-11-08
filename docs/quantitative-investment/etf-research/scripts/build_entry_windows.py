"""Simulate each eligible trading-day entry from cash and record anniversary outcomes."""
import argparse
import json
from bisect import bisect_left
from decimal import Decimal as D
from pathlib import Path

from compare_three_markets import GROUPS, anniversary, csv_out, evidence, simulate, verified_inputs

INITIAL = D('100000')
TARGET = D('.04')


def outcomes():
    base, days, bars, halts = verified_inputs(evidence())
    results = []
    for i, start in enumerate(days):
        endpoints = {y: bisect_left(days, anniversary(start, y)) for y in (1, 2)}
        if endpoints[1] == len(days):
            break
        eligible = {y: j for y, j in endpoints.items() if j < len(days)}
        for group, weights in GROUPS.items():
            # A shared entry has identical trades up to its first anniversary.
            ledger, _ = simulate(days[i:max(eligible.values())+1], bars, base.dividends, halts, weights)
            if ledger[0]['equity'] != INITIAL or ledger[0]['available_cash'] != INITIAL:
                raise ValueError(f'Unexpected opening account on {start}')
            for years, j in eligible.items():
                end = days[j]
                equity = ledger[j-i]['equity']
                ratio = equity / INITIAL
                annual = ratio ** (D('365.25') / (end-start).days) - 1
                results.append(dict(years=years, group=group, start=start, end=end,
                                    ending_equity=equity, pnl=equity-INITIAL,
                                    total_return=ratio-1, annualized_return=annual))
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
