"""Fixed-cohort version comparison; new maturities and opening-halt sensitivity stay separate."""
import argparse
from datetime import date
from decimal import Decimal as D
from functools import lru_cache
import hashlib
import json
from pathlib import Path

import interactive_backtest as work
import method_windows
import factor_lab
import model_replay
from build_entry_windows import entry_schedule, measure_outcome, summarize
from overlay_attribution import cumulative_ledger, interval, daily_gap
from recent_market_data import admitted, THROUGH
from research_profile import FROZEN, RECENT, using

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT/'reports/2026-11-13-data-change'
REPORT_SHA = '372774685b1236fbbf413509134faf316b9900d5af68292b722852dc2d89e0f4'
CAPITAL = D('100000')
LABELS = dict(allocation='一次建仓', installments='按月分三批', trend_120='120日趋势',
              multifactor_v1='三因子', multifactor_volume_v1='三因子＋量价',
              multifactor_kdj_v1='三因子＋KDJ', multifactor_adx_v1='三因子＋ADX')
SCENARIOS = {
    'domestic-'+m:dict(id='domestic-'+m,label=label,group='domestic',model=m,weights='1,0,0,1',
        start='2019-03-20',rebalance='signal' if m.startswith('multifactor') else 'monthly' if m=='trend_120' else 'hold')
    for m,label in LABELS.items()}
SCENARIOS.update({
    'market-'+key:dict(id='market-'+key,label=label,group='markets',model='allocation',weights=weights,
                      start='2022-03-30',rebalance='monthly')
    for key,label,weights in [('csi300','沪深300 / 国债','1,0,0,1'),('sp500','标普500 / 国债','0,1,0,1'),
                              ('hangseng','恒生 / 国债','0,0,1,1'),('equal','三市场平分股票仓位 / 国债','1,1,1,3')]})
CONTROL = dict(id='halt-control',label='11月2日起标普 / 国债一次建仓（未满一年）',group='control',
               model='allocation',weights='0,1,0,1',start='2026-11-02',rebalance='hold')


def params(scenario, start, end):
    return dict(start=str(start),end=str(end),capital=str(CAPITAL),fees='base',
                weights=scenario['weights'],rebalance=scenario['rebalance'])


def replay_params(scenario, start, end):
    p=dict(params(scenario,start,end),model=scenario['model'],step='all')
    if scenario['model']=='installments':p['installments']='3'
    return p


def stats(rows):
    result=summarize(rows)
    result['worstPnl']=min(r['pnl'] for r in rows)
    result['losing']=sum(r['pnl']<0 for r in rows)
    result['flat']=sum(r['pnl']==0 for r in rows)
    result['profitRate']=D(result['profitable'])/result['count']
    result['targetRate']=D(result['reached'])/result['count']
    return result


def delta(after, before):
    return {k:after[k]-before[k] for k in ('count','profitable','reached','worstPnl','profitRate','targetRate')}


def compare_cohorts(old, new, relaxed):
    """Each old endpoint survives unchanged; only genuinely new maturities are appended."""
    key=lambda r:(r['start'],r['end'],r['years'])
    old_map={key(r):r for r in old};new_map={key(r):r for r in new}
    relaxed_map={key(r):r for r in relaxed}
    if len(old_map)!=len(old) or len(new_map)!=len(new) or len(relaxed_map)!=len(relaxed):
        raise ValueError('Duplicate maturity')
    if not old_map.keys() <= new_map.keys() or new_map.keys()!=relaxed_map.keys():
        raise ValueError('Unmatched comparison cohorts')
    if any(new_map[k]!=v or relaxed_map[k]!=v for k,v in old_map.items()):
        raise ValueError('Previously matured result changed')
    before,after,without=map(stats,(old,new,relaxed))
    total,sample,halt=delta(after,before),delta(without,before),delta(after,without)
    if any(total[k]!=sample[k]+halt[k] for k in total):
        raise ValueError('Metric change decomposition differs')
    return dict(before=before,after=after,withoutNewHalts=without,delta=total,
                sampleEffect=sample,haltEffect=halt,oldMaturitiesUnchanged=len(old),
                addedMaturities=len(new)-len(old),
                haltChangedWindows=sum(new_map[k]['pnl']!=relaxed_map[k]['pnl'] for k in new_map))


def new_maturities(days):
    return [(s[0],s[i],years) for s,ends in entry_schedule(days) for years,i in ends.items() if s[i]>work.END]


def cross_book(scenario, start, end, relaxed=False):
    days,_,simulate=work.configured_replay(params(scenario,start,end))
    halts=simulate.keywords['halts']
    if relaxed:
        # Diagnostic only: all historical halts and every other constraint remain.
        halts={x for x in halts if not (x[1]=='513500' and work.END<x[0]<=THROUGH)}
    return simulate(days,halts=halts)


def measure(start, end, years, equity):
    return measure_outcome(start,end,years,D(equity),CAPITAL)


def verify_prefix():
    old=work.frozen_inputs();new=admitted()[0]
    if old[0].dividends!=new[0].dividends or old[0].sessions!=new[0].sessions[:len(old[0].sessions)]:
        raise ValueError('Calendar/event prefix changed')
    if old[3]!={x for x in new[3] if x[0]<=work.END}:
        raise ValueError('Historical opening restrictions changed')
    for symbol,prices in old[2].items():
        if any(new[2][symbol][d]!=v for d,v in prices.items()):
            raise ValueError('Historical raw-price prefix changed')
    return old,new


def old_domestic():
    methods=method_windows.archived_entries()
    body=(factor_lab.REPORT/'comparison.json').read_bytes()
    if hashlib.sha256(body).hexdigest()!=factor_lab.ARCHIVE_SHA256:
        raise ValueError('Old technical report changed')
    technical=json.loads(body)['entries']
    by_key={(r['start'],int(r['years'])):r for r in technical}
    if by_key.keys()!=methods.keys():raise ValueError('Old model cohorts differ')
    result={m:[] for m in LABELS}
    for key,row in methods.items():
        tech=by_key[key]
        if tech['end']!=row['end'] or D(tech['multifactor_v1'])!=D(row['multifactor_v1']):
            raise ValueError('Independent three-factor archives disagree')
        for model in LABELS:
            source=row if model in row else tech
            result[model].append(measure(date.fromisoformat(row['start']),date.fromisoformat(row['end']),
                                         int(row['years']),source[model]))
    return result


def build():
    old,new=verify_prefix();domestic=old_domestic();rows=[];cases={};checks=[]
    def add_case(scenario,start,end,years,kind,profile=RECENT):
        key=f"{scenario['id']}-{years}-{kind}-{start}"
        cases[key]=dict(id=key,scenario=scenario['id'],start=str(start),end=str(end),years=years,kind=kind,dataVersion=profile)
        return key
    for scenario in SCENARIOS.values():
        first=date.fromisoformat(scenario['start'])
        added=[];counter=[];blocked=0
        if scenario['group']=='domestic':
            baseline=domestic[scenario['model']]
            days=tuple(d for d in new[0].sessions if d>=first)
        else:
            old_days=tuple(d for d in old[1] if d>=first)
            baseline=[]
            with using(FROZEN):
                for sessions,ends in entry_schedule(old_days):
                    ledger,_=cross_book(scenario,sessions[0],sessions[-1])
                    for years,i in ends.items():baseline.append(measure(sessions[0],sessions[i],years,ledger[i]['equity']))
            days=tuple(d for d in new[1] if d>=first)
        expected={(s[0],s[i],years) for s,ends in entry_schedule(days) for years,i in ends.items() if s[i]<=work.END}
        if expected!={(r['start'],r['end'],r['years']) for r in baseline}:
            raise ValueError('Existing mature endpoints are not identical')
        details=[]
        with using(RECENT):
            for start,end,years in new_maturities(days):
                if scenario['group']=='domestic':
                    book=model_replay.replay(replay_params(scenario,start,end))
                    equity=book['frames'][-1]['equity'];relaxed=equity;halt_orders=[]
                else:
                    ledger,orders=cross_book(scenario,start,end)
                    relaxed_book,_=cross_book(scenario,start,end,True)
                    equity=ledger[-1]['equity'];relaxed=relaxed_book[-1]['equity']
                    halt_orders=[o for o in orders if o['reason']=='opening_halt' and o['day']>work.END]
                a=measure(start,end,years,equity);b=measure(start,end,years,relaxed)
                added.append(a);counter.append(b);blocked+=len(halt_orders)
                case=add_case(scenario,start,end,years,'new')
                details.append(dict(a,case=case,haltEffectPnl=a['pnl']-b['pnl'],blockedOrders=len(halt_orders)))
        periods={}
        for years in (1,2):
            pick=lambda entries:[r for r in entries if r['years']==years]
            result=compare_cohorts(pick(baseline),pick(baseline+added),pick(baseline+counter))
            result['newWindows']=[r for r in details if r['years']==years]
            for label,profile in [('before',FROZEN),('after',RECENT)]:
                worst=result[label]
                result[label]['worstCase']=add_case(scenario,worst['worstStart'],worst['worstEnd'],years,'worst-'+label,profile)
            if scenario['group']=='domestic':
                name='default-methods.json' if scenario['model'] in method_windows.MODELS else 'default-technical.json'
                from recent_backtest import REPORT as RECENT_REPORT, DEFAULT_ARCHIVES
                body=(RECENT_REPORT/name).read_bytes()
                expected_sha=next(h for n,h in DEFAULT_ARCHIVES.values() if n==name)
                if hashlib.sha256(body).hexdigest()!=expected_sha:raise ValueError('Recent full-computation report changed')
                published=json.loads(body)['periods'][str(years)][scenario['model']]
                for field in ('count','profitable','reached','worstPnl','worstStart','worstEnd'):
                    left,right=result['after'][field],published[field]
                    if (D(str(left))!=D(str(right)) if field=='worstPnl' else left!=right):
                        raise ValueError('New-cohort bridge differs from independent full recomputation')
                checks.append(dict(scenario=scenario['id'],years=years,fullRecomputationMatched=True))
            periods[years]=result
        rows.append(dict(scenario,periods=periods,newHaltBlockedOrders=blocked))
    control_key=add_case(CONTROL,CONTROL['start'],str(THROUGH),0,'diagnostic')
    return dict(schemaVersion=1,oldThrough=str(work.END),newThrough=str(THROUGH),newSessions=admitted()[1]['addedSessions'],
                capital=str(CAPITAL),fees='base',annualTarget='0.04',scenarios=rows,cases=cases,controlCase=control_key,
                openingHalts=admitted()[1]['openingHalts'],fullRecomputationChecks=checks,
                notes=['七个境内模型采用2019-03-20共同起点，沪深300与国债；跨市场四组自2022-03-30起、股债50/50、月度再平衡，两块不直接比总次数。',
                       '先逐项验证旧数据、分红、日历和停牌前缀不变；境内旧窗口使用已封存逐窗结果，新到期窗口重算并与上轮全量重算核对。跨市场旧窗口本轮重新计算。',
                       '样本效应=加入新到期窗口但忽略新增停牌限制后减旧统计；停牌规则效应=实际新统计减该条件对照；两者逐项加总等于总变化。',
                       '取消停牌仅为事后规则敏感性诊断，仍使用日线open（可能是复牌后的首笔价）。无停牌时真实可成交价未知，不能将条件差额解释为真实可赚或可挽回损失。',
                       '最差盈亏是各自窗口集合中的最小值；其差额不等于同一个账户追加9天的盈亏。相邻窗口重叠，赚钱次数不是独立成功概率。'])


@lru_cache(maxsize=1)
def report():
    verify_prefix()
    body=(REPORT/'comparison.json').read_bytes()
    if hashlib.sha256(body).hexdigest()!=REPORT_SHA:raise ValueError('Version comparison report changed')
    return json.loads(body)


def detail(query):
    data=report()
    if query['case'] not in data['cases']:raise work.InputError('未知的版本比较区间。')
    case=data['cases'][query['case']]
    scenario=CONTROL if case['scenario']==CONTROL['id'] else SCENARIOS[case['scenario']]
    start,end=date.fromisoformat(case['start']),date.fromisoformat(case['end'])
    with using(case['dataVersion']):
        actual=model_replay.replay(replay_params(scenario,start,end))
        result=dict(case=case,scenario=scenario,actual=actual,counterfactual=None)
        if scenario['group']!='domestic':
            base,_,bars,_=work.inputs()
            ledger,orders=cross_book(scenario,start,end)
            relaxed,trades=cross_book(scenario,start,end,True)
            if ledger[-1]['equity']!=actual['frames'][-1]['equity']:raise ValueError('Replay and accounting differ')
            a=cumulative_ledger(ledger,orders,bars,base.dividends)
            b=cumulative_ledger(relaxed,trades,bars,base.dividends)
            contribution=interval({'actual':a,'relaxed':b},start,end)['differences']['actual-relaxed']
            peak=CAPITAL;curve=[]
            for r in relaxed:
                peak=max(peak,r['equity']);curve.append(dict(date=r['date'],equity=r['equity'],drawdown=r['equity']/peak-1))
            result['counterfactual']=dict(curve=curve,orders=trades,contribution=contribution,
                dailyGap=daily_gap(a,b,contribution),effect=ledger[-1]['equity']-relaxed[-1]['equity'],
                assumption=data['notes'][3])
        return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);p.add_argument('--case')
    args=p.parse_args()
    if args.output:
        args.output.mkdir(parents=True,exist_ok=False)
        (args.output/'comparison.json').write_bytes(work.encode(build()))
    else:
        print(work.encode(detail({'case':args.case}) if args.case else report()).decode())
