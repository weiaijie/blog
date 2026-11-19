"""Daily majority vote on verified domestic ETF total returns, research version 1."""
from collections import defaultdict, deque
from decimal import Decimal as D
from statistics import stdev

MODEL = 'multifactor_v1'
STOCK, BOND = '510300', '511010'
VOL_LIMIT = D('.25')
FACTORS = (
    dict(key='trend120', label='长期趋势', rule='沪深300含分红指数高于120日均线', threshold='0', comparison='>'),
    dict(key='relative60', label='股债相对强弱', rule='近60个交易日沪深300收益高于国债', threshold='0', comparison='>'),
    dict(key='vol20', label='短期波动', rule='沪深300近20个日收益的年化波动低于25%', threshold=str(VOL_LIMIT), comparison='<'),
)


def factor_schedule(history, visible, calendar, bars, events):
    """Emit close observations and transition-only plans. Calendar contains dates, never future quotes."""
    if len(history) < 120:
        raise ValueError('Missing factor warm-up')
    dividends = defaultdict(lambda: D(0))
    for event in events:
        if event.announcement_date <= event.ex_date <= visible[-1]:
            dividends[event.symbol, event.ex_date] += event.per_share
    levels = {s: deque(maxlen=120) for s in (STOCK, BOND)}
    stock_returns = deque(maxlen=20)
    previous_prices = {}
    previous_regime = None
    decisions, schedule = {}, {}
    next_session = dict(zip(calendar, calendar[1:]))
    for day in (*history[-120:], *visible):
        for symbol, series in levels.items():
            price = bars[symbol][day].close
            if series:
                growth = (price + dividends[symbol, day]) / previous_prices[symbol]
                series.append(series[-1] * growth)
                if symbol == STOCK:
                    stock_returns.append(growth - 1)
            else:
                series.append(D(1))
            previous_prices[symbol] = price
        if day < visible[0]:
            continue
        stocks, bonds = levels[STOCK], levels[BOND]
        trend = stocks[-1] / (sum(stocks) / len(stocks)) - 1
        relative = stocks[-1] / stocks[-61] - bonds[-1] / bonds[-61]
        vol = stdev(stock_returns) * D(252).sqrt()
        votes = [dict(**spec, value=value, passed=passed)
                 for spec, value, passed in zip(FACTORS, (trend, relative, vol),
                                                (trend > 0, relative > 0, vol < VOL_LIMIT), strict=True)]
        count = sum(v['passed'] for v in votes)
        regime = 'balanced' if count >= 2 else 'bonds'
        changed = previous_regime != regime
        decisions[day] = dict(asOf=day, factors=votes, votes=count, required=2, regime=regime,
                              transition='initial' if previous_regime is None else 'switch' if changed else 'hold')
        if changed and day in next_session:
            mix = {STOCK: 2, BOND: 2} if regime == 'balanced' else {BOND: 1}
            schedule[next_session[day]] = dict(denominators=mix, reason='factor_'+regime)
        previous_regime = regime
    return decisions, schedule
