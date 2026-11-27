"""Frozen primitives for the independent five-session experiment."""
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from itertools import pairwise
from math import isfinite
import numpy as np

from .accounting import Ledger
from .baselines import RULES, SCENARIOS, SYMBOLS, debit, fill_price, guard_reason, targets
from .policy_events import TZ, instant

HORIZON = 5
DECISION_TIME = time(8, 55)
MIN_TRAIN = 40
MIN_TEST = 120
MIN_QUARTERS = 2
MIN_EVENTS = 20
CAPITAL = Decimal('100000')
D = Decimal
BASE = ('stockReturn5', 'stockReturn20', 'stockVol20', 'bondReturn5', 'bondReturn20', 'bondVol20', 'turnover20')
GROUPS = {
    'policy': ('policyActiveCount',),
    'etf': ('stockShareFlow', 'bondShareFlow'),
    'margin': ('stockFinancingBuyShare',),
}
VARIANTS = {
    'baseline': BASE,
    'policy': BASE+GROUPS['policy'],
    'etf': BASE+GROUPS['etf'],
    'margin': BASE+GROUPS['margin'],
    'combined': BASE+GROUPS['policy']+GROUPS['etf']+GROUPS['margin'],
}
PRIMARY = 'combined'
BLOCK_SESSIONS = 10
RESAMPLES = 2000
RESAMPLE_SEED = 20261127


@dataclass(frozen=True)
class Window:
    anchor: date
    sessions: tuple[date, ...]

    def __post_init__(self):
        if (len(self.sessions)!=HORIZON or tuple(sorted(set(self.sessions)))!=self.sessions
                or self.anchor>=self.sessions[0]):
            raise ValueError('Five increasing execution sessions after the anchor are required')

    @property
    def entry(self):
        return self.sessions[0]

    @property
    def last(self):
        return self.sessions[-1]

    @property
    def cutoff(self):
        return datetime.combine(self.entry, DECISION_TIME, TZ)


def windows(calendar):
    """Windows advance through an independent trading calendar even if prices are absent."""
    if tuple(calendar) != tuple(sorted(set(calendar))):
        raise ValueError('Independent trading calendar must be increasing and unique')
    for index in range(1, len(calendar)-HORIZON+1):
        yield Window(calendar[index-1],tuple(calendar[index:index+HORIZON]))


def availability(cell, window, *, sealed=None):
    if cell is None or cell.get('verified') is not True or cell.get('asOf')!=str(window.anchor):
        return None
    dates = (cell.get('receivedAt'),cell.get('readyAt'),*cell.get('dependencyReadyAt',()))
    if not all(dates):
        return None
    received, ready, *dependencies = map(instant,dates)
    deadline = window.cutoff if sealed is None else min(window.cutoff,sealed)
    if ready < max((received,*dependencies)) or ready>deadline:
        return None
    number = cell.get('value')
    if number is None:
        return None
    if type(number) is bool or not isfinite(float(number)):
        raise ValueError('Expected a finite numerical observation')
    return float(number)


def feature_vector(cells, names, window, *, sealed=None):
    values = tuple(availability(cells.get(name),window,sealed=sealed) for name in names)
    return None if None in values else values


def sleeve_inputs(levels):
    """Use exactly 21 admitted observations ending at T, in exchange order."""
    if len(levels)!=21 or any(not isfinite(float(x)) or x<=0 for x in levels):
        raise ValueError('Expected 21 positive verified total-return levels')
    series = np.asarray(levels,dtype=float)
    changes = series[1:]/series[:-1]-1
    return (float(series[-1]/series[-6]-1),float(series[-1]/series[0]-1),float(np.std(changes,ddof=0)))


def total_return_levels(closes, distributions):
    """Build a sleeve index from verified closes and confirmed per-share ex-date amounts."""
    if len(closes)!=21 or len(distributions)!=20:
        raise ValueError('Expected 21 closes and 20 ex-date values including confirmed zeros')
    if any(close is None for close in closes) or any(cash is None for cash in distributions):
        return None
    confirmed, cash = tuple(map(D,closes)),tuple(map(D,distributions))
    if (any(not close.is_finite() or close<=0 for close in confirmed)
            or any(not amount.is_finite() or amount<0 for amount in cash)):
        raise ValueError('Invalid close or ex-date amount')
    levels = [D(1)]
    for (previous,current),amount in zip(pairwise(confirmed),cash,strict=True):
        levels.append(levels[-1]*(current+amount)/previous)
    return tuple(levels)


def relative_turnover(amounts):
    if len(amounts)!=21 or any(not isfinite(float(a)) or a<=0 for a in amounts):
        raise ValueError('Expected current and previous 20 same-scope turnover observations')
    return float(amounts[-1])/(sum(float(a) for a in amounts[:-1])/20)


def five_day_label(data, window, opening, *, weight=D('.5'), scenario='base'):
    """Fixed entry order and five close marks. Caller supplies audited opening status."""
    if not isinstance(weight,D) or weight not in (D(0),D('.5')):
        raise ValueError('Only predeclared shadow allocation weights are supported')
    days = (window.anchor,*window.sessions)
    if any(day not in data.sessions for day in days):
        return None
    marks = {sym:{day:data.bars.get(sym,{}).get(day) for day in days} for sym in SYMBOLS}
    if any(bar is None or bar.day!=day or bar.price_mode!='unadjusted'
           for values in marks.values() for day,bar in values.items()):
        return None
    weights = dict(zip(SYMBOLS,(weight,1-weight),strict=True))
    previous = {sym:marks[sym][window.anchor].close for sym in SYMBOLS}
    planned = targets(weights,CAPITAL,previous)
    if any(units and opening.get(sym) not in ('tradable','blocked','known_ex_dividend_day') for sym,units in planned.items()):
        return None

    # Zero holdings at T mean pre-entry record dates confer no entitlement.
    events = tuple(event for event in data.dividends if window.entry<=event.record_date<=window.last)
    costs = SCENARIOS[scenario]
    ledger = Ledger(days,events,cash=CAPITAL,holdings={},costs=costs,lot_size=100,instruments=RULES)
    ledger.open_session(window.anchor)
    ledger.close_session()
    path, decisions = [CAPITAL], {}
    for day in window.sessions:
        ledger.open_session(day)
        if day==window.entry:
            for sym, requested in planned.items():
                if not requested:
                    continue
                bar = marks[sym][day]
                fill = fill_price(bar.open,'buy',costs)
                status = opening[sym]
                reason = ('opening_blocked' if status=='blocked' else
                          guard_reason(bar.open,previous[sym],fill,ex_day=status=='known_ex_dividend_day'))
                if reason is None and fill>bar.high:
                    reason = 'outside_daily_range'
                units = 0
                if reason is None:
                    units = min(requested,int(ledger.available_cash/fill/100)*100)
                    while units and debit(units,fill,costs)>ledger.available_cash:
                        units -= 100
                    if units:
                        ledger.trade(sym,'buy',units,bar.open,signal_date=window.anchor)
                    reason = 'filled' if units==requested else 'cash_limited'
                decisions[sym] = dict(requested=requested,filled=units,reason=reason)
        ledger.close_session()
        path.append(ledger.equity({sym:marks[sym][day].close for sym in SYMBOLS}))
    high, drawdown = path[0], D(0)
    for mark in path:
        high = max(high,mark)
        drawdown = max(drawdown,1-mark/high)
    trades = [row for row in ledger.journal if row['kind']=='trade']
    return dict(terminalReturn=path[-1]/CAPITAL-1,maxDrawdown=drawdown,marks=path,
                commission=sum((t['commission'] for t in trades),D(0)),
                slippage=sum(((t['fill_price']-t['raw_price'])*t['units'] for t in trades),D(0)),
                orders=decisions)


def shifted_month(day, months):
    offset = day.month-1+months
    year,month = day.year+offset//12,offset%12+1
    return date(year,month,min(day.day,monthrange(year,month)[1]))


def holdouts(start):
    """Three predeclared calendar quarters after the initial three months."""
    boundaries = [shifted_month(start,n) for n in (3,6,9,12)]
    return tuple(pairwise(boundaries))


def label_floor(window):
    return datetime.combine(window.last,time(16),TZ)


def training_rows(rows, start):
    freeze = datetime.combine(start,time(),TZ)
    return [r for r in rows if r.get('label') is not None and r.get('labelReadyAt')
            and label_floor(r['window'])<=instant(r['labelReadyAt'])<freeze]


def holdout_rows(rows, start, end, *, training_events=(), prior_holdout_events=()):
    previously_seen = set(training_events)|set(prior_holdout_events)
    return [r for r in rows if start<=r['window'].entry and r['window'].last<end
            and not previously_seen.intersection(r.get('eventIds',()))]


def ridge_fit(x, y):
    """One fixed train-only standardization, unit L2 penalty and unpenalized intercept."""
    x, y = np.asarray(x,dtype=float), np.asarray(y,dtype=float)
    if (x.ndim!=2 or x.shape[1]==0 or len(x)<MIN_TRAIN or y.shape!=(len(x),2)
            or not np.isfinite(x).all() or not np.isfinite(y).all()):
        raise ValueError('Insufficient or invalid paired training rows')
    center, scale, average = x.mean(axis=0), x.std(axis=0,ddof=0), y.mean(axis=0)
    scale = np.where(scale==0,1.0,scale)
    z = (x-center)/scale
    weights = np.linalg.solve(z.T@z+np.eye(z.shape[1]),z.T@(y-average))
    return center,scale,average,weights


def ridge_predict(model,x):
    center,scale,intercept,weights = model
    inputs = np.asarray(x,dtype=float)
    if inputs.ndim!=2 or inputs.shape[1]!=len(center) or not np.isfinite(inputs).all():
        raise ValueError('Invalid feature matrix')
    output = (inputs-center)/scale@weights+intercept
    output[:,1] = np.clip(output[:,1],0,1)
    return output


def label_vector(label):
    return float(label['terminalReturn']),float(label['maxDrawdown'])


def paired_predictions(rows, variant, started_at, fold_index, *, prior_holdout_events=()):
    """Fit both models on the same complete rows and emit scores without reading test outcomes."""
    if type(fold_index) is not int or not 0<=fold_index<3:
        raise ValueError('Expected a predeclared holdout index')
    observed_start = instant(started_at)
    start,end = holdouts(observed_start.astimezone(TZ).date())[fold_index]
    if variant == 'baseline':
        raise ValueError('Choose one of the predeclared increment variants')
    added = VARIANTS[variant]
    uses_policy = 'policyActiveCount' in added
    if len({r['window'].entry for r in rows}) != len(rows):
        raise ValueError('Duplicate decision sessions')
    rows = sorted((row for row in rows if row.get('inputsSealedAt') and
                  observed_start<=instant(row['inputsSealedAt'])<=row['window'].cutoff),
                  key=lambda row:row['window'].entry)

    def vectors(row):
        joined = feature_vector(row['cells'],added,row['window'],sealed=instant(row['inputsSealedAt']))
        return (None,None) if joined is None else (joined[:len(BASE)],joined)

    base, extended, y, trained_events = [], [], [], set()
    for r in training_rows((r for r in rows if r['window'].entry<start),start):
        left,right = vectors(r)
        if left is None:
            continue
        base.append(left)
        extended.append(right)
        y.append(label_vector(r['label']))
        trained_events.update(r.get('eventIds',()))
    if len(y)<MIN_TRAIN:
        return dict(trainingDays=len(y),status='insufficient_training',predictions=[])
    base_model, extended_model = ridge_fit(base,y),ridge_fit(extended,y)
    predictions = []
    for row in holdout_rows(rows,start,end,training_events=trained_events if uses_policy else (),
                            prior_holdout_events=prior_holdout_events if uses_policy else ()):
        left,right = vectors(row)
        if left is not None:
            predictions.append(dict(window=row['window'],fold=start,inputsSealedAt=row['inputsSealedAt'],
                eventIds=tuple(sorted(set(row.get('eventIds',())))) if uses_policy else (),
                baseline=ridge_predict(base_model,[left])[0].tolist(),
                expanded=ridge_predict(extended_model,[right])[0].tolist()))
    return dict(trainingDays=len(y),status='fitted',predictions=predictions)


def nonoverlap(windows):
    """Choose evaluation windows from the complete calendar before matching available signals."""
    last = date.min
    for window in windows:
        if window.entry>last:
            yield window
            last = window.last


def shadow_weight(prediction):
    predicted_return = prediction[0]
    if not isfinite(predicted_return):
        raise ValueError('Expected a finite return forecast')
    return D('.5') if predicted_return>0 else D(0)


def block_intervals(losses, fold_calendars):
    """Paired circular ten-session blocks inside each fold, retaining missing-session masks."""
    rng = np.random.default_rng(RESAMPLE_SEED)
    totals = np.zeros((RESAMPLES,2))
    counts = np.zeros(RESAMPLES)
    for fold, calendar in sorted(fold_calendars.items()):
        n = len(calendar)
        if not n:
            continue
        if tuple(sorted(set(calendar))) != tuple(calendar) or n<BLOCK_SESSIONS:
            raise ValueError('Fold calendar must include at least ten increasing, distinct sessions')
        matrix = np.full((n,2),np.nan)
        for i, day in enumerate(calendar):
            if (fold,day) in losses:
                matrix[i] = losses[fold,day]
        starts = rng.integers(0,n,size=(RESAMPLES,(n+BLOCK_SESSIONS-1)//BLOCK_SESSIONS))
        indices = ((starts[...,None]+np.arange(BLOCK_SESSIONS))%n).reshape(RESAMPLES,-1)[:,:n]
        sampled = matrix[indices]
        totals += np.nansum(sampled,axis=1)
        counts += np.isfinite(sampled[:,:,0]).sum(axis=1)
    valid = counts>0
    if valid.sum()<RESAMPLES*.95:
        return None
    return np.quantile(totals[valid]/counts[valid,None],[.025,.975],axis=0).T.tolist()


def paired_report(predictions, labels, fold_calendars, *, started_at, observed, variant):
    """Match finalized holdout labels after prediction capture and enforce the evidence gates."""
    if observed.tzinfo is None:
        raise ValueError('Report time requires an explicit timezone')
    origin = instant(started_at)
    observation_start = origin.astimezone(TZ).date()
    boundaries = dict(holdouts(observation_start))
    seen, losses, errors, events, quarters = set(), {}, [], set(), set()
    for item in predictions:
        day = item['window'].entry
        if day in seen:
            raise ValueError('Duplicate paired forecast date')
        seen.add(day)
        fold = item['fold']
        if fold not in boundaries or not fold<=day<=item['window'].last<boundaries[fold] or day not in fold_calendars[fold]:
            raise ValueError('Forecast date outside fold calendar')
        inputs, forecast = item.get('inputsSealedAt'), item.get('forecastSealedAt')
        if not inputs or not forecast or not origin<=instant(inputs)<=instant(forecast)<=item['window'].cutoff:
            continue
        label = labels.get(day)
        if label is None or label.get('value') is None or not label.get('readyAt'):
            continue
        ready = instant(label['readyAt'])
        if ready>observed:
            continue
        if ready<label_floor(item['window']):
            raise ValueError('Label published before the last mark')
        actual = np.asarray(label_vector(label['value']))
        left,right = abs(actual-item['baseline']),abs(actual-item['expanded'])
        if not (actual.shape==left.shape==right.shape==(2,)
                and np.isfinite((actual,left,right)).all()):
            raise ValueError('Missing or nonfinite comparison values')
        losses[fold,day] = left-right
        errors.append((left,right))
        events.update(item['eventIds'])
        quarters.add(fold)
    counts = dict(completedPairs=len(losses),quarters=len(quarters),independentEvents=len(events))
    policy_required = 'policyActiveCount' in VARIANTS[variant]
    if observed.astimezone(TZ).date()<shifted_month(observation_start,12):
        return dict(**counts,status='observation_in_progress')
    if len(losses)<MIN_TEST or len(quarters)<MIN_QUARTERS or (policy_required and len(events)<MIN_EVENTS):
        return dict(**counts,status='insufficient_samples')
    ci = block_intervals(losses,{fold:fold_calendars[fold] for fold in quarters})
    result = 'uncertain' if ci is None else ('improved' if all(low>0 for low,_ in ci) else 'not_established')
    means = np.mean(errors,axis=0)
    return dict(**counts,status=result if variant==PRIMARY else 'exploratory',
                baselineMae=means[0].tolist(),expandedMae=means[1].tolist(),
                pairedImprovementInterval=ci)
