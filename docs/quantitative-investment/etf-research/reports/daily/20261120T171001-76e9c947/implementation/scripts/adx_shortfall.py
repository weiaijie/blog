"""Three separate retrospective views of the frozen 321 ADX shortfall windows."""
import argparse
from collections import Counter
from datetime import date
from decimal import Decimal as D
from functools import lru_cache
import hashlib
import json
from pathlib import Path

import adx_bond as audit
import adx_trades as trades
import interactive_backtest as work
from overlay_attribution import cumulative_ledger, interval, daily_gap
from technical_factors import schedule_from_decisions

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/2026-11-12-adx-shortfall'
ARCHIVE_SHA256='1795712994d37c11f0ab8114964acdaa6db9670196df407cfd8c58bb4941738d'
LABELS={'losingStock':'亏损股票轮次：价差＋分红','winningStock':'其余股票轮次：价差＋分红',
        'bondPrice':'相对纯债的国债价差','bondDividend':'相对纯债的国债分红',
        'commission':'额外佣金的负贡献','slippage':'额外滑点的负贡献'}


@lru_cache(maxsize=1)
def selected():
    body=(trades.REPORT/'comparison.json').read_bytes()
    if hashlib.sha256(body).hexdigest()!=trades.ARCHIVE_SHA256:raise ValueError('Parent window archive changed')
    source=json.loads(body)
    rows=[r for r in source['windows'] if r['years']==2 and D(r['scenarios']['base']['gap'])<0
          and D(r['scenarios']['base']['fixedFillGrossGap'])<0]
    if len(rows)!=321 or source['parameters']!=trades.DEFAULTS:raise ValueError('Frozen cohort identity changed')
    return {r['start']:r for r in rows}


def cancel_short_gaps(days,decisions,episodes):
    schedule=schedule_from_decisions({d:dict(decisions[d]) for d in days},days)
    pairs=[];removed=set()
    for previous,current in zip(episodes,episodes[1:]):
        if previous['exit'] is None:raise ValueError('Open episode before a later entry')
        gap=days.index(current['entry'])-days.index(previous['exit'])
        if gap<=5:
            dates=[d for d in schedule if previous['exit']<=d<=current['entry']]
            removed.update(dates)
            pairs.append(dict(exit=previous['exit'],reentry=current['entry'],gapSessions=gap,
                removedTargets=dates,exitDecision=previous['exitDecision'],entryDecision=current['entryDecision']))
    return {d:v for d,v in schedule.items() if d not in removed},pairs


def missed_opportunity(days,books,ledgers):
    """Balanced comparator opportunity on fully flat days after a filled exit only."""
    adx=books[audit.ADX][0];after_exit=False;marked=[]
    totals=dict(stockUp=D(0),stockDown=D(0),stockFlat=D(0),bond=D(0),commission=D(0),slippage=D(0))
    for i in range(1,len(days)):
        before,day=days[i-1],days[i]
        old,new=adx[i-1]['units_510300'],adx[i]['units_510300']
        if old>0 and new==0:after_exit=True
        if not (after_exit and old==0 and new==0):continue
        parts={m:audit.pieces(ledgers[m],before,day) for m in (audit.ADX,'balanced')}
        target,reference=parts[audit.ADX],parts['balanced']
        reference_stock=reference['510300']['price']+reference['510300']['dividend']
        delta_stock=target['510300']['price']+target['510300']['dividend']-reference_stock
        key='stockUp' if reference_stock>0 else 'stockDown' if reference_stock<0 else 'stockFlat'
        c=dict.fromkeys(totals,D(0));c[key]=delta_stock
        c['bond']=sum(target['511010'][k]-reference['511010'][k] for k in ('price','dividend'))
        for k in ('commission','slippage'):c[k]=sum(target[s][k]-reference[s][k] for s in audit.SYMBOLS)
        actual=(ledgers[audit.ADX][day][0]-ledgers[audit.ADX][before][0])-(ledgers['balanced'][day][0]-ledgers['balanced'][before][0])
        if sum(c.values())!=actual:raise ValueError('Missed opportunity daily account mismatch')
        for k in totals:totals[k]+=c[k]
        marked.append(dict(date=day,components=c,accountGap=actual))
    full=(ledgers[audit.ADX][days[-1]][0]-ledgers[audit.ADX][days[0]][0])-(ledgers['balanced'][days[-1]][0]-ledgers['balanced'][days[0]][0])
    return dict(days=len(marked),components=totals,selectedDaysGap=sum(totals.values()),
                otherDaysGap=full-sum(totals.values()),fullBalancedGap=full,marked=marked)


def analyze(source,context=None,include_daily=False):
    full_days,_,simulate,base,bars,tape=context or trades.setup(trades.DEFAULTS)
    start,end=map(date.fromisoformat,(source['start'],source['end']))
    days=tuple(d for d in full_days if start<=d<=end)
    books,ledgers,decisions=audit.accounts(days,simulate,tape,bars,base.dividends)
    base_books={m:books[m] for m in trades.MODELS}
    rounds=trades.episodes(base_books,bars,base.dividends,decisions)
    full=interval(ledgers,days[0],days[-1]);diff=full['differences'][audit.ADX+'-bonds']
    gross=diff['totals']['price']+diff['totals']['dividend']
    expected=source['scenarios']['base']
    if diff['accountChange']!=D(expected['gap']) or gross!=D(expected['fixedFillGrossGap']):
        raise ValueError('321-window replay differs from frozen parent')
    for m in trades.MODELS:
        if books[m][0][-1]['equity']!=D(expected['accounts'][m]['equity']):raise ValueError('Endpoint differs')
    components=dict(losingStock=sum((e['gross'] for e in rounds['episodes'] if e['gross']<0),D(0)),
        winningStock=sum((e['gross'] for e in rounds['episodes'] if e['gross']>=0),D(0)),
        bondPrice=diff['byEtf']['511010']['price'],bondDividend=diff['byEtf']['511010']['dividend'],
        commission=diff['totals']['commission'],slippage=diff['totals']['slippage'])
    if sum(components.values())!=diff['accountChange'] or sum(components[k] for k in ('losingStock','winningStock','bondPrice','bondDividend'))!=gross:
        raise ValueError('Round attribution mismatch')
    opportunity=missed_opportunity(days,books,ledgers)
    schedule,pairs=cancel_short_gaps(days,decisions,rounds['episodes'])
    alternative=simulate(days,schedule=schedule)
    alt_ledger=cumulative_ledger(*alternative,bars,base.dividends)
    original=ledgers[audit.ADX][days[-1]][1];counter=alt_ledger[days[-1]][1]
    costs_saved=sum(counter[s][k]-original[s][k] for s in audit.SYMBOLS for k in ('commission','slippage'))
    price_path=sum(counter[s][k]-original[s][k] for s in audit.SYMBOLS for k in ('price','dividend'))
    improvement=alternative[0][-1]['equity']-books[audit.ADX][0][-1]['equity']
    if costs_saved+price_path!=improvement:raise ValueError('Short-gap counterfactual does not reconcile')
    if not pairs and improvement:raise ValueError('No removed targets must preserve original result')
    churn=dict(pairs=len(pairs),gaps=[dict(exit=p['exit'],reentry=p['reentry']) for p in pairs],
        removedBatches=len({d for p in pairs for d in p['removedTargets']}),
        netImprovement=improvement,costsSaved=costs_saved,priceDividendPath=price_path,
        alternativeNetGap=diff['accountChange']+improvement,alternativeGrossGap=gross+price_path,
        originalShortRounds=sum(e['closed'] and e['holdingSessions']<=5 for e in rounds['episodes']),
        originalShortStockGross=sum((e['gross'] for e in rounds['episodes'] if e['closed'] and e['holdingSessions']<=5),D(0)))
    row=dict(start=source['start'],end=source['end'],netGap=diff['accountChange'],grossGap=gross,
        components=components,stockGross=components['losingStock']+components['winningStock'],
        losingRounds=sum(e['gross']<0 for e in rounds['episodes']),rounds=len(rounds['episodes']),
        openRounds=rounds['openCount'],opportunity={k:v for k,v in opportunity.items() if k!='marked'},churn=churn)
    if not include_daily:return row
    # Both daily gap and costs add-back are exact Decimal cumulative accounting.
    detail=trades.detail(dict(trades.DEFAULTS,start=source['start'],end=source['end'],fees='base'))
    running=D(0)
    previous_decision=None
    for day in detail['daily']['days']:
        added=-(day['totals']['commission']+day['totals']['slippage'])
        day['grossChange']=day['change']+added;running+=day['grossChange'];day['cumulativeGrossGap']=running
        current=day['executionDecision']
        prior={f['key']:f['passed'] for f in previous_decision['factors']} if previous_decision else {}
        day['changedFactors']=[f['label'] for f in current['factors'] if f['key'] in prior and f['passed']!=prior[f['key']]] if current else []
        previous_decision=current
    if running!=gross:raise ValueError('Daily gross contribution mismatch')
    alt_peak=alternative[0][0]['equity'];alt_curve=[]
    for r in alternative[0]:
        alt_peak=max(alt_peak,r['equity'])
        alt_curve.append(dict(date=r['date'],equity=r['equity'],nav=r['equity']/alternative[0][0]['equity'],drawdown=r['equity']/alt_peak-1))
    cf_prefix={audit.ADX:ledgers[audit.ADX],'alternative':alt_ledger}
    cf_part=interval(cf_prefix,days[0],days[-1])
    cf_daily=daily_gap(alt_ledger,ledgers[audit.ADX],cf_part['differences']['alternative-'+audit.ADX])
    for r in cf_daily['days']:r['orders']=[o for o in alternative[1] if o['day']==r['date']]
    return dict(summary=row,parameters=dict(trades.DEFAULTS,start=source['start'],end=source['end'],fees='base'),
        labels=LABELS,replay=detail,episodes=rounds['episodes'],missedDays=opportunity['marked'],
        counterfactual=dict(pairs=pairs,curve=alt_curve,daily=cf_daily,attribution=cf_part,
            warning='Uses future re-entry dates to cancel historical targets; not an executable strategy.'))


def calculate():
    context=trades.setup(trades.DEFAULTS)
    rows=[analyze(source,context) for source in selected().values()]
    rows.sort(key=lambda r:(r['grossGap'],r['start']))
    counts=dict(count=len(rows),negativeStock=sum(r['stockGross']<0 for r in rows),
        positiveStock=sum(r['stockGross']>0 for r in rows),flatStock=sum(r['stockGross']==0 for r in rows),
        negativeBond=sum(r['components']['bondPrice']+r['components']['bondDividend']<0 for r in rows),
        missedRise=sum(r['opportunity']['components']['stockUp']<0 for r in rows),
        shortGapWindows=sum(r['churn']['pairs']>0 for r in rows),
        cancellationGrossBetter=sum(r['churn']['priceDividendPath']>0 for r in rows),
        cancellationGrossWorse=sum(r['churn']['priceDividendPath']<0 for r in rows),
        cancellationGrossEqual=sum(r['churn']['priceDividendPath']==0 for r in rows),
        cancellationGrossStillBehind=sum(r['churn']['alternativeGrossGap']<0 for r in rows),
        cancellationNetStillBehind=sum(r['churn']['alternativeNetGap']<0 for r in rows))
    return dict(parameters=trades.DEFAULTS,fees='base',labels=LABELS,parentSha256=trades.ARCHIVE_SHA256,
        counts=counts,entryYears=dict(sorted(Counter(r['start'][:4] for r in rows).items())),windows=rows,
        shortGapEvents=[dict(exit=str(a),reentry=str(b),windowCount=n) for (a,b),n in
            sorted(Counter((p['exit'],p['reentry']) for r in rows for p in r['churn']['gaps']).items())],
        worstStarts=[r['start'] for r in rows[:5]],
        diagnosticStarts=dict(missedRise=min(rows,key=lambda r:(r['opportunity']['components']['stockUp'],r['start']))['start'],
            cancellationBest=max(rows,key=lambda r:r['churn']['priceDividendPath'])['start'],
            cancellationWorst=min(rows,key=lambda r:r['churn']['priceDividendPath'])['start']),
        caveat='Views use different baselines and overlap. Do not add missed upside or counterfactual effects to the pure-bond gap.')


@lru_cache(maxsize=1)
def archived():
    selected()
    body=(REPORT/'cohort.json').read_bytes()
    if hashlib.sha256(body).hexdigest()!=ARCHIVE_SHA256:raise ValueError('321-window report checksum differs')
    return json.loads(body)


def compare(params):
    if params:raise work.InputError('本报告使用固定321个窗口、10万元和基准费用。')
    return archived()


def detail(params):
    if set(params)!={'start'} or params['start'] not in selected():raise work.InputError('请选择已归档321个窗口中的起点。')
    result=analyze(selected()[params['start']],include_daily=True)
    expected=next(r for r in archived()['windows'] if r['start']==params['start'])
    if json.loads(work.encode(result['summary']))!=expected:raise ValueError('Shortfall detail differs from archive')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--start')
    args=p.parse_args();result=detail(dict(start=args.start)) if args.start else calculate()
    with args.output.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(result,ensure_ascii=False,indent=2,default=str)+'\n')
