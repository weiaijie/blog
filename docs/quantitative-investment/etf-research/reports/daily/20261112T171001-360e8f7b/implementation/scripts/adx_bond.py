"""Paired ADX/bond accounts, exact attribution, years and non-overlapping chains."""
import argparse
from bisect import bisect_left
from collections import defaultdict
from datetime import date
from decimal import Decimal as D
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re

import interactive_backtest as work
import factor_lab
from build_entry_windows import entry_schedule, measure_outcome, summarize
from compare_three_markets import anniversary
from method_windows import prepare
from overlay_attribution import cumulative_ledger, interval, PARTS
from technical_factors import technical_schedule, schedule_from_decisions

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/2026-11-11-adx-bond'
DEFAULTS=factor_lab.DEFAULTS
ADX='multifactor_adx_v1'
MODELS={ADX:'ADX原规则','bonds':'只持国债','balanced':'一次建仓股债各半'}
SYMBOLS=('510300','511010')
CENT=D('.01')
ARCHIVE_SHA256='c1f08383d2bd9787d77c9ac6f64398251df19c6fa7c1da59c9ce345c15c7848f'
MATH_LABELS={
    'allocation':'平均股票敞口（事后）','timing':'持股时段匹配（事后）',
    'execution':'开盘换仓后的日内贡献','capital':'历史盈亏形成的资本差',
    'cash':'现金及应收的国债机会成本差','entitlement':'分红登记权益差',
    'commission':'佣金差','slippage':'滑点差','rounding':'显示舍入差额',
}
RISK_LABELS={'stockDown':'股票下跌日的股票贡献差','stockUp':'股票上涨日的股票贡献差',
             'stockFlat':'股票平盘日的股票贡献差','bonds':'国债价格和分红贡献差',
             'commission':'佣金差','slippage':'滑点差','rounding':'显示舍入差额'}


def context(params):
    _,days,initial,simulate=prepare(factor_lab.parameters(params))
    base,_,bars,_=work.inputs()
    history=base.sessions[:base.sessions.index(days[0])]
    tape,_=technical_schedule(history,days,days,bars,base.dividends,ADX)
    return days,initial,simulate,base,bars,tape


def accounts(days,simulate,tape,bars,events):
    decisions={d:dict(tape[d]) for d in days}
    schedule=schedule_from_decisions(decisions,days)
    books={ADX:simulate(days,schedule=schedule),
           'bonds':simulate(days,schedule={days[1]:dict(denominators={'511010':1})}),
           'balanced':simulate(days,schedule={days[1]:dict(denominators={'510300':2,'511010':2})})}
    ledgers={m:cumulative_ledger(*book,bars,events) for m,book in books.items()}
    return books,ledgers,decisions


def pieces(prefix,previous,day):
    return {s:{k:prefix[day][1][s][k]-prefix[previous][1][s][k] for k in PARTS} for s in SYMBOLS}


def primitives(books,ledgers,bars,events):
    """Daily exact trade and entitlement effects, before choosing any mean weight."""
    cash=defaultdict(lambda:D(0))
    for e in events:
        cash[e.symbol,e.ex_date]+=e.per_share
    indexed={m:{r['date']:r for r in book[0]} for m,book in books.items()}
    rows=[]
    days=list(indexed[ADX])
    for before,day in zip(days,days[1:]):
        a,b=indexed[ADX][before],indexed['bonds'][before]
        rs=(bars['510300'][day].close+cash['510300',day])/bars['510300'][before].close-1
        rb=(bars['511010'][day].close+cash['511010',day])/bars['511010'][before].close-1
        parts={m:pieces(ledgers[m],before,day) for m in MODELS}
        diff={s:{k:parts[ADX][s][k]-parts['bonds'][s][k] for k in PARTS} for s in SYMBOLS}
        riskdiff={s:{k:parts[ADX][s][k]-parts['balanced'][s][k] for k in PARTS} for s in SYMBOLS}
        gap=sum(sum(v.values()) for v in diff.values())
        old_gap=a['equity']-b['equity']
        if gap!=(indexed[ADX][day]['equity']-indexed['bonds'][day]['equity'])-old_gap:
            raise ValueError('Daily paired account mismatch')
        stock_value=a['units_510300']*bars['510300'][before].close
        execution=D(0)
        for s in SYMBOLS:
            adelta=indexed[ADX][day]['units_'+s]-a['units_'+s]
            bdelta=indexed['bonds'][day]['units_'+s]-b['units_'+s]
            execution+=(adelta-bdelta)*(bars[s][day].close-bars[s][day].open)
        dividend=sum(diff[s]['dividend'] for s in SYMBOLS)
        entitlement=dividend-sum((a['units_'+s]-b['units_'+s])*cash[s,day] for s in SYMBOLS)
        components=dict(execution=execution,capital=old_gap*rb,
            cash=-(a['cash']+a['receivables']-b['cash']-b['receivables'])*rb,
            entitlement=entitlement,commission=sum(diff[s]['commission'] for s in SYMBOLS),
            slippage=sum(diff[s]['slippage'] for s in SYMBOLS))
        held=stock_value*(rs-rb)
        if abs(held+sum(components.values())-gap)>D('1e-16'):
            raise ValueError('Exposure attribution does not reconcile')
        risk=dict(stockDown=D(0),stockUp=D(0),stockFlat=D(0),
                  bonds=riskdiff['511010']['price']+riskdiff['511010']['dividend'],
                  commission=sum(riskdiff[s]['commission'] for s in SYMBOLS),
                  slippage=sum(riskdiff[s]['slippage'] for s in SYMBOLS))
        risk['stockDown' if rs<0 else 'stockUp' if rs>0 else 'stockFlat']=riskdiff['510300']['price']+riskdiff['510300']['dividend']
        rows.append(dict(date=day,etfDifference=diff,equity=a['equity'],stockValue=stock_value,unitSpread=a['equity']*(rs-rb),
                         heldSpread=held,gap=gap,components=components,risk=risk))
    return rows


def rounded(parts,expected):
    result={k:v.quantize(CENT) for k,v in parts.items()}
    result['rounding']=expected.quantize(CENT)-sum(result.values())
    if sum(result.values())!=expected.quantize(CENT):
        raise ValueError('Rounded components do not reconcile')
    return result


def decomposition(rows):
    if not rows:raise ValueError('Attribution needs a return interval')
    mean=sum(r['stockValue'] for r in rows)/sum(r['equity'] for r in rows)
    parts={k:sum(r['components'][k] for r in rows) for k in rows[0]['components']}
    parts['allocation']=mean*sum(r['unitSpread'] for r in rows)
    parts['timing']=sum(r['heldSpread'] for r in rows)-parts['allocation']
    gap=sum(r['gap'] for r in rows)
    if abs(sum(parts.values())-gap)>D('1e-15'):
        raise ValueError('Period exposure attribution differs')
    risk={k:sum(r['risk'][k] for r in rows) for k in rows[0]['risk']}
    return dict(meanStockWeight=mean,gap=gap,components=rounded(parts,gap),
                timingAfterCosts=sum(parts[k] for k in ('timing','execution','commission','slippage')).quantize(CENT),
                riskComponents=rounded(risk,sum(risk.values())),gapBalanced=sum(risk.values()))


def period(books,ledgers,raw,days):
    start,end=days[0],days[-1]
    sliced=[r for r in raw if start<r['date']<=end]
    attribution=interval(ledgers,start,end)
    comparison=decomposition(sliced)
    if comparison['gap']!=attribution['differences'][ADX+'-bonds']['accountChange']:
        raise ValueError('Bond comparison mismatch')
    if comparison['gapBalanced']!=attribution['differences'][ADX+'-balanced']['accountChange']:
        raise ValueError('Balanced comparison mismatch')
    summaries={}
    for m,(daily,orders) in books.items():
        rows=[r for r in daily if start<=r['date']<=end]
        trades=[o for o in orders if start<o['day']<=end]
        summary=factor_lab.account_summary(rows,trades,rows[0]['equity'])
        summary.update(startingEquity=rows[0]['equity'],endingEquity=rows[-1]['equity'],
                       totalReturn=rows[-1]['equity']/rows[0]['equity']-1)
        summaries[m]=summary
    return dict(start=str(start),end=str(end),accounts=summaries,**comparison,attribution=attribution)


def compact(row,years):
    return dict(start=row['start'],end=row['end'],years=years,
                equities={m:r['endingEquity'] for m,r in row['accounts'].items()},
                drawdowns={m:r['maxDrawdown'] for m,r in row['accounts'].items()},
                **{k:row[k] for k in ('gap','gapBalanced','meanStockWeight','components','timingAfterCosts','riskComponents')})


def cohort(rows,initial):
    models={}
    for m in MODELS:
        outcomes=[measure_outcome(date.fromisoformat(r['start']),date.fromisoformat(r['end']),r['years'],D(r['equities'][m]),initial) for r in rows]
        models[m]=summarize(outcomes) if rows else dict(count=0,profitable=0,reached=0,worstPnl=None)
    gaps=[D(r['gap']) for r in rows]
    def extreme(reverse):
        return sorted(rows,key=lambda r:(-D(r['gap']) if reverse else D(r['gap']),r['start']))[0] if rows else None
    return dict(count=len(rows),models=models,beatBonds=sum(g>0 for g in gaps),tieBonds=sum(g==0 for g in gaps),
                lagBonds=sum(g<0 for g in gaps),beatBalanced=sum(D(r['gapBalanced'])>0 for r in rows),
                positiveTimingAfterCosts=sum(D(r['timingAfterCosts'])>0 for r in rows),
                bestGap=extreme(True),worstGap=extreme(False))


def chains(days,rows,initial):
    lookup={(r['start'],r['years']):r for r in rows}
    starts=[days[0]]
    first_month=days[0].year*12+days[0].month-1
    for offset in range(1,12):
        month=first_month+offset
        candidate=next((d for d in days if d.year*12+d.month-1==month),None)
        if candidate:starts.append(candidate)
    result={}
    for years in (1,2):
        result[years]=[]
        for anchor in starts:
            selected=[];start=anchor
            while (str(start),years) in lookup:
                row=lookup[str(start),years]
                selected.append(row);start=date.fromisoformat(row['end'])
            result[years].append(dict(anchor=str(anchor),windows=selected,summary=cohort(selected,initial),
                 immatureTail=dict(start=str(start),end=str(days[-1])) if start<days[-1] else None))
    return result


def annuals(books,ledgers,raw,days,params):
    result=[]
    for year in sorted({d.year for d in days}):
        first=next(i for i,d in enumerate(days) if d.year==year)
        last=max(i for i,d in enumerate(days) if d.year==year)
        anchor=max(0,first-1)
        if last<=anchor:continue
        row=period(books,ledgers,raw,days[anchor:last+1])
        row.update(year=year,complete=params['start']<=f'{year}-01-01' and params['end']>=f'{year}-12-31',
                   firstReturnSession=str(days[anchor+1]))
        result.append(row)
    return result


def calculate(params):
    days,initial,simulate,base,bars,tape=context(params)
    books,ledgers,_=accounts(days,simulate,tape,bars,base.dividends)
    raw=primitives(books,ledgers,bars,base.dividends)
    full=period(books,ledgers,raw,days)
    yearly=annuals(books,ledgers,raw,days,params)
    old=json.loads((factor_lab.REPORT/'comparison.json').read_text()) if params==DEFAULTS else None
    archive={(r['start'],r['years']):r for r in old['entries']} if old else None
    rows=[]
    for sessions,endpoints in entry_schedule(days):
        books,ledgers,_=accounts(sessions,simulate,tape,bars,base.dividends)
        raw=primitives(books,ledgers,bars,base.dividends)
        for years,i in endpoints.items():
            row=compact(period(books,ledgers,raw,sessions[:i+1]),years)
            if archive is not None and D(archive[row['start'],years][ADX])!=row['equities'][ADX]:
                raise ValueError('ADX endpoint differs from frozen research')
            rows.append(row)
    periods={y:cohort([r for r in rows if r['years']==y],initial) for y in (1,2)}
    entry_years={y:{year:cohort([r for r in rows if r['years']==y and r['start'][:4]==year],initial)
                   for year in sorted({r['start'][:4] for r in rows if r['years']==y})} for y in (1,2)}
    return dict(parameters=params,models=MODELS,mathLabels=MATH_LABELS,riskLabels=RISK_LABELS,
                fullPeriod=full,calendarYears=yearly,periods=periods,entryYears=entry_years,
                nonOverlapping=chains(days,rows,initial),windows=rows,
                limitations='Retrospective attribution; average exposure uses the completed interval. Chains overlap across anchors. Not evidence of predictive skill.')


@lru_cache(maxsize=8)
def _compare(start,end,capital,fees):
    params=dict(start=start,end=end,capital=capital,fees=fees)
    prepare(factor_lab.parameters(params))
    if params==DEFAULTS:
        body=(REPORT/'comparison.json').read_bytes()
        if hashlib.sha256(body).hexdigest()!=ARCHIVE_SHA256:raise ValueError('ADX/bond archive checksum differs')
        return json.loads(body)
    return calculate(params)


def compare(params):
    return _compare(**params)


def detail(params):
    original={k:params[k] for k in DEFAULTS}
    days,initial,simulate,base,bars,tape=context(original)
    books,ledgers,decisions=accounts(days,simulate,tape,bars,base.dividends)
    raw=primitives(books,ledgers,bars,base.dividends)
    selected=days
    if 'year' in params:
        if not re.fullmatch(r'[0-9]{4}',params['year']):raise work.InputError('年度格式须为四位年份。')
        year=int(params['year'])
        candidates=[i for i,d in enumerate(days) if d.year==year]
        if not candidates or candidates[-1]<=max(0,candidates[0]-1):raise work.InputError('所选年度没有完整收益区间。')
        selected=days[max(0,candidates[0]-1):candidates[-1]+1]
    row=period(books,ledgers,raw,selected)
    curves={}
    for m,(daily,orders) in books.items():
        subset=[r for r in daily if selected[0]<=r['date']<=selected[-1]]
        peak=subset[0]['equity']
        curves[m]=[]
        for r in subset:
            peak=max(peak,r['equity'])
            curves[m].append(dict(date=r['date'],equity=r['equity'],nav=r['equity']/subset[0]['equity'],
                                 drawdown=r['equity']/peak-1))
    daily=[]
    total=D(0)
    running={k:D(0) for k in MATH_LABELS if k!='rounding'}
    shown=dict(running)
    for rawday in raw:
        if not selected[0]<rawday['date']<=selected[-1]:continue
        c=dict(rawday['components'])
        c['allocation']=row['meanStockWeight']*rawday['unitSpread']
        c['timing']=rawday['heldSpread']-c['allocation']
        total+=rawday['gap']
        day=rawday['date']
        for key,value in c.items():running[key]+=value
        current={k:v.quantize(CENT) for k,v in running.items()}
        displayed={k:current[k]-shown[k] for k in current}
        displayed['rounding']=rawday['gap'].quantize(CENT)-sum(displayed.values())
        shown=current
        previous=days[days.index(day)-1]
        daily.append(dict(date=day,gap=rawday['gap'],cumulativeGap=total,components=displayed,
            decision=decisions[day],executionDecision=decisions[previous],etfDifference=rawday['etfDifference'],
            accounts={m:dict(holdings={s:next(r for r in book[0] if r['date']==day)['units_'+s] for s in SYMBOLS},
                            orders=[o for o in book[1] if o['day']==day]) for m,book in books.items()}))
    if total!=row['gap']:raise ValueError('Daily relative P&L mismatch')
    if any(sum(d['components'][k] for d in daily)!=v for k,v in row['components'].items()):
        raise ValueError('Daily displayed components do not sum to period attribution')
    return dict(parameters=params,mode='continuous_year' if 'year' in params else 'fresh_cash',
                models=MODELS,mathLabels=MATH_LABELS,riskLabels=RISK_LABELS,summary=row,curves=curves,daily=daily)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--detail',action='store_true')
    parser.add_argument('--year')
    for key,value in DEFAULTS.items():parser.add_argument('--'+key,default=value)
    args=parser.parse_args()
    params={k:getattr(args,k) for k in DEFAULTS}
    if args.year:
        if not args.detail:parser.error('--year requires --detail')
        params['year']=args.year
    result=detail(params) if args.detail else calculate(params)
    with args.output.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n')
