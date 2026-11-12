"""Common-start, common-capital comparisons of the four domestic ETF methods."""
import argparse
import csv
from dataclasses import replace
from datetime import date
from decimal import Decimal as D
import hashlib
from functools import lru_cache
from pathlib import Path
import re

import interactive_backtest as work
from build_entry_windows import entry_schedule, measure_outcome, summarize
from etf_research.baselines import run
from installment_strategy import installment_schedule
from model_replay import replay
from multifactor_strategy import MODEL as FACTOR_MODEL, factor_schedule

MODELS = ('allocation', 'installments', 'trend_120', FACTOR_MODEL)
DEFAULTS = dict(start=work.OPTIONS['trendFirst'], end=work.DEFAULTS['end'], capital='100000',
                fees='base', installments='3', rebalance='hold')
ARCHIVE = Path(__file__).resolve().parents[1]/'reports/2026-11-10-multifactor-windows/entries.csv'


def prepare(params):
    if not re.fullmatch(r'[2-9]|1[0-2]', params['installments']):
        raise work.InputError('分批期数须为 2 至 12 的整数。')
    config = dict(params, weights='1,0,0,1')
    days, capital, simulate = work.configured_replay(config)
    if days[0] < work.inputs()[0].sessions[120]:
        raise work.InputError('四种方式共用的最早起点为 '+DEFAULTS['start']+'，此前行情供趋势预热。')
    return config, days, capital, simulate


def allocation_ledgers(config, sessions, bars, simulate):
    schedule = installment_schedule(sessions, sessions, bars['510300'], int(config['installments']),
                                    config['rebalance'], simulate.keywords['denominators'])
    return dict(allocation=simulate(sessions), installments=simulate(sessions, schedule=schedule))


def factor_ledger(sessions, base, bars, simulate):
    first = base.sessions.index(sessions[0])
    warmup = base.sessions[first-120:first]
    _, schedule = factor_schedule(warmup, sessions, sessions, bars, base.dividends)
    daily, _ = simulate(sessions, schedule=schedule)
    return daily


def calculate_entries(params):
    config, days, capital, simulate = prepare(params)
    base, _, bars, _ = work.inputs()
    for sessions, endpoints in entry_schedule(days):
        start = sessions[0]
        books = allocation_ledgers(config,sessions,bars,simulate)
        fixed, _ = books['allocation']
        staged, _ = books['installments']
        # Preserve all pre-start history for the frozen trend calculation. The last
        # available close and each opening signal use the same cutoffs as replay.
        end_index = base.sessions.index(sessions[-1])
        prefix = replace(base, sessions=base.sessions[:end_index+1])
        trend = run(prefix,'trend_120',config['fees'],capital,account_start=start)['daily']
        factor = factor_ledger(sessions,base,bars,simulate)
        for years, i in endpoints.items():
            yield dict(start=str(start),end=str(sessions[i]),years=years,
                       allocation=fixed[i]['equity'],installments=staged[i]['equity'],trend_120=trend[i]['equity'],
                       multifactor_v1=factor[i]['equity'])


@lru_cache(maxsize=1)
def archived_entries():
    text = ARCHIVE.read_text(encoding='utf-8')
    if hashlib.sha256(text.encode()).hexdigest() != 'd634f08a2ba0e06a2a6ba86c629e7761ea4bed5e2c000cdc864d857ad6d8c3bc':
        raise ValueError('Published method outcomes changed; verify the export')
    return {(row['start'],int(row['years'])):row for row in csv.DictReader(text.splitlines())}


def selected_entries(params, days):
    archive_settings = ('fees','installments','rebalance')
    if (D(params['capital'])==D(DEFAULTS['capital']) and
            all(params[k]==DEFAULTS[k] for k in archive_settings)):
        archive = archived_entries()
        for sessions, endpoints in entry_schedule(days):
            for years, i in endpoints.items():
                row = archive[str(sessions[0]),years]
                if row['end']!=str(sessions[i]):
                    raise ValueError('Archived maturity differs from admitted calendar')
                yield row
    else:
        yield from calculate_entries(params)


def compare(params):
    return _compare(**params)


@lru_cache(maxsize=8)
def _compare(start, end, capital, fees, installments, rebalance):
    params = dict(start=start,end=end,capital=capital,fees=fees,installments=installments,rebalance=rebalance)
    _, days, initial, _ = prepare(params)
    cohorts = {y:{m:[] for m in MODELS} for y in (1,2)}
    for row in selected_entries(params,days):
        years = int(row['years'])
        for model in MODELS:
            result = measure_outcome(date.fromisoformat(row['start']),date.fromisoformat(row['end']),
                                     years,D(row[model]),initial)
            cohorts[years][model].append(result)
    periods = {years: {model: summarize(rows) if rows else dict(count=0,profitable=0,reached=0,
               worstPnl=None,worstReturn=None,worstStart=None,worstEnd=None,worstTies=0)
               for model,rows in models.items()} for years,models in cohorts.items()}
    return dict(parameters=params,firstSession=days[0],lastSession=days[-1],models=MODELS,periods=periods)


def detail(params):
    config, days, initial, _ = prepare(params)
    result = {}
    for model in MODELS:
        settings = dict(config,model=model,step='all')
        if model!='installments':
            settings.pop('installments')
        if model=='trend_120':
            settings['rebalance']='monthly'
        if model == FACTOR_MODEL:
            settings['rebalance']='signal'
        frames = replay(settings)['frames']
        events = []
        for i, row in enumerate(frames[1:]):
            signal = frames[i]
            if not signal['nextPlan']:
                continue
            event = dict(day=row['date'], plan=signal['nextPlan'], orders=row['orders'])
            if model == FACTOR_MODEL:
                decision = signal['decision']
                previous = frames[i-1]['decision'] if i else None
                event['decision'] = decision
                event['previousVotes'] = previous['votes'] if previous else None
                event['changedFactors'] = [current['key'] for current, prior in
                    zip(decision['factors'], previous['factors'], strict=True)
                    if current['passed'] != prior['passed']] if previous else []
            events.append(event)
        result[model] = dict(pnl=frames[-1]['equity']-initial, events=events,
                             curve=[dict(date=r['date'],equity=r['equity'],drawdown=r['drawdown']) for r in frames])
    return dict(parameters=params,start=days[0],end=days[-1],models=result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', required=True, type=Path)
    args = parser.parse_args()
    with args.export.open('x',encoding='utf-8',newline='') as out:
        writer = csv.DictWriter(out,fieldnames=['start','end','years',*MODELS],lineterminator='\n')
        writer.writeheader()
        writer.writerows(calculate_entries(DEFAULTS))
