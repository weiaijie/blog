"""Independent read-only reconstruction; no orders, frozen strategy or Ledger calls."""
from collections import defaultdict
from decimal import Decimal as D, localcontext

SYMS = ('510300', '511010')
FIXED = {'cash': (0, 0), 'equity_hold': (1, 0), 'bond_hold': (0, 1),
         'monthly_20_80': (D('.2'), D('.8')), 'monthly_50_50': (D('.5'), D('.5'))}
STRATEGIES = (*FIXED, 'trend_120')


def signal_weights(strategy, closes, dividends, as_of):
    if strategy in FIXED:
        return tuple(map(D, FIXED[strategy])), None
    if strategy != 'trend_120':
        raise ValueError('Unknown strategy')
    # The older index level scales all 120 observations equally and cancels in the comparison.
    window = [(day, price) for day, price in closes if day <= as_of][-120:]
    if len(window) != 120 or window[-1][0] != as_of:
        raise ValueError('Incomplete prior-close trend window')
    known = {e.ex_date: e.per_share for e in dividends if e.symbol == SYMS[0] and e.announcement_date <= as_of}
    with localcontext() as ctx:
        ctx.prec = 60
        level = total = D(1)
        for (_, prev), (day, price) in zip(window, window[1:]):
            level *= (price + known.get(day, 0)) / prev
            total += level
        spread = level - total / 120
    weights = (D('.5'), D('.5')) if spread > 0 else (D(0), D(1))
    return weights, spread


def batches(days, strategy, delay):
    """Signal close index and intended execution index (may fall beyond the sample)."""
    if delay not in (1, 2, 3) or strategy not in STRATEGIES:
        raise ValueError('Invalid case')
    first = 119 if strategy == 'trend_120' else 0
    monthly = strategy.startswith('monthly_') or strategy == 'trend_120'
    for i, (day, upcoming) in enumerate(zip(days, days[1:])):
        if i == first or (i > first and monthly and (day.year,day.month) != (upcoming.year,upcoming.month)):
            yield i, i + delay


def lots(nav, prices, weights):
    return tuple(int((nav * w) // (p * 100)) * 100 for p, w in zip(prices, weights, strict=True))


def close_book(data, capital, fills):
    """Reconstruct economic NAV (cash plus receivables); it is not available cash."""
    if set(fills).difference(data.sessions):
        raise ValueError('Fill outside verified calendar')
    book = D(capital)
    units = dict.fromkeys(SYMS, 0)
    entitled = {}
    records, ex = defaultdict(list), defaultdict(list)
    for e in data.dividends:
        records[e.record_date].append(e)
        ex[e.ex_date].append(e)
    nav, held = [], []
    for day in data.sessions:
        for e in ex[day]:
            book += entitled[e.key] * e.per_share
        for f in fills.get(day, ()):
            s = f['symbol']
            if f['side'] not in ('buy','sell') or int(f['units']) <= 0:
                raise ValueError('Invalid sealed fill')
            delta = int(f['units']) * (1 if f['side']=='buy' else -1)
            units[s] += delta
            book -= delta * D(f['model_fill']) + D(f['commission']) + D(f['sell_tax'])
        for e in records[day]:
            entitled[e.key] = units[e.symbol]
        held.append(tuple(units[s] for s in SYMS))
        nav.append(book + sum(units[s] * data.bars[s][day].close for s in SYMS))
    return nav, held
