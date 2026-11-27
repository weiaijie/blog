"""Paired attribution of the nine new two-year maturities; never changes trading rules."""
import argparse
from datetime import date
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))

import data_change_report as parent
import interactive_backtest as work
import model_replay
from build_entry_windows import measure_outcome
from compare_three_markets import CODES
from overlay_attribution import PARTS, cumulative_ledger, interval, daily_gap
from research_profile import RECENT, using

REPORT = Path(__file__).resolve().parents[1]/'reports/2026-11-14-new-window-attribution'
REPORT_SHA = '95ff2c4818a99fd85190a9441d05cc08f316e7a01543b4debe9785870648e8bc'
MODELS = ('allocation', 'multifactor_v1')
SYMBOLS = ('510300', '511010')
NOTES = [
    '固定上轮verified-2026-11-12版本的9个新增两年窗口，各10万元、基准费用、人民币含分红；不是账户最近9天的收益。相邻窗口高度重叠，不能视作9次独立实验。',
    '债券为511010国债ETF，不是可转债。一次建仓初始股债50/50后持有；三因子按已冻结投票在股债50/50与全债间切换，次日执行，不调整阈值。',
    '差额方向均为多因子减一次建仓。价格贡献=前日持仓×(今日开盘-前收)+今日持仓×(收盘-开盘)，分红按登记日持仓在除息日确认；到账只在现金和应收间转移。佣金、滑点为负贡献。',
    '全债状态按实际持仓分段，隔夜用前收持仓、日内用当日成交后持仓，分红按登记日状态分组；其余包含股债与未建仓现金。状态分组只解释已实现账目，不是取消切换后的可实现收益。',
    '加回费用保持原成交数量与路径，仅去除账面佣金及滑点；没有重算无费用下的现金、整手和目标，不能称无费用可执行策略。4%门槛按实际日数/365.25复利计算，未取整前判定。',
]


def selected():
    data = parent.report()
    cohorts = {s['model']:s['periods']['2']['newWindows'] for s in data['scenarios']
               if s['group']=='domestic' and s['model'] in MODELS}
    identity = lambda rows:[(r['start'],r['end']) for r in rows]
    if len(cohorts['allocation'])!=9 or identity(cohorts['allocation'])!=identity(cohorts['multifactor_v1']):
        raise ValueError('Paired nine-window cohort changed')
    return {a['start']:{'allocation':a,'multifactor_v1':b}
            for a,b in zip(cohorts['allocation'],cohorts['multifactor_v1'],strict=True)}


def book(replay):
    daily, orders = [], []
    for f in replay['frames']:
        daily.append(dict(date=f['date'],equity=f['equity'],
                          **{'units_'+s:f['holdings'].get(s,0) for s in CODES}))
        for o in f['orders']:
            orders.append(dict(o,day=f['date'],open=f['bars'][o['symbol']]['open'],
                               modeled_price=o['price'] if o['filled'] else f['bars'][o['symbol']]['open']))
    return daily,orders


def regime_parts(books, bars, events, expected):
    """Exact gross exposure differences grouped by actual factor exposure at each leg."""
    factor,fixed = books['multifactor_v1'][0],books['allocation'][0]
    parts = {state:{s:{k:D(0) for k in ('price','dividend')} for s in SYMBOLS}
             for state in ('bondOnly','other')}
    def tag(row):
        return 'bondOnly' if row['units_510300']==0 and row['units_511010']>0 else 'other'
    for i in range(1,len(factor)):
        for s in SYMBOLS:
            day,prev=factor[i]['date'],factor[i-1]['date'];q='units_'+s
            parts[tag(factor[i-1])][s]['price']+=(factor[i-1][q]-fixed[i-1][q])*(bars[s][day].open-bars[s][prev].close)
            parts[tag(factor[i])][s]['price']+=(factor[i][q]-fixed[i][q])*(bars[s][day].close-bars[s][day].open)
    by_day={f['date']:(f,b) for f,b in zip(factor,fixed,strict=True)}
    for e in events:
        if e.symbol in SYMBOLS and e.record_date in by_day and e.ex_date in by_day:
            f,b=by_day[e.record_date]
            parts[tag(f)][e.symbol]['dividend']+=(f['units_'+e.symbol]-b['units_'+e.symbol])*e.per_share
    for s in SYMBOLS:
        for k in ('price','dividend'):
            if sum(v[s][k] for v in parts.values())!=expected['byEtf'][s][k]:
                raise ValueError('Regime attribution differs from account attribution')
    return dict(parts=parts,bondOnlyClosingSessions=sum(tag(r)=='bondOnly' for r in factor),
                totalSessions=len(factor),grossDifference=sum(sum(v.values()) for p in parts.values() for v in p.values()))


def calculate(start, pair):
    end=pair['allocation']['end'];start_day,end_day=map(date.fromisoformat,(start,end))
    with using(RECENT):
        base,_,bars,_=work.inputs()
        replays={m:model_replay.replay(parent.replay_params(parent.SCENARIOS['domestic-'+m],start,end)) for m in MODELS}
        books={m:book(r) for m,r in replays.items()}
        ledgers={m:cumulative_ledger(*b,bars,base.dividends) for m,b in books.items()}
        period=interval(ledgers,start_day,end_day)
        difference=period['differences']['multifactor_v1-allocation']
        gap=daily_gap(ledgers['multifactor_v1'],ledgers['allocation'],difference,include_accounts=True)
        threshold=parent.CAPITAL*D('1.04')**(D((end_day-start_day).days)/D('365.25'))
        metrics={}
        for m,r in replays.items():
            equity=r['frames'][-1]['equity']
            outcome=measure_outcome(start_day,end_day,2,equity,parent.CAPITAL)
            if any(outcome[k]!=D(str(pair[m][k])) for k in ('pnl','annualized_return')):
                raise ValueError('Previously published maturity differs from replay')
            cost=-sum(period['accounts'][m]['totals'][k] for k in ('commission','slippage'))
            metrics[m]=dict(outcome,reached=outcome['annualized_return']>=D('.04'),
                            targetGap=equity-threshold,cost=cost,fixedFillGrossPnl=outcome['pnl']+cost,
                            fixedFillGrossReached=equity+cost>=threshold,
                            filledOrders=sum(o['filled']>0 for o in books[m][1]),
                            attribution=period['accounts'][m])
        regime=regime_parts(books,bars,base.dividends,difference)
        return dict(start=start,end=end,threshold=threshold,thresholdPnl=threshold-parent.CAPITAL,
                    metrics=metrics,difference=difference,regime=regime,replays=replays,dailyGap=gap,
                    direction='multifactor_v1-allocation')


def build(output):
    output.mkdir(parents=True,exist_ok=False)
    windows=[];digests={}
    for start,pair in selected().items():
        detail=calculate(start,pair);body=work.encode(detail)
        (output/(start+'.json')).write_bytes(body);digests[start]=hashlib.sha256(body).hexdigest()
        windows.append({k:v for k,v in detail.items() if k not in ('replays','dailyGap')})
    summary=dict(schemaVersion=1,dataVersion=RECENT,parentReportSha=parent.REPORT_SHA,capital='100000',fees='base',
                 years=2,annualTarget='0.04',windows=windows,details=digests,notes=NOTES,
                 counts={m:dict(profitable=sum(w['metrics'][m]['pnl']>0 for w in windows),
                     reached=sum(w['metrics'][m]['reached'] for w in windows),
                     fixedFillGrossReached=sum(w['metrics'][m]['fixedFillGrossReached'] for w in windows)) for m in MODELS})
    (output/'comparison.json').write_bytes(work.encode(summary))
    return summary


def report():
    selected()  # Validate the source evidence and immutable parent cohort too.
    body=(REPORT/'comparison.json').read_bytes()
    if hashlib.sha256(body).hexdigest()!=REPORT_SHA:raise ValueError('Nine-window report changed')
    return json.loads(body)


def detail(query):
    data=report();key=query['case']
    if key not in data['details']:raise work.InputError('请选择已核验的9个新增两年窗口之一。')
    body=(REPORT/(key+'.json')).read_bytes()
    if hashlib.sha256(body).hexdigest()!=data['details'][key]:raise ValueError('Nine-window detail changed')
    return json.loads(body)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);p.add_argument('--case')
    args=p.parse_args()
    print(work.encode(build(args.output) if args.output else detail({'case':args.case}) if args.case else report()).decode())
