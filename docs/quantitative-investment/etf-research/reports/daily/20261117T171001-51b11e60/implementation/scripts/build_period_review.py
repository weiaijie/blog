"""Build historical calendar-quarter and calendar-year reviews from sealed research."""
import argparse
import csv
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal as D
from itertools import groupby
from pathlib import Path
from statistics import mean, stdev
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from etf_research.admission import sessions_between
from etf_research.long_history import load_long_history
from etf_research.monthly import index_levels
from etf_research.publication import read, sha, create

HISTORY = ROOT/'reports/2026-11-05-long-history'
PNL = ROOT/'reports/2026-11-07-historical-pnl'
PARTS = ('price_510300','price_511010','dividend_510300','dividend_511010','slippage','commission','sell_tax')
MAIN = 'monthly_50_50_base_100000_d1'


def records(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def bounds(day, quarterly):
    first_month = 1 + 3*((day.month-1)//3) if quarterly else 1
    start = date(day.year, first_month, 1)
    next_month = first_month + (3 if quarterly else 12)
    end = date(day.year + (next_month>12), (next_month-1)%12+1, 1) - timedelta(days=1)
    label = f'{day.year}Q{(first_month-1)//3+1}' if quarterly else str(day.year)
    return label,start,end


def build(output):
    data = load_long_history(ROOT/'data/snapshots')
    days = data.sessions
    cfg = read(ROOT/'config/monthly_benchmark.json')
    levels = index_levels(data, days, cfg)
    calendar = read(ROOT/'data/snapshots/2026-11-04-calendar-08/calendar.json')['holiday_ranges']
    pnl = defaultdict(list)
    for row in records(PNL/'daily_pnl.csv'):
        pnl[row['run']].append(row)
    fills = defaultdict(list)
    for row in records(PNL/'fills.csv'):
        fills[row['run'],row['day']].append(row)
    names = {r['run'] for r in read(HISTORY/'results.json')['results']}
    if names!=set(pnl):
        raise ValueError('Historical portfolio coverage differs')
    source_paths = [PNL/'daily_pnl.csv', PNL/'fills.csv', HISTORY/'results.json', ROOT/'config/monthly_benchmark.json']
    periods = []
    for name in sorted(names):
        nav_file = HISTORY/(name+'_daily.csv')
        source_paths.append(nav_file)
        ledger = records(nav_file)
        nav = [D(r['equity']) for r in ledger]
        entries = pnl[name]
        if ([r['date'] for r in ledger] != [str(d) for d in days]
                or [r['date'] for r in entries] != [str(d) for d in days]
                or nav != [D(r['close_equity']) for r in entries]):
            raise ValueError('Missing or misaligned portfolio rows')
        if any(D(entries[0][k]) != 0 for k in PARTS) or fills.get((name,str(days[0]))):
            raise ValueError('Initial close requires explicit inception treatment')
        returns = [D(0)]+[b/a-1 for a,b in zip(nav,nav[1:])]
        for quarterly in (False,True):
            for (label,start,end), group in groupby(range(len(days)),lambda i:bounds(days[i],quarterly)):
                indices = list(group)
                first,last = indices[0],indices[-1]
                anchor = max(0,first-1)
                expected = sessions_between(calendar,start,end)
                complete = first>0 and tuple(days[i] for i in indices)==expected
                selected = range(anchor+1,last+1)
                samples = returns[anchor+1:last+1]
                pieces = {k:sum((D(entries[i][k]) for i in selected),D(0)) for k in PARTS}
                change = nav[last]-nav[anchor]
                if sum(pieces.values())!=change:
                    raise ValueError(f'{name} {label} does not reconcile to net equity')
                trades = [t for i in selected for t in fills.get((name,str(days[i])),())]
                notional = sum((D(t['model_fill'])*int(t['units']) for t in trades),D(0))
                peak = nav[anchor]
                dd = D(0)
                for i in selected:
                    peak = max(peak,nav[i])
                    dd = max(dd,1-nav[i]/peak)
                volatility = stdev(samples)*D(252).sqrt() if complete and len(samples)>1 else None
                sharpe = mean(samples)*252/volatility if volatility else None
                net,benchmark = nav[last]/nav[anchor]-1,levels[last]/levels[anchor]-1
                periods.append(dict(run=name,period=label,complete=complete,anchor=str(days[anchor]),
                    through=str(days[last]),returns=len(samples),opening_nav=nav[anchor],closing_nav=nav[last],
                    net_pnl=change,net_return=net,benchmark_return=benchmark,relative_return=net-benchmark,
                    max_drawdown=dd,annualized_volatility=volatility,sharpe_rf0=sharpe,
                    trades=len(trades),outside_range=sum(t['direction']!='within' for t in trades),
                    gross_notional=notional,gross_turnover=notional/mean(nav[i] for i in indices),**pieces))
    output.mkdir(parents=True,exist_ok=True)
    with (output/'periods.csv').open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(periods[0]),lineterminator='\n')
        writer.writeheader()
        writer.writerows(periods)
    create(output/'inputs.json',dict(source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in source_paths},
           market_manifests=data.provenance['manifests_sha256']))
    render(output, periods)


def render(output, periods):
    lines=['# 历史50/50组合季报和年报','',
           '本金10万元、基准费用、延迟一个交易日。金额按元计，收益和回撤按期初收盘锚计算。'
           '换手为期内双边模型成交额除以同期平均收盘净值。波动率和夏普只列完整期间，'
           '采用日收益样本标准差、252日年化和零无风险收益。基准沿用已固定的股债ETF总收益代理。',
           '', '[全部18个组合及七项金额归因](periods.csv) · [核验方法与来源](PROGRESS.md)', '']
    for yearly, title in [(True,'年度'),(False,'季度')]:
        rows=[r for r in periods if r['run']==MAIN and ('Q' not in r['period'])==yearly]
        lines.extend(['## '+title+'比较','',
            '|期间|范围|净收益|股债基准|相对收益（百分点）|最大回撤|年化波动|夏普|模型成交笔数|双边换手|',
            '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|'])
        for r in rows:
            vol='—' if r['annualized_volatility'] is None else f"{r['annualized_volatility']:.2%}"
            sr='—' if r['sharpe_rf0'] is None else f"{r['sharpe_rf0']:.2f}"
            lines.append(f"|{r['period']}|{'完整' if r['complete'] else '部分'}|{r['net_return']:.2%}|"
                         f"{r['benchmark_return']:.2%}|{100*r['relative_return']:+.2f}|{r['max_drawdown']:.2%}|"
                         f"{vol}|{sr}|{r['trades']}|{r['gross_turnover']:.2%}|")
        lines.extend(['','## '+title+'净值变动（元）','',
            '|期间|股票ETF价格|债券ETF价格|股票分红|债券分红|滑点、佣金及税合计|净值变动|',
            '|---|---:|---:|---:|---:|---:|---:|'])
        for r in rows:
            cost=sum(r[k] for k in ('slippage','commission','sell_tax'))
            lines.append('|'+r['period']+'|'+ '|'.join(f'{v:,.2f}' for v in
                (r['price_510300'],r['price_511010'],r['dividend_510300'],r['dividend_511010'],cost,r['net_pnl']))+'|')
        lines.append('')
    with (output/'PERIODS.md').open('x',encoding='utf-8',newline='\n') as stream:
        stream.write('\n'.join(lines).rstrip()+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True,type=Path)
    build(parser.parse_args().output)
