"""Audit every published entry, anniversary, threshold and extreme against frozen accounts."""
import argparse
import csv
import json
from calendar import monthrange
from datetime import date
from decimal import Decimal as D
from pathlib import Path

from compare_three_markets import GROUPS, ROOT, evidence, run, simulate, verified_inputs


def check(condition, label):
    if not condition:
        raise ValueError(label)


def verify(csv_path, summary_path):
    data, calendar, bars, halts = verified_inputs(evidence())
    with csv_path.open(encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    saved = json.loads(summary_path.read_bytes())
    lookup = {(r['group'], int(r['years']), date.fromisoformat(r['start'])): r for r in rows}
    check(len(lookup) == len(rows), 'Duplicate entry')
    check((saved['firstSession'], saved['lastSession']) == tuple(map(str, (calendar[0], calendar[-1]))),
          'Snapshot endpoints')
    with (ROOT/'reports/2026-11-08-three-markets/accounts.csv').open(encoding='utf-8') as f:
        fixed = {(r['group'], int(r['years'])): r for r in csv.DictReader(f)}
    checked = 0
    for years in (1, 2):
        endpoints = {}
        for i, start in enumerate(calendar):
            year = start.year + years
            target = date(year, start.month, min(start.day, monthrange(year, start.month)[1]))
            j = next((n for n in range(i+1, len(calendar)) if calendar[n] >= target), None)
            if j is not None:
                endpoints[start] = i, j
        summary = saved['periods'][str(years)]
        check((summary['firstStart'], summary['lastStart']) == tuple(map(str, (min(endpoints), max(endpoints)))),
              'Eligible entry range')
        check(set(summary['groups']) == set(GROUPS), 'Group coverage')
        for group, weights in GROUPS.items():
            amounts = []
            reached = 0
            for start, (i, j) in endpoints.items():
                end = calendar[j]
                row = lookup[group, years, start]
                check(str(end) == row['end'], 'First session on/after anniversary')
                if group == '510300':
                    # Separate domestic strategy implementation from the original long-history study.
                    daily = run(data, 'monthly_50_50', 'base', account_start=start)['daily']
                    endpoint = daily[j-i]
                else:
                    # Replay only to this maturity, including the actual last trading session.
                    daily, _ = simulate(calendar[i:j+1], bars, data.dividends, halts, weights)
                    endpoint = daily[-1]
                equity = endpoint['equity']
                check(endpoint['date'] == end and equity == D(row['ending_equity']), 'Terminal valuation')
                check(daily[0]['cash'] == 100000 and not any(daily[0]['units_'+s] for s in weights), 'Opening ledger')
                pnl = equity - 100000
                annual = (equity/100000)**(D('365.25')/(end-start).days)-1
                check(pnl == D(row['pnl']) and pnl/100000 == D(row['total_return'])
                      and annual == D(row['annualized_return']), 'Recorded returns')
                reached += equity >= D(100000)*D('1.04')**(D((end-start).days)/D('365.25'))
                amounts.append((pnl, start, end))
                if end == calendar[-1] and str(start) == fixed[group, years]['start']:
                    check(equity == D(fixed[group, years]['ending_equity']), 'Archived fixed window')
                checked += 1
            pnl, start, end = min(amounts)
            expected = dict(count=len(amounts), profitable=sum(v>0 for v,_,_ in amounts), reached=reached,
                            worstPnl=float(pnl), worstReturn=float(pnl/100000), worstStart=str(start),
                            worstEnd=str(end), worstTies=sum(v==pnl for v,_,_ in amounts))
            check(summary['groups'][group] == expected, f'Summary {years}/{group}')
    check(checked == len(rows) and set(saved['periods']) == {'1','2'}, 'Unexpected rows')
    print(checked, 'start/end balances and returns reconciled; 8 summaries passed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('entries', type=Path)
    parser.add_argument('summary', type=Path)
    args = parser.parse_args()
    verify(args.entries, args.summary)
