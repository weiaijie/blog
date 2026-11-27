"""Independent CSV replay of positions, cash, entitlement, targets, fills and recovery."""
import argparse
import csv
import sys
from collections import defaultdict
from datetime import date
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path

import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from market_evidence import END, evidence, verified_inputs

CODES = ('510300','513500','159920','511010')


def grouped(folder, name):
    result = defaultdict(list)
    with (folder/(name+'.csv')).open(encoding='utf-8') as file:
        for row in csv.DictReader(file):
            result[int(row['years']), row['group']].append(row)
    return result


def check(condition, message):
    if not condition:
        raise ValueError(message)


def verify_metrics(rows, result):
    amounts = np.array([float(r['equity']) for r in rows])
    decline = amounts / np.maximum.accumulate(amounts) - 1
    trough = int(np.argmin(decline))
    peak = int(np.flatnonzero(amounts[:trough+1] == max(amounts[:trough+1]))[-1])
    later = np.flatnonzero(amounts[trough:] >= amounts[peak])
    recovered = int(trough + later[0]) if len(later) else None
    for key, value in [('max_drawdown',min(decline)), ('ending_drawdown',decline[-1]),
                       ('total_return',amounts[-1]/amounts[0]-1),
                       ('annualized_return',(amounts[-1]/amounts[0])**(365.25/(
                        date.fromisoformat(rows[-1]['date'])-date.fromisoformat(rows[0]['date'])).days)-1)]:
        check(abs(float(result[key])-value) < 1e-11, key)
    for key, expected in [('peak',rows[peak]['date']), ('trough',rows[trough]['date']),
                          ('recovery',rows[recovered]['date'] if recovered is not None else ''),
                          ('peak_to_recovery_sessions',str(recovered-peak) if recovered is not None else ''),
                          ('trough_to_recovery_sessions',str(recovered-trough) if recovered is not None else ''),
                          ('observed_since_trough_sessions',str(len(rows)-1-trough) if recovered is None else '')]:
        check(result[key] == expected, key)


def verify(folder):
    base, days, bars, halts = verified_inputs(evidence())
    daily, orders, summaries, rolling = (grouped(folder,k) for k in ('daily','orders','accounts','rolling'))
    check(set(daily) == set(orders) == set(summaries) == {(y,s) for y in (1,2,3) for s in (*CODES[:3],'equal')}, 'Account coverage')
    for (years, group), rows in daily.items():
        calendar = [d for d in days if d >= END.replace(year=END.year-years)]
        check([str(d) for d in calendar] == [r['date'] for r in rows], 'Calendar')
        codes = CODES if group == 'equal' else (group,'511010')
        holding = dict.fromkeys(CODES,0)
        cash, pending = D(100000), {}
        eligible = [e for e in base.dividends if e.symbol in codes and e.record_date >= calendar[0]]
        cursor = iter(orders[years,group])
        for i,(day,r) in enumerate(zip(calendar,rows)):
            blocked, accrued = D(0), D(0)
            for e in eligible:
                if e.ex_date <= day <= e.pay_date:
                    amount = e.per_share*pending[e.key]
                    if day == e.pay_date:
                        cash += amount
                        blocked += amount
                    else:
                        accrued += amount
            if i and (i==1 or day.month != calendar[i-1].month):
                prev = calendar[i-1]
                changes = {}
                for s in codes:
                    den = 6 if group=='equal' and s!='511010' else 2
                    goal = int(D(rows[i-1]['equity'])/(bars[s][prev].close*100*den))*100
                    if goal != holding[s]:
                        changes[s] = goal-holding[s]
                for s in sorted(changes,key=lambda symbol:changes[symbol]>0):
                    order = next(cursor)
                    delta = changes[s]
                    buy = delta > 0
                    raw = bars[s][day].open
                    price = (raw*(D('1.0005') if buy else D('0.9995'))).quantize(
                        D('.001'),rounding=ROUND_CEILING if buy else ROUND_FLOOR)
                    check((str(day), str(prev), s, 'buy' if buy else 'sell', abs(delta),holding[s]+delta,raw,price)==(
                        order['day'],order['signal'],order['symbol'],order['side'],int(order['requested']),
                        int(order['target']),D(order['open']),D(order['modeled_price'])), 'Order mismatch')
                    units = abs(delta)
                    prior = bars[s][prev].close
                    reason = 'filled'
                    if (day,s) in halts:
                        reason = 'opening_halt'
                    elif any(e.symbol==s and e.ex_date==day for e in eligible):
                        reason = 'known_ex_dividend_day'
                    elif max(abs(raw-prior),abs(price-prior)) >= prior*D('.09'):
                        reason = 'conservative_9pct_buffer'
                    if reason != 'filled':
                        units = 0
                    while units:
                        fee = max(D(5),units*price*D('.0003')).quantize(D('.01'),rounding=ROUND_HALF_UP)
                        if not buy or units*price+fee <= cash-blocked:
                            break
                        units -= 100
                        reason = 'cash_limited'
                    if not units:
                        fee = D(0)
                    check((units,fee,reason)==(int(order['filled']),D(order['fee']),order['reason']), 'Fill mismatch')
                    bar = bars[s][day]
                    check((D(order['session_low']),D(order['session_high']),order['outside_range']) ==
                          (bar.low,bar.high,str(bool(units and not bar.low <= price <= bar.high))), 'Daily range audit')
                    holding[s] += units if buy else -units
                    cash += (-units if buy else units)*price-fee
            for e in eligible:
                if day==e.record_date:
                    pending[e.key] = holding[e.symbol]
            equity = cash+accrued+sum(holding[s]*bars[s][day].close for s in codes)
            check(all(int(r['units_'+s]) == holding[s] for s in CODES) and
                  [D(r[k]) for k in ('cash','available_cash','receivables','equity')] ==
                  [cash,cash-blocked,accrued,equity], 'Cash, holdings or equity '+str(day))
        check(next(cursor,None) is None,'Unmatched order')
        verify_metrics(rows,summaries[years,group][0])
        if years == 3:
            for y in (1,2):
                j=0
                for i,start in enumerate(calendar):
                    anniversary=start.replace(year=start.year+y,day=28 if (start.month,start.day)==(2,29) else start.day)
                    while j<len(calendar) and calendar[j]<anniversary:
                        j+=1
                    if j==len(calendar):
                        break
                    window=rolling[y,group][i]
                    check(window['start']==str(start) and window['end']==str(calendar[j]), 'Window endpoints')
                    verify_metrics(rows[i:j+1],window)
                check(len(rolling[y,group])==i,'Rolling coverage')
    print('PASS independent lot, fee, cash, dividend, daily NAV, window, drawdown and recovery replay')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    verify(parser.parse_args().folder)
