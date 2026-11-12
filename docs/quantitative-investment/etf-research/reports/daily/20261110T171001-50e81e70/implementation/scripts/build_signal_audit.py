"""Reconstruct historical target batches and the previously published Nov 6 intent."""
import argparse
import csv
from collections import defaultdict
from datetime import date
from decimal import Decimal as D
from functools import lru_cache
from itertools import product
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from etf_research.admission import load_incremental, sessions_between
from etf_research.long_history import load_long_history
from etf_research.publication import sha
from etf_research.forward import digest, prefix_digest
from etf_research.signal_audit import STRATEGIES, SYMS, batches, close_book, lots, signal_weights

HIST = ROOT/'reports/2026-11-05-long-history'
PRIOR = HIST/'forward_checkpoint.json'
PLAN = ROOT/'reports/2026-11-06-intent/plan.json'
MATRIX = ROOT/'reports/2026-11-06-engine-matrix-final/matrix.json'
FILLS = ROOT/'reports/2026-11-07-historical-pnl/fills.csv'
CASES = tuple(product(STRATEGIES, ('low','base','high'), (10000,100000,1000000), (1,2,3)))
SNAP = ROOT/'data/snapshots'
CALENDAR = SNAP/'2026-11-04-calendar-08/calendar.json'


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def save(path, obj):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str, allow_nan=False)
        f.write('\n')


def write_csv(p, rows):
    with p.open('x', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def forward():
    # This calculation is deliberately not given the saved intent or Nov 6 close/checkpoint.
    data, _ = load_incremental(SNAP, '2026-11-05-close-12b')
    as_of, due = date(2026,11,5), date(2026,11,6)
    prior = read(PRIOR)
    if (data.sessions[-1] != as_of or prior['as_of'] != str(as_of) or prior['forward_sessions'] != 1
            or sessions_between(read(CALENDAR)['holiday_ranges'],due,due) != (due,)):
        raise ValueError('Wrong forward input boundary')
    if (digest({k:v for k,v in prior.items() if k!='checkpoint_sha256'}) != prior['checkpoint_sha256']
            or prefix_digest(data, as_of) != prior['admitted_prefix_sha256']):
        raise ValueError('Prior checkpoint is not bound to these inputs')
    closes = [(d, data.bars[SYMS[0]][d].close) for d in data.sessions]
    prices = tuple(data.bars[s][as_of].close for s in SYMS)
    result = {}
    for strategy in STRATEGIES:
        weights, _ = signal_weights(strategy, closes, data.dividends, as_of)
        for fee in ('low','base','high'):
            name = strategy+'_'+fee
            daily = prior['portfolios'][name]['daily']
            if len(daily)!=1 or daily[0]['date']!=str(as_of):
                raise ValueError('Wrong account prefix')
            last = daily[0]
            nav = D(last['equity'])
            result[name] = dict(signal_date=str(as_of), weights=dict(zip(SYMS, weights)),
                target_units=dict(zip(SYMS,lots(nav,prices,weights))), previous_equity=nav,
                previous_holdings={s:last['units_'+s] for s in SYMS if last['units_'+s]})
    return dict(target_session=str(due), source_through=str(as_of), previous_closes=dict(zip(SYMS,prices)),
                prior_checkpoint_sha256=prior['checkpoint_sha256'], portfolios=result)


def build(out):
    data = load_long_history(SNAP)
    days = data.sessions
    prices = [(d,data.bars[SYMS[0]][d].close) for d in days]
    fills = defaultdict(lambda: defaultdict(list))
    with FILLS.open(encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            fills[row['run']][date.fromisoformat(row['day'])].append(row)
    @lru_cache(None)
    def weight(strategy, day):
        return signal_weights(strategy, prices, data.dividends, day)
    rows, cases = [], []
    for strategy, fee, capital, delay in CASES:
        name = f'{strategy}_{fee}_{capital}_d{delay}'
        nav, held = close_book(data, capital, fills.pop(name, {}))
        batch_count = 0
        for i, j in batches(days, strategy, delay):
            as_of = days[i]
            marks = tuple(data.bars[s][as_of].close for s in SYMS)
            weights, spread = weight(strategy, as_of)
            target = lots(nav[i], marks, weights)
            pre = held[j-1] if j < len(days) else (None,None)
            rows.append(dict(run=name, signal_date=as_of, next_session=days[i+1],
                execution_day=days[j] if j<len(days) else '', delay=delay,
                signal_nav=nav[i], stock_close=marks[0], bond_close=marks[1],
                stock_weight=weights[0], bond_weight=weights[1], trend_spread=spread,
                stock_target=target[0], bond_target=target[1], stock_before=pre[0], bond_before=pre[1],
                state='pending' if j>=len(days) else ('unchanged' if pre==target else 'decision')))
            batch_count += 1
        cases.append(dict(run=name, batches=batch_count, terminal_nav=nav[-1]))
    if fills:
        raise ValueError('Unexpected fill accounts')
    fwd = forward()
    inputs = [FILLS, PRIOR, ROOT/'PROTOCOL_V1.md', CALENDAR, SNAP/'2026-11-05-close-12b/manifest.json',
              *(SNAP/n/'manifest.json' for n in data.provenance['manifests_sha256'])]
    out.mkdir(parents=True, exist_ok=False)
    write_csv(out/'targets.csv', rows)
    write_csv(out/'cases.csv', cases)
    save(out/'forward.json', fwd)
    save(out/'inputs.json', {p.relative_to(ROOT).as_posix():sha(p) for p in inputs})


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True, type=Path)
    build(p.parse_args().output)
