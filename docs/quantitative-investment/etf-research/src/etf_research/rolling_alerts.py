"""Historical, close-only risk paths. Missing, clear and active are distinct states."""
import numpy as np
import pandas as pd

# Column names identify values as well as rules (two rules share the volatility value).
RULES = {
    'current_drawdown_warning': ('当前回撤', 'current_drawdown', '>', 'drawdown_warning'),
    'observed_year_drawdown_limit': ('年度最大回撤', 'year_drawdown', '>=', 'annual_drawdown_limit'),
    'volatility_limit': ('波动率上限', 'rolling_volatility', '>=', 'annual_volatility_limit'),
    'volatility_warning': ('波动率预警', 'rolling_volatility', '>', 'annual_volatility_warning'),
    'var_limit': ('单日历史 VaR', 'daily_var', '>=', 'daily_var_limit'),
    'sharpe_below_or_equal_target': ('夏普', 'rolling_sharpe', '<=', 'sharpe_target'),
    'daily_move_warning': ('单日涨跌绝对值', 'latest_daily_return', 'abs>', 'daily_move_warning'),
}


def metrics(nav, dates, risk):
    nav = np.asarray(nav, dtype=float)
    if not len(nav) or np.any(~np.isfinite(nav)) or np.any(nav <= 0):
        raise ValueError('Invalid daily NAV')
    idx = pd.DatetimeIndex(dates)
    if len(nav) != len(idx) or idx.hasnans or idx.has_duplicates or not idx.is_monotonic_increasing:
        raise ValueError('Invalid NAV dates')
    frame = pd.DataFrame(index=dates)
    frame['current_drawdown'] = 1 - nav / np.maximum.accumulate(nav)
    ydd = np.empty(len(nav))
    for year in idx.year.unique():
        ix = np.flatnonzero(idx.year == year)
        anchor = max(0, ix[0] - 1)
        vals = nav[anchor:ix[-1] + 1]
        ydd[ix] = np.maximum.accumulate(1 - vals / np.maximum.accumulate(vals))[ix - anchor]
    frame['year_drawdown'] = ydd
    ret = nav[1:] / nav[:-1] - 1
    frame['latest_daily_return'] = np.r_[np.nan, ret]
    window, sessions = risk['lookback_returns'], risk['annualization_sessions']
    for col in ('rolling_volatility', 'daily_var', 'rolling_sharpe'):
        frame[col] = np.nan
    if len(ret) >= window:
        windows = np.lib.stride_tricks.sliding_window_view(ret, window)
        std = windows.std(axis=1, ddof=1)
        rf = (1 + risk['annual_risk_free_assumption']) ** (1 / sessions) - 1
        frame.loc[dates[window:], 'rolling_volatility'] = std * np.sqrt(sessions)
        frame.loc[dates[window:], 'rolling_sharpe'] = np.divide(
            windows.mean(axis=1) - rf, std, out=np.full_like(std, np.nan), where=std > 0
        ) * np.sqrt(sessions)
        frame.loc[dates[window:], 'daily_var'] = np.maximum(0, -np.quantile(
            windows, 1 - risk['var_confidence'], axis=1, method='linear'))
    return frame


def states(series, code, risk):
    _, _, op, key = RULES[code]
    threshold = risk[key] - (1e-12 if code == 'observed_year_drawdown_limit' else 0)
    if op == '>':
        hit = series > threshold
    elif op == '>=':
        hit = series >= threshold
    elif op == '<=':
        hit = series <= threshold
    else:
        hit = series.abs() > threshold
    return np.where(series.isna(), 'unknown', np.where(hit, 'active', 'clear'))


def episodes(run, rule, dates, flags):
    rows = []
    current = None
    for day, state in zip(dates, flags, strict=True):
        if state == 'active':
            if current is None:
                current = dict(run=run, rule=rule, start=day, last_active=day, sessions=0,
                               status='open', cleared='', clearance_reason='')
                rows.append(current)
            current.update(last_active=day, sessions=current['sessions'] + 1)
        elif current is not None:
            if state == 'clear':
                reset = rule == 'observed_year_drawdown_limit' and current['last_active'][:4] != day[:4]
                current.update(status='cleared', cleared=day,
                               clearance_reason='year_reset' if reset else 'threshold')
            else:
                current['status'] = 'interrupted_unknown'
            current = None
    return rows
