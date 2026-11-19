"""Cross-check calendar aggregation against frozen monthly returns, NAV and journals."""
import argparse
import csv
import json
import math
from hashlib import sha256
from collections import defaultdict
from decimal import Decimal as D
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT/'reports/2026-11-05-long-history'
ATTRIBUTION = ROOT/'reports/2026-11-07-historical-pnl'
MONTHLY = ROOT/'reports/daily/20261107T135033-e268ce3b/monthly.json'


def check(value, expected, field):
    if value != expected:
        raise ValueError(f'{field}: {value} != {expected}')


def close(value, expected, field):
    if value == '' and expected is None:
        return
    if value == '' or expected is None or not math.isclose(float(value),expected,rel_tol=1e-11,abs_tol=1e-11):
        raise ValueError(f'{field}: {value} differs from {expected}')


def verify(folder):
    from check_historical_pnl import verify as verify_daily
    upstream=verify_daily(ATTRIBUTION)
    inputs=json.loads((folder/'inputs.json').read_bytes())
    for name,digest in inputs['source_sha256'].items():
        check(sha256((ROOT/name).read_bytes()).hexdigest(),digest,name)
    for name,digest in inputs['market_manifests'].items():
        check(sha256((ROOT/'data/snapshots'/name/'manifest.json').read_bytes()).hexdigest(),digest,name)
    monthly=json.loads(MONTHLY.read_bytes())['history']
    journal=json.loads((HISTORY/'audit.json').read_bytes())
    components=('price_510300','price_511010','dividend_510300','dividend_511010','slippage','commission','sell_tax')
    contributions=pd.read_csv(ATTRIBUTION/'daily_pnl.csv',dtype=str)
    for k in components:
        contributions[k]=contributions[k].map(D)
    grouped={name: frame.set_index('date') for name,frame in contributions.groupby('run')}
    with (folder/'periods.csv').open(encoding='utf-8',newline='') as stream:
        raw=list(csv.DictReader(stream))
    by_key={(r['run'],r['period']):r for r in raw}
    check(len(by_key),len(raw),'duplicate period')
    counts=defaultdict(int)
    for name, months in monthly.items():
        nav=pd.read_csv(HISTORY/(name+'_daily.csv'),index_col='date',dtype=str).equity.map(D)
        ledger=[t for t in journal[name]['journal'] if t['kind']=='trade']
        for freq in ('Y','Q'):
            buckets=defaultdict(list)
            for month in months:
                p=pd.Period(month['month'],freq='M').asfreq(freq)
                buckets[str(p)].append(month)
            for label, group in buckets.items():
                row=by_key.pop((name,label))
                anchor,end=group[0]['anchor'],group[-1]['through']
                check((row['anchor'],row['through']),(anchor,end),label)
                complete=all(m['complete'] for m in group) and len(group)==(12 if freq=='Y' else 3)
                check(row['complete'],str(complete),label)
                paired=sum(m['paired_returns'] for m in group)
                check(int(row['returns']),paired,'return count')
                net=math.prod(1+m['net_return'] for m in group)-1
                bench=math.prod(1+m['benchmark_return'] for m in group)-1
                for key,v in [('net_return',net),('benchmark_return',bench),('relative_return',net-bench)]:
                    close(row[key],v,key)
                values=nav.loc[anchor:end]
                check((D(row['opening_nav']),D(row['closing_nav'])),(values.iloc[0],values.iloc[-1]),'anchors')
                check(D(row['net_pnl']),values.iloc[-1]-values.iloc[0],'equity change')
                vector=values.to_numpy(dtype=float)
                close(row['max_drawdown'],float(max(1-vector/np.maximum.accumulate(vector))),'drawdown')
                ret=np.diff(vector)/vector[:-1]
                vol=float(np.std(ret,ddof=1)*math.sqrt(252)) if complete else None
                close(row['annualized_volatility'],vol,'volatility')
                close(row['sharpe_rf0'],float(ret.mean()*252/vol) if vol else None,'sharpe')
                totals=grouped[name].loc[anchor:end].iloc[1:][list(components)].sum()
                for key in components:
                    check(D(row[key]),totals[key],key)
                trades=[t for t in ledger if anchor<t['day']<=end]
                check(int(row['trades']),len(trades),'fills')
                notional=sum((D(t['notional']) for t in trades),D(0))
                check(D(row['gross_notional']),notional,'notional')
                dates=values.index if anchor==nav.index[0] and group[0]==months[0] else values.index[1:]
                close(row['gross_turnover'],float(notional)/nav.loc[dates].astype(float).mean(),'turnover')
                counts['annual' if freq=='Y' else 'quarterly']+=1
                counts['complete' if complete else 'partial']+=1
    check(len(by_key),0,'unmatched periods')
    # Verify the count outside observations against actual SSE high/low at each fill date.
    px={}
    for s in ('510300','511010'):
        rawbars=json.loads((ROOT/'data/snapshots/2026-11-05-costs-11'/('official_full_'+s+'.body')).read_bytes(),parse_float=D)
        px[s]={str(x[0]):(D(x[3]),D(x[2])) for x in rawbars['kline']}
    outside=defaultdict(int)
    for name in monthly:
        for t in journal[name]['journal']:
            if t['kind']!='trade':
                continue
            lo,hi=px[t['symbol']][t['day'].replace('-','')]
            if not lo<=D(t['fill_price'])<=hi:
                for f in ('Y','Q'):
                    outside[name,str(pd.Period(t['day'],freq=f))]+=1
    for r in raw:
        check(int(r['outside_range']),outside[r['run'],r['period']],'outside_range')
    return dict(accounts=len(monthly),rows=len(raw),**counts,monthly_basis=MONTHLY.relative_to(ROOT).as_posix(),
                upstream=upstream,monetary_check='Decimal equality',ratio_tolerance=1e-11)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--folder',type=Path,default=ROOT/'reports/2026-11-07-period-review')
    print(json.dumps(verify(p.parse_args().folder),ensure_ascii=False,indent=2))
