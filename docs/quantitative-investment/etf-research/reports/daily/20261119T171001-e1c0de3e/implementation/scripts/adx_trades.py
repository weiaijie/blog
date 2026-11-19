"""Actual holding episodes and fixed-signal cost diagnostics, research only."""
import argparse
from collections import defaultdict
from datetime import date
from decimal import Decimal as D
from functools import lru_cache
import hashlib
import json
from pathlib import Path

import adx_bond as audit
import factor_lab
import interactive_backtest as work
from build_entry_windows import entry_schedule, measure_outcome, summarize
from etf_research.accounting import Costs
from etf_research.baselines import SCENARIOS
from overlay_attribution import cumulative_ledger, interval, daily_gap
from technical_factors import schedule_from_decisions

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/2026-11-12-adx-trades'
DEFAULTS={k:v for k,v in audit.DEFAULTS.items() if k!='fees'}
FEES={'low':'低费用','base':'基准费用','high':'高费用','zero':'零成本诊断'}
MODELS={audit.ADX:'ADX原规则','bonds':'只持国债'}
ZERO=Costs(D(0),D(0),D(0),D(0))
ARCHIVE_SHA256='6ef7b9d1697f3f4183f9d39c4ac9d07257025a59d906a88768973c13bba1819d'


def setup(params):
    return audit.context(dict(params,fees='base'))


def books_for(days,simulate,tape,fees):
    decisions={d:dict(tape[d]) for d in days}
    schedule=schedule_from_decisions(decisions,days)
    costs=ZERO if fees=='zero' else SCENARIOS[fees]
    return {audit.ADX:simulate(days,schedule=schedule,costs=costs),
            'bonds':simulate(days,schedule={days[1]:dict(denominators={'511010':1})},costs=costs)},decisions


def costs_to(orders,days):
    daily=defaultdict(lambda:dict(commission=D(0),slippage=D(0)))
    for o in orders:
        daily[o['day']]['commission']+=o['fee']
        daily[o['day']]['slippage']+=o['filled']*(o['modeled_price']-o['open'])*(1 if o['side']=='buy' else -1)
    running=dict(commission=D(0),slippage=D(0));result={}
    for day in days:
        for k in running:running[k]+=daily[day][k]
        result[day]=dict(running)
    return result


def endpoint(books,costs,index):
    accounts={m:dict(equity=rows[index]['equity'],**costs[m][rows[index]['date']]) for m,(rows,_) in books.items()}
    a,b=accounts.values()
    gap=a['equity']-b['equity']
    extra=sum(a[k]-b[k] for k in ('commission','slippage'))
    return dict(accounts=accounts,gap=gap,extraCosts=extra,fixedFillGrossGap=gap+extra)


def bridge(scenarios):
    zero=scenarios['zero']['gap']
    for row in scenarios.values():
        row['zeroReplayGap']=zero
        row['pathEffect']=zero-row['fixedFillGrossGap']
        row['zeroReplayImprovement']=zero-row['gap']
        if row['extraCosts']+row['pathEffect']!=row['zeroReplayImprovement']:
            raise ValueError('Cost bridge does not reconcile')
    return scenarios


def cohort(rows,initial,fees):
    selected=[r['scenarios'][fees] for r in rows]
    accounts={}
    for m in MODELS:
        outcomes=[measure_outcome(date.fromisoformat(r['start']),date.fromisoformat(r['end']),r['years'],
            D(r['scenarios'][fees]['accounts'][m]['equity']),initial) for r in rows]
        accounts[m]=summarize(outcomes) if rows else dict(count=0,profitable=0,reached=0,worstPnl=None)
    # Disjoint diagnosis of losing net comparisons; zero is kept as its own case.
    return dict(count=len(rows),accounts=accounts,
        beatBonds=sum(D(r['gap'])>0 for r in selected),lagBonds=sum(D(r['gap'])<0 for r in selected),
        tieBonds=sum(D(r['gap'])==0 for r in selected),
        costsReverse=sum(D(r['gap'])<0 and D(r['fixedFillGrossGap'])>0 for r in selected),
        grossAlreadyBehind=sum(D(r['gap'])<0 and D(r['fixedFillGrossGap'])<0 for r in selected),
        grossTied=sum(D(r['gap'])<0 and D(r['fixedFillGrossGap'])==0 for r in selected),
        worstGap=min(rows,key=lambda r:D(r['scenarios'][fees]['gap'])) if rows else None)


def chains(days,rows,initial):
    lookup={(r['start'],r['years']):r for r in rows}
    first=days[0].year*12+days[0].month-1
    anchors=[days[0]]
    for offset in range(1,12):
        d=next((d for d in days if d.year*12+d.month-1==first+offset),None)
        if d:anchors.append(d)
    result={}
    for y in (1,2):
        result[y]=[]
        for anchor in anchors:
            windows=[];start=str(anchor)
            while (start,y) in lookup:
                r=lookup[start,y];windows.append(r);start=r['end']
            result[y].append(dict(anchor=str(anchor),windows=windows,
                summaries={f:cohort(windows,initial,f) for f in FEES},
                immatureTail=dict(start=start,end=str(days[-1])) if start<str(days[-1]) else None))
    return result


def episodes(books,bars,events,decisions):
    """Stock-leg cash flows and disjoint continuous-account interval comparisons."""
    daily,orders=books[audit.ADX];days=[r['date'] for r in daily]
    by_day={r['date']:r for r in daily}
    fills=defaultdict(list)
    for o in orders:fills[o['day']].append(o)
    prefixes={m:cumulative_ledger(*b,bars,events) for m,b in books.items()}
    spans=[];start=None
    for i,r in enumerate(daily):
        if r['units_510300']>0 and start is None:start=i
        if start is not None and r['units_510300']==0:
            spans.append((start,i,True));start=None
    if start is not None:spans.append((start,len(days)-1,False))
    result=[];previous_exit=None
    for first,last,closed in spans:
        day,end=days[first],days[last]
        stock_orders=[o for d in days[first:last+1] for o in fills[d] if o['symbol']=='510300' and o['filled']]
        raw_flow=sum((o['filled']*o['open']*(1 if o['side']=='sell' else -1) for o in stock_orders),D(0))
        price=raw_flow+daily[last]['units_510300']*bars['510300'][end].close
        commission=sum((o['fee'] for o in stock_orders),D(0))
        slippage=sum((o['filled']*(o['modeled_price']-o['open'])*(1 if o['side']=='buy' else -1) for o in stock_orders),D(0))
        dividend=D(0);late=D(0);pending=D(0);entitlements=[]
        for e in events:
            if e.symbol!='510300' or not day<=e.record_date<=end:continue
            amount=by_day[e.record_date]['units_510300']*e.per_share
            if not amount:continue
            if e.ex_date<=days[-1]:
                dividend+=amount
                if e.ex_date>end:late+=amount
            else:pending+=amount
            entitlements.append(dict(recordDate=e.record_date,exDate=e.ex_date,payDate=e.pay_date,amount=amount,
                                     recognized=e.ex_date<=days[-1]))
        gross=price+dividend;net=gross-commission-slippage
        part=interval(prefixes,days[first-1],end)
        gap=part['differences'][audit.ADX+'-bonds']['accountChange']
        held=sum(r['units_510300']>0 for r in daily[first:last+1])
        result.append(dict(id=str(day),entry=day,exit=end if closed else None,through=end,closed=closed,
            anchor=days[first-1],holdingSessions=held,calendarDays=(end-day).days,
            reentryGapSessions=first-previous_exit if previous_exit is not None else None,
            price=price,dividend=dividend,dividendAfterExit=late,pendingDividend=pending,
            commission=commission,slippage=slippage,gross=gross,net=net,pairedGap=gap,
            costsReverseStock=gross>0 and net<0,entitlements=entitlements,
            entryDecision=decisions[days[first-1]],exitDecision=decisions[days[last-1]] if closed else None,
            stockOrders=stock_orders,accountAttribution=part))
        previous_exit=last if closed else None
    stock_total=prefixes[audit.ADX][days[-1]][1]['510300']
    totals=dict(price=sum((r['price'] for r in result),D(0)),dividend=sum((r['dividend'] for r in result),D(0)),
                commission=-sum((r['commission'] for r in result),D(0)),slippage=-sum((r['slippage'] for r in result),D(0)))
    if totals!=stock_total:raise ValueError('Episodes do not reconcile to stock ledger')
    full=interval(prefixes,days[0],days[-1])
    gap=full['differences'][audit.ADX+'-bonds']['accountChange']
    episode_gap=sum((r['pairedGap'] for r in result),D(0))
    bands=[]
    for label,lo,hi in [('1–5',1,5),('6–20',6,20),('21–60',21,60),('61+',61,10**9)]:
        group=[r for r in result if r['closed'] and lo<=r['holdingSessions']<=hi]
        bands.append(dict(label=label,count=len(group),stockNet=sum((r['net'] for r in group),D(0)),
            commission=sum((r['commission'] for r in group),D(0)),slippage=sum((r['slippage'] for r in group),D(0)),
            positiveStock=sum(r['net']>0 for r in group),costsReverseStock=sum(r['costsReverseStock'] for r in group)))
    return dict(episodes=result,closedCount=sum(r['closed'] for r in result),openCount=sum(not r['closed'] for r in result),
        quickReentries=sum(r['reentryGapSessions'] is not None and r['reentryGapSessions']<=5 for r in result),
        stockTotals=totals,holdingBands=bands,episodeGap=episode_gap,outsideEpisodeGap=gap-episode_gap,
        fullGap=gap,fullAttribution=full)


def calculate(params):
    days,initial,simulate,base,bars,tape=setup(params)
    full={};full_end={}
    for f in FEES:
        books,decisions=books_for(days,simulate,tape,f)
        full[f]=episodes(books,bars,base.dividends,decisions)
        prefixes={m:costs_to(o,days) for m,(_,o) in books.items()}
        full_end[f]=endpoint(books,prefixes,-1)
    bridge(full_end)
    rows=[]
    old=audit.compare(audit.DEFAULTS) if params==DEFAULTS else None
    old_rows={(r['start'],int(r['years'])):r for r in old['windows']} if old else {}
    for sessions,ends in entry_schedule(days):
        by_year={y:{} for y in ends}
        for f in FEES:
            books,_=books_for(sessions,simulate,tape,f)
            costs={m:costs_to(o,sessions) for m,(_,o) in books.items()}
            for y,i in ends.items():by_year[y][f]=endpoint(books,costs,i)
        for y,i in ends.items():
            r=dict(start=str(sessions[0]),end=str(sessions[i]),years=y,scenarios=bridge(by_year[y]))
            if old:
                prior=old_rows[r['start'],y]
                for m in MODELS:
                    if D(prior['equities'][m])!=r['scenarios']['base']['accounts'][m]['equity']:
                        raise ValueError('Original base account changed')
            rows.append(r)
    return dict(parameters=params,fees=FEES,models=MODELS,full=full,fullCosts=full_end,windows=rows,
        periods={y:{f:cohort([r for r in rows if r['years']==y],initial,f) for f in FEES} for y in (1,2)},
        nonOverlapping=chains(days,rows,initial),
        signalSha256=hashlib.sha256(work.encode(tape_as_rows(tape))).hexdigest(),
        limitations='Retrospective fixed signals. Fee scenarios change quantities/cash/guards. Zero cost is diagnostic only. Overlapping windows are not independent trials.')


def tape_as_rows(tape):
    return [dict(date=d,decision=decision) for d,decision in tape.items()]


@lru_cache(maxsize=4)
def _compare(start,end,capital):
    params=dict(start=start,end=end,capital=capital)
    setup(params)
    if params==DEFAULTS:
        body=(REPORT/'comparison.json').read_bytes()
        if hashlib.sha256(body).hexdigest()!=ARCHIVE_SHA256:raise ValueError('Trade audit archive changed')
        return json.loads(body)
    return calculate(params)


def compare(params):
    return {k:v for k,v in _compare(**params).items() if k!='windows'}


def detail(params):
    original={k:params[k] for k in DEFAULTS}
    fees=params['fees']
    if fees not in FEES:raise work.InputError('未知费用方案。')
    days,_,simulate,base,bars,tape=setup(original)
    books,decisions=books_for(days,simulate,tape,fees)
    report=episodes(books,bars,base.dividends,decisions)
    selected=None
    if params.get('episode'):
        selected=next((r for r in report['episodes'] if r['id']==params['episode']),None)
        if selected is None:raise work.InputError('该区间和费用下没有这轮实际持仓。')
    start=selected['anchor'] if selected else days[0]
    end=selected['through'] if selected else days[-1]
    subset={m:([r for r in rows if start<=r['date']<=end],o) for m,(rows,o) in books.items()}
    ledgers={m:cumulative_ledger(*b,bars,base.dividends) for m,b in books.items()}
    part=interval(ledgers,start,end)
    slices={m:{d:v for d,v in p.items() if start<=d<=end} for m,p in ledgers.items()}
    gaps=daily_gap(slices[audit.ADX],slices['bonds'],part['differences'][audit.ADX+'-bonds'])
    indexed={m:{r['date']:r for r in book[0]} for m,book in books.items()}
    for r in gaps['days']:
        day=r['date'];i=days.index(day)
        r.update(decision=decisions[day],executionDecision=decisions[days[i-1]] if i else None,
            accounts={m:dict(holdings={s:indexed[m][day]['units_'+s] for s in audit.SYMBOLS},
                equity=indexed[m][day]['equity'],cash=indexed[m][day]['cash'],receivables=indexed[m][day]['receivables'],
                orders=[o for o in book[1] if o['day']==day and day>start]) for m,book in books.items()})
    curves={}
    for m,(daily,_) in subset.items():
        peak=daily[0]['equity'];curves[m]=[]
        for r in daily:
            peak=max(peak,r['equity'])
            curves[m].append(dict(date=r['date'],equity=r['equity'],nav=r['equity']/daily[0]['equity'],drawdown=r['equity']/peak-1))
    return dict(parameters=params,mode='continuous_episode' if selected else 'fresh_cash',episode=selected,
        models=MODELS,attribution=part,curves=curves,daily=gaps,
        note='Episode curves retain original account capital; they are not equal fresh investments.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--detail',action='store_true')
    p.add_argument('--fees',default='base');p.add_argument('--episode')
    for k,v in DEFAULTS.items():p.add_argument('--'+k,default=v)
    a=p.parse_args();params={k:getattr(a,k) for k in DEFAULTS}
    if a.episode and not a.detail:p.error('--episode requires --detail')
    if a.detail:params.update(fees=a.fees,**({'episode':a.episode} if a.episode else {}))
    result=detail(params) if a.detail else calculate(params)
    with a.output.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(result,ensure_ascii=False,indent=2,default=str,allow_nan=False)+'\n')
