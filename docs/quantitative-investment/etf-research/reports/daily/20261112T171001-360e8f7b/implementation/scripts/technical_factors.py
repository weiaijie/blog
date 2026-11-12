"""Independent research gates; frozen multifactor_v1 is not modified."""
from collections import defaultdict
from datetime import date
from decimal import Decimal as D
from functools import lru_cache
from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd
import talib

from etf_research.data import verify_manifest
from multifactor_strategy import factor_schedule, STOCK, BOND

ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    'multifactor_volume_v1': '三因子＋量价确认',
    'multifactor_kdj_v1': '三因子＋KDJ',
    'multifactor_adx_v1': '三因子＋ADX',
}


def admit_volume(sessions, bars, official, sina):
    """Reject duplicates, missing days, inconsistent units, and nonpositive counts."""
    result, audit = {}, {}
    for symbol in (STOCK, BOND):
        payload = official[symbol]
        if payload['code'] != symbol or payload['total'] != len(payload['kline']):
            raise ValueError('Incomplete official volume series')
        records = payload['kline']
        keys = [date(int(str(r[0])[:4]), int(str(r[0])[4:6]), int(str(r[0])[6:])) for r in records]
        skeys = [date.fromisoformat(r['day']) for r in sina[symbol]]
        if keys != sorted(set(keys)) or skeys != sorted(set(skeys)):
            raise ValueError('Duplicate or unordered volume dates')
        lookup = dict(zip(keys, records, strict=True))
        secondary = dict(zip(skeys, sina[symbol], strict=True))
        values = {}
        for day in sessions:
            row, other = lookup[day], secondary[day]
            volume, amount = D(str(row[5])), D(str(row[6]))
            if not volume.is_finite() or volume <= 0 or volume != volume.to_integral_value():
                raise ValueError('Invalid volume')
            if volume != D(other['volume']):
                raise ValueError('Cross-source volume conflict')
            bar = bars[symbol][day]
            if not amount.is_finite() or not bar.low <= amount / volume <= bar.high:
                raise ValueError('Volume/amount unit or price range conflict')
            if [D(str(v)) for v in row[1:5]] != [bar.open, bar.high, bar.low, bar.close]:
                raise ValueError('Volume not bound to admitted prices')
            values[day] = int(volume)
        result[symbol] = values
        audit[symbol] = dict(days=len(values), first=str(sessions[0]), last=str(sessions[-1]),
                             exactVolumeMatches=len(values), amountRangeChecks=len(values))
    return result, audit


@lru_cache(maxsize=1)
def volume_inputs():
    from interactive_backtest import inputs
    base, _, bars, _ = inputs()
    snaps = ROOT/'data/snapshots'
    folders = ('2026-11-05-costs-11', '2026-11-04-expansion-07')
    for name in folders:
        verify_manifest(snaps/name)
    official, sina, sources = {}, {}, []
    for symbol in (STOCK, BOND):
        op = snaps/folders[0]/f'official_full_{symbol}.body'
        sp = snaps/folders[1]/f'sina_daily_{symbol}.body'
        official[symbol] = json.loads(op.read_text())
        text = sp.read_text()
        sina[symbol] = json.loads(text[text.index('([')+1:text.rindex(')')])
        for path in (op, sp):
            sources.append(dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    values, audit = admit_volume(base.sessions, bars, official, sina)
    return values, dict(symbols=audit, sources=sources,
        unit='Source counts agree; amount/count lies within raw OHLC. Relative volume is dimensionless.',
        limitations='No independent historical free-float denominator; turnover rate and executable capacity remain unknown.')


def indicator_series(days, bars, events, volumes):
    """Only observed prefix enters rolling/recursive calculations; anchor is 2018-09-14."""
    cash = defaultdict(lambda: D(0))
    for event in events:
        if event.announcement_date <= event.ex_date <= days[-1]:
            cash[event.ex_date] += event.per_share if event.symbol == STOCK else D(0)
    level, previous = D(1), None
    rows = []
    for day in days:
        bar = bars[STOCK][day]
        growth = (bar.close + cash[day])/previous if previous is not None else D(1)
        level *= growth
        # Same-day scaling of all OHLC; no future dividends or vendor adjusted prices.
        scale = level / bar.close
        rows.append([float(bar.high*scale),float(bar.low*scale),float(level),float(growth-1),volumes[STOCK][day]])
        previous = bar.close
    frame = pd.DataFrame(rows, index=days, columns=['high','low','close','return','volume'])
    high, low, close = [frame[k].to_numpy(dtype=float) for k in ('high','low','close')]
    bottom, top = frame.low.rolling(9).min(), frame.high.rolling(9).max()
    rsv = (100*(frame.close-bottom)/(top-bottom)).where(top != bottom, 50)
    # Declared KDJ convention: initial K=D=50 before first 9-bar RSV; alpha=1/3.
    seeded = pd.Series([50., *rsv.iloc[8:].tolist()])
    k = seeded.ewm(alpha=1/3,adjust=False).mean()
    d = k.ewm(alpha=1/3,adjust=False).mean()
    frame['k'] = [np.nan]*8 + k.iloc[1:].tolist()
    frame['d'] = [np.nan]*8 + d.iloc[1:].tolist()
    frame['j'] = 3*frame.k-2*frame.d
    frame['adx'] = talib.ADX(high,low,close,timeperiod=14)
    frame['plusDI'] = talib.PLUS_DI(high,low,close,timeperiod=14)
    frame['minusDI'] = talib.MINUS_DI(high,low,close,timeperiod=14)
    frame['volumeRatio'] = frame.volume/frame.volume.shift(1).rolling(20).mean()
    return frame


def schedule_from_decisions(decisions, calendar):
    next_session = dict(zip(calendar,calendar[1:]))
    schedule, previous = {}, None
    for day, decision in decisions.items():
        regime = decision['regime']
        decision['transition'] = 'initial' if previous is None else 'switch' if previous != regime else 'hold'
        if previous != regime and day in next_session:
            schedule[next_session[day]] = dict(denominators={STOCK:2,BOND:2} if regime=='balanced' else {BOND:1},
                                               reason='factor_'+regime)
        previous = regime
    return schedule


def technical_schedule(history, visible, calendar, bars, events, model, volumes=None):
    if model not in MODELS or len(history) < 120:
        raise ValueError('Unknown technical model or missing warm-up')
    if volumes is None:
        volumes = volume_inputs()[0]
    decisions, _ = factor_schedule(history,visible,calendar,bars,events)
    indicators = indicator_series((*history,*visible),bars,events,volumes)
    for day, decision in decisions.items():
        x = indicators.loc[day]
        if not np.isfinite(x[['k','d','j','adx','plusDI','minusDI','volumeRatio','return']]).all():
            raise ValueError('Incomplete indicator warm-up')
        metrics = {key:float(x[key]) for key in ('k','d','j','adx','plusDI','minusDI','volumeRatio','return')}
        if model == 'multifactor_volume_v1':
            passed = x.volumeRatio > 1 and x['return'] > 0
            value, rule = float(x.volumeRatio), '当日量 / 此前20日平均量 > 1，且当日含分红收益 > 0'
        elif model == 'multifactor_kdj_v1':
            passed = x.k > x.d
            value, rule = float(x.k-x.d), 'KDJ(9,3,3) 的 K > D；J 显示但不额外投票'
        else:
            passed = x.adx >= 25 and x.plusDI > x.minusDI
            value, rule = float(x.adx), 'ADX(14) ≥ 25 且 +DI > −DI'
        gate = dict(key=model,label=MODELS[model],rule=rule,value=value,passed=bool(passed),unit='raw',metrics=metrics)
        decision.update(gate=gate, baseRegime=decision['regime'],
                        regime='balanced' if decision['votes'] >= 2 and passed else 'bonds')
        decision['factors'] = [*decision['factors'],gate]
    return decisions, schedule_from_decisions(decisions,calendar)
