"""Predeclared holding-period audit, separate from frozen historical outputs."""
from pathlib import Path
from dataclasses import replace
from decimal import Decimal
from bisect import bisect_left
import argparse, csv, hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import pandas as pd
from etf_research.holding_horizons import windows, summarize, disjoint
from etf_research.long_history import load_long_history
from etf_research.baselines import run, SCENARIOS


def write_csv(path, rows):
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def build(output):
    output.mkdir(parents=True,exist_ok=True)
    config_path=ROOT/'config/holding_horizon_audit.json'
    config=json.loads(config_path.read_text(encoding='utf-8'))
    if config['horizons_calendar_years'] != [1,2] or config['annualization_days']!=365.25 or config['target_thresholds']!=[.04,.05] or config['disjoint_phases_months']!=list(range(12)):
        raise ValueError('Method change requires a new version')
    results=ROOT/config['history_results']
    source_paths=[config_path,results,ROOT/'PROTOCOL_V1.md']
    all_rows=[];phases=[];summaries=[]
    saved=json.loads(results.read_text(encoding='utf-8'))
    if len(saved['results'])!=18:raise ValueError('Expected all 18 frozen baseline accounts')
    for account in saved['results']:
        path=results.parent/(account['run']+'_daily.csv');source_paths.append(path)
        df=pd.read_csv(path)
        for years in (1,2):
            rows=windows(df.date,df.equity,years)
            prefix=dict(run=account['run'],years=years)
            all_rows.extend(dict(**prefix,**r) for r in rows)
            summaries.append(dict(**prefix,excluded_incomplete_starts=len(df)-len(rows),**summarize(rows)))
            for phase in range(12):
                chosen=disjoint(rows,df.date.iloc[0],phase)
                phases.extend(dict(**prefix,phase_months=phase,**r) for r in chosen)
    write_csv(output/'continuous_windows.csv',all_rows)
    write_csv(output/'disjoint_windows.csv',phases)
    # New money is evaluated separately: only the predeclared primary strategy.
    data=load_long_history(ROOT/'data/snapshots')
    starts=[]
    for i,day in enumerate(data.sessions):
        if i and (day.year,day.month)!=(data.sessions[i-1].year,data.sessions[i-1].month):starts.append(day)
    fresh=[];fresh_paths=[];fresh_decisions=[]
    for start in starts:
        endpoints={}
        for years in (1,2):
            anniversary=(pd.Timestamp(start)+pd.DateOffset(years=years)).date()
            j=bisect_left(data.sessions,anniversary)
            if j<len(data.sessions):endpoints[years]=j
        if not endpoints:continue
        sample=replace(data,sessions=data.sessions[:max(endpoints.values())+1])
        for scenario in SCENARIOS:
            result=run(sample,'monthly_50_50',scenario,Decimal('100000'),execution_delay=1,account_start=start)
            name=f'monthly_50_50_{scenario}_{start}'
            fresh_paths.extend(dict(account=name,**r) for r in result['daily'])
            fresh_decisions.extend(dict(account=name,**r) for r in result['decisions'])
            dates=[r['date'] for r in result['daily']];nav=[r['equity'] for r in result['daily']]
            for years in endpoints:
                row=windows(dates,nav,years)[0]
                fresh.append(dict(run=name,scenario=scenario,years=years,**row))
    write_csv(output/'fresh_accounts.csv',fresh)
    write_csv(output/'fresh_daily.csv',fresh_paths)
    write_csv(output/'fresh_decisions.csv',fresh_decisions)
    source_paths.extend(ROOT/'src/etf_research'/name for name in ('baselines.py','accounting.py','data.py','long_history.py','holding_horizons.py'))
    source_paths.append(Path(__file__))
    report=dict(schema_version=1,mode='retrospective_research_only',history_as_of=str(data.sessions[-1]),
        changes_forward_account=False,selection_or_optimization=False,historical_frequency_is_future_probability=False,
        terminal_liquidation_included=False,settings=config,
        sources_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
        historical_data_provenance=data.provenance,continuous=summaries,
        disjoint=[dict(run=s['run'],years=s['years'],phase_months=phase,**summarize([r for r in phases if r['run']==s['run'] and r['years']==s['years'] and r['phase_months']==phase])) for s in summaries for phase in range(12)],
        fresh=[dict(scenario=scenario,years=years,**summarize([r for r in fresh if r['scenario']==scenario and r['years']==years])) for scenario in SCENARIOS for years in (1,2)],
        fresh_eligible_months=len(set(r['start'] for r in fresh)),fresh_excluded_incomplete_months=len(starts)-len(set(r['start'] for r in fresh)))
    (output/'horizons.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(continuous_windows=len(all_rows),disjoint_windows=len(phases),fresh_windows=len(fresh),fresh_accounts=len(set(r['run'] for r in fresh)))))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'reports/2026-11-06-research-audit');args=parser.parse_args();build(args.output)
