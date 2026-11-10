"""Rebuild offline research accounts on matched RMB exchange sessions."""
import argparse
import csv
import json
import sys
from bisect import bisect_left
from datetime import date
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from etf_research.accounting import Ledger, InstrumentRules
from etf_research.baselines import SCENARIOS, debit, fill_price, guard_reason, run
from market_evidence import END, START, evidence, verified_inputs
from market_holdings import holdings_report

CODES = ('510300', '513500', '159920', '511010')
GROUPS = {s: {s: 2, '511010': 2} for s in CODES[:3]}
GROUPS['equal'] = dict(zip(CODES, (6, 6, 6, 2)))
COST = SCENARIOS['base']
RULES = {s: InstrumentRules(100, D('.001'), s != '510300') for s in CODES}


def simulate(days, bars, events, halts, denominators, *, initial=D(100000), costs=COST, rebalance='monthly'):
    """Denominators may be integers or exact Fractions for user-defined allocations."""
    if rebalance not in ('monthly', 'hold'):
        raise ValueError('Unknown rebalance frequency')
    events = [e for e in events if e.symbol in denominators and e.record_date >= days[0]]
    ledger = Ledger(days, events, cash=initial, holdings={}, costs=costs, lot_size=100, instruments=RULES)
    daily, orders = [], []
    for i, day in enumerate(days):
        ledger.open_session(day)
        if i == 1 or (rebalance == 'monthly' and i > 1 and day.month != days[i-1].month):
            prev = days[i-1]
            targets = {s: int((daily[-1]['equity'] * den.denominator) // (den.numerator * bars[s][prev].close * 100)) * 100
                       for s, den in denominators.items()}
            for side in ('sell', 'buy'):
                for s in denominators:
                    delta = targets[s] - ledger.holdings.get(s, 0)
                    if (delta <= 0 if side == 'buy' else delta >= 0):
                        continue
                    raw = bars[s][day].open
                    fill = fill_price(raw, side, costs)
                    reason = guard_reason(raw, bars[s][prev].close, fill, ex_day=any(
                        e.symbol == s and e.ex_date == day and e.announcement_date < day for e in events))
                    if (day, s) in halts:
                        reason = 'opening_halt'
                    units, fee = 0, D(0)
                    if reason is None:
                        units = abs(delta)
                        if side == 'buy':
                            units = min(units, int(ledger.available_cash // (fill*100))*100)
                            while units and debit(units, fill, costs) > ledger.available_cash:
                                units -= 100
                        if units:
                            fee = ledger.trade(s, side, units, raw, signal_date=prev)['commission']
                        reason = 'filled' if units == abs(delta) else 'cash_limited'
                    orders.append(dict(day=day, signal=prev, symbol=s, side=side, target=targets[s],
                                       requested=abs(delta), filled=units, open=raw, modeled_price=fill,
                                       fee=fee, reason=reason, session_low=bars[s][day].low,
                                       session_high=bars[s][day].high,
                                       outside_range=bool(units and not bars[s][day].low <= fill <= bars[s][day].high)))
        ledger.close_session()
        equity = ledger.equity({s: bars[s][day].close for s in denominators})
        daily.append(dict(date=day, equity=equity, cash=ledger.cash, available_cash=ledger.available_cash,
                          receivables=sum(ledger.receivables.values(), D(0)),
                          **{'units_'+s:ledger.holdings.get(s, 0) for s in CODES}))
    return daily, orders


def metrics(rows):
    nav = [r['equity'] for r in rows]
    peak = high = trough = 0
    worst = D(0)
    for i, value in enumerate(nav):
        if value >= nav[peak]:
            peak = i
        dd = value / nav[peak] - 1
        if dd < worst:
            worst, high, trough = dd, peak, i
    recovered = next((i for i in range(trough + 1, len(nav)) if nav[i] >= nav[high]), None) if worst else 0
    last = len(nav)-1
    return dict(start=rows[0]['date'], end=rows[-1]['date'], total_return=nav[-1]/nav[0]-1,
                annualized_return=(nav[-1]/nav[0])**(D('365.25')/(rows[-1]['date']-rows[0]['date']).days)-1,
                max_drawdown=worst, peak=rows[high]['date'], trough=rows[trough]['date'],
                recovery=rows[recovered]['date'] if recovered is not None else None,
                trough_to_recovery_sessions=recovered-trough if recovered is not None else None,
                peak_to_recovery_sessions=recovered-high if recovered is not None else None,
                observed_since_trough_sessions=last-trough if recovered is None else None,
                ending_drawdown=nav[-1]/max(nav)-1)


def anniversary(day, years):
    try:
        return day.replace(year=day.year+years)
    except ValueError:
        return date(day.year+years, 2, 28)


def csv_out(path, rows):
    with path.open('x', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def build(out):
    items = evidence()
    domestic, calendar, bars, halts = verified_inputs(items)
    holdings = holdings_report(items)
    totals, daily, orders, windows = [], [], [], []
    for years in (1, 2, 3):
        start = END.replace(year=END.year-years)
        days = tuple(d for d in calendar if d >= start)
        if (days[0], days[-1]) != (start, END):
            raise ValueError('Fixed endpoints unavailable')
        for group, denominators in GROUPS.items():
            rows, trades = simulate(days, bars, domestic.dividends, halts, denominators)
            if group == '510300':
                baseline = run(domestic, 'monthly_50_50', 'base', account_start=start)['daily']
                if len(rows) != len(baseline) or any(any(r[k] != v for k,v in b.items()) for r,b in zip(rows,baseline)):
                    raise ValueError('Domestic baseline diverged')
            label = dict(years=years, group=group)
            daily.extend(dict(**label, **r) for r in rows)
            orders.extend(dict(**label, **r) for r in trades)
            totals.append(dict(**label, **metrics(rows), sessions=len(days),
                               ending_equity=rows[-1]['equity'], commissions=sum(t['fee'] for t in trades)))
            if years == 3:
                for horizon in (1, 2):
                    for i, day in enumerate(days):
                        j = bisect_left(days, anniversary(day, horizon))
                        if j == len(days):
                            break
                        windows.append(dict(years=horizon, group=group, **metrics(rows[i:j+1])))
    out.mkdir(exist_ok=False, parents=True)
    for name, rows in [('accounts', totals), ('daily', daily), ('orders', orders), ('rolling', windows)]:
        csv_out(out / (name + '.csv'), rows)
    (out/'holdings.json').write_text(json.dumps(holdings, ensure_ascii=False, indent=2, default=str)+'\n', encoding='utf-8')
    print(f'{len(daily)} account closes, {len(orders)} orders, {len(windows)} rolling windows, {len(halts)} opening halts')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    build(parser.parse_args().output)
