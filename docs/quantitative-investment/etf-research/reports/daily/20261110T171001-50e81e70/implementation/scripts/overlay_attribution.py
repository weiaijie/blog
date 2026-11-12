"""Exact close-to-close ETF P&L from replayed positions, opening fills and record-date entitlements."""
from collections import Counter, defaultdict
from decimal import Decimal as D
from itertools import permutations

from compare_three_markets import CODES

PARTS = ('price', 'dividend', 'commission', 'slippage')


def cumulative_ledger(daily, orders, bars, events):
    by_date = {row['date']: row for row in daily}
    entitlements = defaultdict(Counter)
    for event in events:
        if event.record_date in by_date:
            units = by_date[event.record_date]['units_'+event.symbol]
            entitlements[event.ex_date][event.symbol] += units * event.per_share
    fills = defaultdict(list)
    for order in orders:
        fills[order['day']].append(order)

    total = {s: dict.fromkeys(PARTS, D(0)) for s in CODES}
    opening = daily[0]['equity']
    prefix = {}
    for i, row in enumerate(daily):
        day = row['date']
        if i:
            prev = daily[i-1]
            traded = Counter()
            for fill in fills[day]:
                s = fill['symbol']
                qty = fill['filled'] if fill['side']=='buy' else -fill['filled']
                if fill['open'] != bars[s][day].open:
                    raise ValueError(f'Opening price mismatch: {s} {day}')
                traded[s] += qty
                total[s]['commission'] -= fill['fee']
                total[s]['slippage'] += qty*(fill['open']-fill['modeled_price'])
            for s in CODES:
                before, after = prev['units_'+s], row['units_'+s]
                if before + traded[s] != after:
                    raise ValueError(f'Position change mismatch: {s} {day}')
                if before or after:
                    bar = bars[s][day]
                    total[s]['price'] += before*(bar.open-bars[s][prev['date']].close) + after*(bar.close-bar.open)
                total[s]['dividend'] += entitlements[day][s]
        if sum(sum(parts.values()) for parts in total.values()) != row['equity']-opening:
            raise ValueError(f'ETF attribution differs from closing account on {day}')
        prefix[day] = (row['equity'], {s:parts.copy() for s,parts in total.items()})
    return prefix


def breakdown(left, right, expected):
    by_etf = {}
    for s in CODES:
        parts = {k:right[s][k]-left[s][k] for k in PARTS}
        by_etf[s] = dict(**parts, net=sum(parts.values()))
    totals = {k:sum(parts[k] for parts in by_etf.values()) for k in (*PARTS, 'net')}
    if totals['net'] != expected or sum(totals[k] for k in PARTS) != expected:
        raise ValueError('Attribution does not reconcile to account P&L')
    return dict(byEtf=by_etf, totals=totals, accountChange=expected)


def interval(ledgers, start, end):
    accounts = {}
    for label, prefix in ledgers.items():
        opening, left = prefix[start]
        closing, right = prefix[end]
        accounts[label] = dict(startEquity=opening, endEquity=closing,
                               **breakdown(left,right,closing-opening))
    differences = {}
    for label, base in permutations(accounts,2):
        target, reference = accounts[label], accounts[base]
        differences[label+'-'+base] = breakdown(reference['byEtf'], target['byEtf'],
                                                target['accountChange']-reference['accountChange'])
    return dict(start=start, end=end, accounts=accounts, differences=differences)


def daily_gap(target, reference, holding):
    """Daily signed changes in target minus reference, including the zero starting close."""
    if target.keys() != reference.keys():
        raise ValueError('Gap accounts have different trading dates')
    first = next(iter(target))
    previous_day = first
    rows = []
    sums = {s: dict.fromkeys(PARTS, D(0)) for s in CODES}
    running = D(0)
    for day in target:
        changes = []
        for ledger in (target, reference):
            opening, left = ledger[previous_day]
            closing, right = ledger[day]
            changes.append(breakdown(left, right, closing-opening))
        a, b = changes
        change = a['accountChange'] - b['accountChange']
        detail = breakdown(b['byEtf'], a['byEtf'], change)
        running += change
        if running != (target[day][0]-target[first][0]) - (reference[day][0]-reference[first][0]):
            raise ValueError(f'Cumulative gap differs from accounts on {day}')
        for symbol, parts in detail['byEtf'].items():
            for k in PARTS:
                sums[symbol][k] += parts[k]
        rows.append(dict(date=day, change=change, cumulative=running, targetChange=a['accountChange'],
                         referenceChange=b['accountChange'], byEtf=detail['byEtf'], totals=detail['totals']))
        previous_day = day
    for symbol, parts in sums.items():
        if any(v != holding['byEtf'][symbol][k] for k,v in parts.items()):
            raise ValueError(f'Daily components differ from holding period for {symbol}')
    if running != holding['accountChange']:
        raise ValueError('Daily gaps differ from holding period')
    increases = sorted((r for r in rows if r['change'] > 0), key=lambda r: -r['change'])
    decreases = sorted((r for r in rows if r['change'] < 0), key=lambda r: r['change'])
    return dict(days=rows, increases=[r['date'] for r in increases[:3]],
                decreases=[r['date'] for r in decreases[:3]])


def attribution(ledgers, portfolios):
    first = portfolios[0]['summary']
    holding = interval(ledgers, first['start'], first['end'])
    stress = {}
    for portfolio in portfolios:
        s = portfolio['summary']
        segment = None
        if s['max_drawdown'] != 0:
            segment = interval(ledgers, s['peak'], s['trough'])
            if segment['accounts'][portfolio['id']]['accountChange'] != -s['peak_to_trough_loss']:
                raise ValueError('Peak to trough loss mismatch')
        stress[portfolio['id']] = segment
    gaps = {}
    for target, reference in permutations(ledgers, 2):
        key = target + '-' + reference
        gaps[key] = daily_gap(ledgers[target], ledgers[reference], holding['differences'][key])
    return dict(holding=holding, peakToTrough=stress, dailyGaps=gaps)
