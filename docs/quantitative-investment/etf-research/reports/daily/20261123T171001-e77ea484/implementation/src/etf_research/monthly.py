"""Gross ETF comparator and monthly net account comparisons; no execution."""
from calendar import monthrange
from datetime import date
from decimal import Decimal as D
from statistics import stdev
from .admission import sessions_between


def index_levels(data, days, cfg):
    weights = {s: D(w) for s, w in cfg['weights'].items()}
    if (weights != {'510300': D('.5'), '511010': D('.5')} or cfg['version'] != 1
        or cfg['rebalance'] != 'month_boundary_prior_close'
        or cfg['dividend'] != 'verified_cash_reinvest_at_ex_close'
        or cfg['costs'] != 'zero_fractional_units' or cfg['scope'] != 'report_only'):
        raise ValueError('Unknown comparator policy')
    if not days or list(days) != [d for d in data.sessions if days[0] <= d <= days[-1]]:
        raise ValueError('Account and admitted trading calendar differ')
    cash = {}
    for e in data.dividends:
        key = e.symbol, e.ex_date
        cash[key] = cash.get(key, D(0)) + e.per_share
    values = weights.copy()
    levels = [D(1)]
    for prev, day in zip(days, days[1:]):
        if (prev.year, prev.month) != (day.year, day.month):
            values = {s: levels[-1] * w for s, w in weights.items()}
        for s in values:
            values[s] *= (data.bars[s][day].close + cash.get((s, day), 0)) / data.bars[s][prev].close
        levels.append(sum(values.values()))
    return levels


def compare(days, equity, levels, ranges, cfg):
    if (len(equity) != len(days) or len(days) != len(levels) or not days
            or list(days) != sorted(set(days)) or any(not v.is_finite() or v <= 0 for v in [*equity, *levels])):
        raise ValueError('Invalid aligned equity series')
    months = {}
    for i, d in enumerate(days):
        months.setdefault(d.strftime('%Y-%m'), []).append(i)
    rows = []
    for m, indices in months.items():
        start, end = indices[0], indices[-1]
        anchor = max(0, start-1)
        sample = range(anchor+1, end+1)
        dt = days[start]
        expected = sessions_between(ranges, dt.replace(day=1), dt.replace(day=monthrange(dt.year, dt.month)[1]))
        if any(days[i] not in expected for i in indices):
            raise ValueError('Observation outside exchange calendar')
        complete = start > 0 and tuple(days[i] for i in indices) == expected
        net = equity[end]/equity[anchor]-1 if sample else None
        gross = levels[end]/levels[anchor]-1 if sample else None
        active = [equity[i]/equity[i-1] - levels[i]/levels[i-1] for i in sample]
        te = (stdev(active) * D(cfg['annualization_sessions']).sqrt()
              if complete and len(active) >= max(2, cfg['tracking_error_min_month_returns']) else None)
        peak = equity[anchor]
        drawdown = D(0)
        for i in sample:
            peak = max(peak, equity[i])
            drawdown = max(drawdown, 1-equity[i]/peak)
        def num(x):
            return float(x) if x is not None else None
        rows.append(dict(month=m, complete=complete, anchor=str(days[anchor]), through=str(days[end]),
                         paired_returns=len(active), net_return=num(net), benchmark_return=num(gross),
                         relative_return=num(net-gross if sample else None), max_drawdown=num(drawdown if sample else None),
                         cumulative_net=num(equity[end]/equity[0]-1 if end else None),
                         cumulative_benchmark=num(levels[end]/levels[0]-1 if end else None),
                         tracking_error_annualized=num(te)))
    return rows
