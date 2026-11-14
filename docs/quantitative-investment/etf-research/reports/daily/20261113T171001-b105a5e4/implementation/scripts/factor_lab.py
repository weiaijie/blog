"""Same-parameter research of three independent technical gates."""
import argparse
from decimal import Decimal as D
from functools import lru_cache
from research_profile import profile_cache
import json
import hashlib
from pathlib import Path

import interactive_backtest as work
from build_entry_windows import entry_schedule, measure_outcome, summarize
from method_windows import DEFAULTS as METHOD_DEFAULTS, prepare, archived_entries
from model_replay import replay
from multifactor_strategy import MODEL, factor_schedule
from overlay_attribution import cumulative_ledger
from technical_factors import MODELS as VARIANTS, technical_schedule, schedule_from_decisions, volume_inputs

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT/'reports/2026-11-11-technical-factors'
ARCHIVE_SHA256 = 'da84cd32c7a2f62eba959fcf10072ea996789a72c1ace675902661e172444659'
DEFAULTS = {k:METHOD_DEFAULTS[k] for k in ('start','end','capital','fees')}
MODELS = {MODEL:'原三因子 v1', **VARIANTS}


def parameters(params):
    return dict(params,installments='3',rebalance='hold')


def replay_params(params, model):
    return dict(params,weights='1,0,0,1',rebalance='signal',model=model,step='all')


def account_summary(ledger, orders, initial):
    peak = initial
    dd = D(0)
    for row in ledger:
        peak = max(peak,row['equity'])
        dd = min(dd,row['equity']/peak-1)
    commission = sum((o['fee'] for o in orders), D(0))
    slippage = sum((D(o['filled'])*(o['modeled_price']-o['open'])*(1 if o['side']=='buy' else -1)
                    for o in orders if o['filled']), D(0))
    return dict(pnl=ledger[-1]['equity']-initial, maxDrawdown=dd,
                trades=sum(o['filled']>0 for o in orders),commission=commission,slippage=slippage,
                stockHoldingDays=sum(r['units_510300']>0 for r in ledger),observations=len(ledger))


def calculate(params):
    _, days, initial, simulate = prepare(parameters(params))
    base, _, bars, _ = work.inputs()
    history = base.sessions[:base.sessions.index(days[0])]
    volumes, audit = volume_inputs()
    tapes, full = {}, {}
    for model in MODELS:
        if model == MODEL:
            decisions, schedule = factor_schedule(history,days,days,bars,base.dividends)
        else:
            decisions, schedule = technical_schedule(history,days,days,bars,base.dividends,model,volumes)
        tapes[model] = decisions
        ledger, orders = simulate(days,schedule=schedule)
        cumulative_ledger(ledger,orders,bars,base.dividends)
        full[model] = account_summary(ledger,orders,initial)
        full[model]['balancedTargetDays'] = sum(d['regime']=='balanced' for d in decisions.values())
    cohorts = {y:{m:[] for m in MODELS} for y in (1,2)}
    entries = []
    archive = archived_entries() if params == DEFAULTS else None
    for sessions, endpoints in entry_schedule(days):
        books = {}
        for model in MODELS:
            # Rebuild initial instruction for every cash-start account; never carry holdings in.
            decisions = {d:dict(tapes[model][d]) for d in sessions}
            schedule = schedule_from_decisions(decisions,sessions)
            books[model] = simulate(sessions,schedule=schedule)[0]
        for years, offset in endpoints.items():
            row = dict(start=str(sessions[0]),end=str(sessions[offset]),years=years)
            for model in MODELS:
                equity = books[model][offset]['equity']
                if model == MODEL and archive is not None:
                    old = archive[row['start'],years]
                    if old['end'] != row['end'] or D(old[MODEL]) != equity:
                        raise ValueError('Frozen baseline maturity changed')
                row[model] = str(equity)
                cohorts[years][model].append(measure_outcome(sessions[0],sessions[offset],years,equity,initial))
            entries.append(row)
    periods = {}
    for years, groups in cohorts.items():
        periods[years] = {}
        for model, rows in groups.items():
            stats = summarize(rows) if rows else dict(count=0,profitable=0,reached=0,worstPnl=None,worstStart=None,worstEnd=None)
            stats.update(losing=sum(r['pnl']<0 for r in rows),flat=sum(r['pnl']==0 for r in rows))
            if rows:
                baseline = cohorts[years][MODEL]
                stats['beatBaseline'] = sum(r['pnl']>b['pnl'] for r,b in zip(rows,baseline,strict=True))
            periods[years][model] = stats
    bond_ledger,bond_orders = simulate(days,schedule={days[1]:dict(denominators={'511010':1})})
    cumulative_ledger(bond_ledger,bond_orders,bars,base.dividends)
    bond_reference = account_summary(bond_ledger,bond_orders,initial)
    return dict(parameters=params,models=MODELS,periods=periods,fullPeriod=full,bondReference=bond_reference,volumeAudit=audit,
                firstSession=days[0],lastSession=days[-1],entries=entries,
                caveat='Overlapping retrospective windows, not independent probabilities or out-of-sample evidence.')


@profile_cache(maxsize=16)
def _compare(start,end,capital,fees):
    params = dict(start=start,end=end,capital=capital,fees=fees)
    prepare(parameters(params))
    if params == DEFAULTS:
        body = (REPORT/'comparison.json').read_bytes()
        if hashlib.sha256(body).hexdigest() != ARCHIVE_SHA256:
            raise ValueError('Published technical comparison changed; verify the archive')
        data = json.loads(body)
    else:
        data = calculate(params)
    return {k:v for k,v in data.items() if k!='entries'}


def compare(params):
    return _compare(**params)


def detail(params):
    prepare(parameters(params))
    result = {}
    for model in MODELS:
        frames = replay(replay_params(params,model))['frames']
        events = []
        for i, row in enumerate(frames):
            if row['nextPlan'] or row['orders']:
                events.append(dict(date=row['date'],decision=row['decision'],nextPlan=row['nextPlan'],
                                   orders=row['orders'],holdings=row['holdings'],equity=row['equity']))
        result[model] = dict(pnl=frames[-1]['pnl'],maxDrawdown=min(f['drawdown'] for f in frames),
                            curve=[dict(date=f['date'],equity=f['equity'],drawdown=f['drawdown']) for f in frames],
                            events=events)
    return dict(parameters=params,models=result)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--detail',action='store_true')
    for key,value in DEFAULTS.items():
        parser.add_argument('--'+key,default=value)
    args=parser.parse_args()
    params={k:getattr(args,k) for k in DEFAULTS}
    result=detail(params) if args.detail else calculate(params)
    text=json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n'
    if args.output:
        if args.output.exists():
            raise ValueError('Refuse overwriting research evidence')
        args.output.write_text(text,encoding='utf-8')
    else:
        print(text)
