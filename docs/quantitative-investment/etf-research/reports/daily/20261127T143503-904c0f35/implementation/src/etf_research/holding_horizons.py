"""Read-only calendar holding windows. No signal or execution changes."""
import numpy as np
import pandas as pd


def windows(dates, equity, years):
    if type(years) is not int or years not in (1, 2):
        raise ValueError('Only predeclared one/two calendar years')
    days = pd.DatetimeIndex(pd.to_datetime(dates))
    nav = np.asarray(equity, dtype=float)
    if len(days) != len(nav) or len(days) < 2 or not days.is_monotonic_increasing or days.has_duplicates:
        raise ValueError('Unique increasing observations required')
    if days.hasnans or not np.isfinite(nav).all() or (nav <= 0).any():
        raise ValueError('Finite positive NAV required')
    rows = []
    for i, start in enumerate(days):
        anniversary = start + pd.DateOffset(years=years)
        j = int(days.searchsorted(anniversary))
        if j == len(days):
            continue
        elapsed = (days[j] - start).days
        path = nav[i:j+1]
        rows.append(dict(start=start.date().isoformat(), end=days[j].date().isoformat(),
                         anniversary=anniversary.date().isoformat(), calendar_days=elapsed,
                         observations=j-i+1, start_equity=float(nav[i]), end_equity=float(nav[j]),
                         total_return=float(nav[j]/nav[i]-1),
                         annualized_return=float((nav[j]/nav[i])**(365.25/elapsed)-1),
                         max_drawdown=float(np.max(1-path/np.maximum.accumulate(path)))))
    return rows


def summarize(rows):
    if not rows:
        return dict(count=0, at_least_4pct=None, at_least_5pct=None, losses=None,
                    annualized_quantiles=None, worst_window_drawdown=None)
    returns = np.array([r['annualized_return'] for r in rows])
    return dict(count=len(rows), at_least_4pct=int((returns >= .04).sum()),
                at_least_5pct=int((returns >= .05).sum()), losses=int((returns < 0).sum()),
                annualized_quantiles=dict(zip(('min', 'p05', 'median', 'p95', 'max'),
                    map(float, np.quantile(returns, [0, .05, .5, .95, 1])))),
                worst_window_drawdown=max(r['max_drawdown'] for r in rows))


def disjoint(rows, first_date, phase_months):
    """Twelve disclosed starting phases; only within each phase is non-overlap."""
    if type(phase_months) is not int or phase_months not in range(12):
        raise ValueError('Unknown phase')
    threshold = (pd.Timestamp(first_date) + pd.DateOffset(months=phase_months)).date().isoformat()
    selected = []
    for row in rows:
        if row['start'] >= threshold:
            selected.append(row)
            threshold = row['end']
    return selected
