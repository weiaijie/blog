"""Independent stdlib/Decimal window oracle; no pandas or analysis-module import."""
from pathlib import Path
from datetime import date
from decimal import Decimal as D
from calendar import monthrange
from bisect import bisect_left
from collections import defaultdict
import argparse,csv,json,math,hashlib
ROOT=Path(__file__).resolve().parents[1]


def read_csv(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


def anniversary(day, years):
    return date(day.year+years,day.month,min(day.day,monthrange(day.year+years,day.month)[1]))


def check(output):
    report=json.loads((output/'horizons.json').read_text(encoding='utf-8'))
    for name,expected in report['sources_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:raise AssertionError('Source changed: '+name)
    accounts={}
    for file in (ROOT/'reports/2026-11-05-long-history').glob('*_daily.csv'):
        accounts[file.name[:-10]]=read_csv(file)
    fresh=defaultdict(list)
    for row in read_csv(output/'fresh_daily.csv'):fresh[row['account']].append(row)
    checks=0
    for filename,paths in [('continuous_windows.csv',accounts),('fresh_accounts.csv',fresh)]:
        grouped=defaultdict(list)
        for row in read_csv(output/filename):grouped[(row['run'],int(row['years']))].append(row)
        for (name,years),rows in grouped.items():
            source=paths[name];dates=[date.fromisoformat(r['date']) for r in source];values=[D(r['equity']) for r in source]
            lookup={d:i for i,d in enumerate(dates)}
            expected=[i for i,d in enumerate(dates) if anniversary(d,years)<=dates[-1]] if filename.startswith('continuous') else [0]
            if [lookup[date.fromisoformat(r['start'])] for r in rows]!=expected:raise AssertionError('Missing/reordered window')
            for row in rows:
                i=lookup[date.fromisoformat(row['start'])];target=anniversary(dates[i],years);j=bisect_left(dates,target)
                elapsed=(dates[j]-dates[i]).days;ratio=values[j]/values[i]
                peak=values[i];dd=D(0)
                for value in values[i:j+1]:peak=max(peak,value);dd=max(dd,1-value/peak)
                if row['end']!=str(dates[j]) or row['anniversary']!=str(target) or int(row['calendar_days'])!=elapsed or int(row['observations'])!=j-i+1:raise AssertionError('Calendar endpoint mismatch')
                for field,expected_value in [('start_equity',values[i]),('end_equity',values[j]),('total_return',ratio-1),('annualized_return',ratio**(D('365.25')/elapsed)-1),('max_drawdown',dd)]:
                    if not math.isclose(float(row[field]),float(expected_value),rel_tol=0,abs_tol=1e-9):raise AssertionError(name+' '+row['start']+' '+field)
                    checks+=1
    # The first day of each fresh account is uninvested; decisions cannot use future signals.
    for name,rows in fresh.items():
        first=rows[0]
        if D(first['equity'])!=100000 or D(first['cash'])!=100000 or any(int(first['units_'+s]) for s in ('510300','511010')):raise AssertionError('Fresh entry contains inherited holdings')
    for row in read_csv(output/'fresh_decisions.csv'):
        if row['day']<=row['signal_date'] or row['day']<=fresh[row['account']][0]['date']:raise AssertionError('Lookahead signal')
    phases=defaultdict(list)
    for row in read_csv(output/'disjoint_windows.csv'):phases[(row['run'],row['years'],row['phase_months'])].append(row)
    for rows in phases.values():
        if any(a['end']>b['start'] for a,b in zip(rows,rows[1:])):raise AssertionError('Overlapping disjoint phase')
    continuous=read_csv(output/'continuous_windows.csv');fresh_rows=read_csv(output/'fresh_accounts.csv')
    if len(report['continuous'])!=36 or len(report['fresh'])!=6 or len(report['disjoint'])!=432:raise AssertionError('Missing scenario summaries')
    summary_checks=0
    for kind,source in [('continuous',continuous),('fresh',fresh_rows),('disjoint',read_csv(output/'disjoint_windows.csv'))]:
        for summary in report[kind]:
            keys=['years','scenario'] if kind=='fresh' else (['run','years','phase_months'] if kind=='disjoint' else ['run','years'])
            rows=[r for r in source if all(str(r[k])==str(summary[k]) for k in keys)]
            values=sorted(float(r['annualized_return']) for r in rows)
            expected=dict(count=len(rows),at_least_4pct=sum(v>=.04 for v in values),at_least_5pct=sum(v>=.05 for v in values),losses=sum(v<0 for v in values))
            if any(summary[k]!=v for k,v in expected.items()):raise AssertionError('Summary count mismatch')
            if rows:
                for key,q in [('min',0),('p05',.05),('median',.5),('p95',.95),('max',1)]:
                    index=(len(values)-1)*q;low=int(index);high=min(low+1,len(values)-1)
                    value=values[low]+(values[high]-values[low])*(index-low)
                    if abs(summary['annualized_quantiles'][key]-value)>1e-12:raise AssertionError('Quantile mismatch')
                if abs(summary['worst_window_drawdown']-max(float(r['max_drawdown']) for r in rows))>1e-12:raise AssertionError('Summary drawdown mismatch')
            summary_checks+=1
    for (name,years,phase),rows in phases.items():
        base=date.fromisoformat(accounts[name][0]['date']);month_index=base.year*12+base.month-1+int(phase)
        year,month=divmod(month_index,12);month+=1
        threshold=str(date(year,month,min(base.day,monthrange(year,month)[1])))
        expected=[]
        for row in continuous:
            if row['run']==name and row['years']==years and row['start']>=threshold:
                expected.append(row);threshold=row['end']
        if [r['start'] for r in rows]!=[r['start'] for r in expected]:raise AssertionError('Disjoint phase selection mismatch')
    result=dict(passed=True,independent_engine='stdlib calendar/bisect/Decimal; no pandas/numpy',numeric_fields_checked=checks,summary_groups_checked=summary_checks,fresh_accounts_checked=len(fresh),disjoint_groups_checked=len(phases),tolerance_absolute=1e-9)
    (output/'horizon_crosscheck.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'reports/2026-11-06-research-audit');a=p.parse_args();check(a.output)
