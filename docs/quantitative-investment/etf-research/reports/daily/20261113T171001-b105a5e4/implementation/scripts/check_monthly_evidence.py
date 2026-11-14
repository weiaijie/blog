"""Independent monthly reconciliation from ETF return legs, cash NAV CSVs and Q3 audit."""
import argparse, calendar, csv, json, sys
from pathlib import Path
from datetime import date
from decimal import Decimal as D
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from etf_research.publication import read, sha, verify_bundle
from etf_research.long_history import load_long_history
from etf_research.admission import load_incremental, sessions_between
from etf_research.risk_extensions import benchmark_returns
from audit_session_evidence import audit


def check(folder):
    verify_bundle(folder)
    state=read(folder/'forward_checkpoint.json')
    report=read(folder/'monthly.json')
    assert state['checkpoint_sha256']==report['checkpoint_sha256']
    policy=read(folder/'monthly_policy.json')
    assert policy==read(ROOT/'config/monthly_benchmark.json')
    assert sha(ROOT/'config/monthly_benchmark.json')==report['policy_sha256']
    history=ROOT/'reports/2026-11-05-long-history'
    snap=read(folder/'risk_extensions_config.json')['forward_price_snapshot']
    ranges=read(ROOT/'data/snapshots/2026-11-04-calendar-08/calendar.json')['holiday_ranges']
    counts={}
    examples={}
    for scope, data in [('history',load_long_history(ROOT/'data/snapshots')),
                        ('forward',load_incremental(ROOT/'data/snapshots',snap)[0])]:
        leg=pd.concat([benchmark_returns(data,s) for s in ('510300','511010')],axis=1)
        checked=0
        for account, rows in report[scope].items():
            if scope=='history':
                nav=pd.read_csv(history/(account+'_daily.csv'),index_col='date',parse_dates=['date']).equity
            else:
                nav=pd.DataFrame(state['portfolios'][account]['daily']).set_index('date').equity.astype(float)
                nav.index=pd.to_datetime(nav.index)
            matched=leg.loc[nav.index[1:]]
            baseline=1.
            gross=pd.Series(index=nav.index,dtype=float)
            gross.iloc[0]=1.
            # Independent within-month buy-and-hold via product of each ETF leg.
            for m, part in matched.groupby(matched.index.to_period('M')):
                path=baseline*(1.+part).cumprod().mean(axis=1)
                gross.loc[path.index]=path
                baseline=path.iloc[-1]
            monthly=list(nav.groupby(nav.index.to_period('M')))
            assert len(monthly)==len(rows)
            for (period, part), row in zip(monthly,rows):
                i=nav.index.get_loc(part.index[0])
                anchor=nav.index[max(i-1,0)]
                end=part.index[-1]
                net=nav.loc[anchor:end]
                ref=gross.loc[anchor:end]
                paired=len(net)-1
                full=bool(i and tuple(x.date() for x in part.index)==sessions_between(ranges,period.start_time.date(),period.end_time.date()))
                assert (row['month'],row['anchor'],row['through'],row['complete'],row['paired_returns'])==(str(period),str(anchor.date()),str(end.date()),full,paired)
                ex=(net.pct_change()-ref.pct_change()).dropna()
                n=net.iloc[-1]/net.iloc[0]-1
                b=ref.iloc[-1]/ref.iloc[0]-1
                for key,value in [('net_return',n if paired else None),('benchmark_return',b if paired else None),
                      ('relative_return',n-b if paired else None),('max_drawdown',max(1-net/net.cummax()) if paired else None),
                      ('tracking_error_annualized',float(ex.std()*np.sqrt(252)) if full and paired>=10 else None),
                      ('cumulative_net',net.iloc[-1]/nav.iloc[0]-1 if end!=nav.index[0] else None),
                      ('cumulative_benchmark',ref.iloc[-1]-1 if end!=nav.index[0] else None)]:
                    assert (row[key] is None if value is None else np.isclose(row[key],value,rtol=0,atol=1e-11)),(scope,account,period,key)
                checked+=1
        counts[scope]=dict(accounts=len(report[scope]),account_months=checked)
        examples[scope]=report[scope]['monthly_50_50_base'+('_100000_d1' if scope=='history' else '')][-1]
    known=read(ROOT/'reports/2026-11-06-research-audit/holdings.json')['q3_separate_observation']['known_issue_nav_lower_bounds']
    ext=read(folder/'risk_extensions.json')
    price=data.bars['511010'][data.sessions[-1]].close
    for p in ext['forward']:
        last=state['portfolios'][p['run']]['daily'][-1]
        value=price*last['units_511010']
        rows=p['lookthrough']['511010']['disclosed_issues']
        assert len(rows)==len(known) and sum(len(r['codes']) for r in rows)==5
        for row in rows:
            fraction=D(known[row['issue']])
            assert fraction==D(row['fund_fraction']) and value*fraction==D(row['portfolio_amount'])
            assert D(row['portfolio_amount'])/D(last['equity'])==D(row['portfolio_fraction'])
    ev=audit()
    assert ev==read(ROOT/'reports/2026-11-07-daily-evidence/sessions.json')
    return dict(account_month_checks=counts,latest_main=examples,issue_accounts=len(ext['forward']),
                dividend_events=len(ev['events']),checkpoint=state['checkpoint_sha256'],scope='Independent monthly return path and seven metrics, Q3 amounts, source audit reproduction.')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--bundle',type=Path)
    a=p.parse_args()
    print(json.dumps(check(a.bundle or ROOT/read(ROOT/'config/active_run.json')['bundle']),ensure_ascii=False,indent=2))
