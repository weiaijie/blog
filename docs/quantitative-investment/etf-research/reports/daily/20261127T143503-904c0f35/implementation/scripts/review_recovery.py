"""Drawdown episodes of the 18 sealed historical close-NAV series."""
import argparse
import csv
from datetime import date
from decimal import Decimal as D
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from etf_research.long_history import load_long_history
from etf_research.publication import create, read, sha
from build_period_review import HISTORY, MAIN, records


def episodes(days, nav):
    if (not days or len(days)!=len(nav) or list(days)!=sorted(set(days))
            or any(not x.is_finite() or x<=0 for x in nav)):
        raise ValueError('Invalid dated NAV')
    rows = []
    peak = trough = 0

    def finish(end, recovered):
        rows.append(dict(peak=days[peak], first_below=days[peak+1], trough=days[trough],
                         peak_nav=nav[peak], trough_nav=nav[trough], depth=1-nav[trough]/nav[peak],
                         observed_through=days[end], ending_nav=nav[end],
                         recovery=days[end] if recovered else None,
                         peak_to_trough=trough-peak, peak_to_end=end-peak,
                         trough_to_recovery=end-trough if recovered else None,
                         underwater_closes=end-peak-int(recovered),
                         elapsed_calendar_days=(days[end]-days[peak]).days))
    for i in range(1,len(nav)):
        if nav[i]>=nav[peak]:
            if trough!=peak:
                finish(i,True)
            peak=trough=i
        elif nav[i]<nav[trough]:
            trough=i
    if trough!=peak:
        finish(len(nav)-1,False)
    return rows


def plot(output, days, nav):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import numpy as np
    values=np.asarray(nav,dtype=float)
    high=np.maximum.accumulate(values)
    fig,(ax,dd)=plt.subplots(2,1,sharex=True,figsize=(9,4.4),height_ratios=(2,1),layout='constrained')
    ax.plot(days,values/1000,color='#235889',label='Closing NAV')
    ax.plot(days,high/1000,color='#888888',linestyle='--',label='Previous high')
    ax.set_ylabel('CNY thousands')
    ax.legend(frameon=False,ncols=2)
    dd.fill_between(days,100*(values/high-1),0,color='#bd6152')
    dd.set_ylabel('Drawdown (%)')
    dd.xaxis.set_major_locator(mdates.YearLocator())
    dd.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    fig.savefig(output/'main_drawdowns.png',dpi=150)
    plt.close(fig)


def build(output):
    data=load_long_history(ROOT/'data/snapshots')
    days=data.sessions
    reference=ROOT/'reports/2026-11-07-historical-pnl/summary.json'
    audits={r['run']:r['max_drawdown'] for r in read(reference)['portfolios']}
    source_paths=[reference,HISTORY/'results.json']
    all_rows=[]
    summaries={}
    for run in read(HISTORY/'results.json')['results']:
        name=run['run']
        path=HISTORY/(name+'_daily.csv')
        source_paths.append(path)
        ledger=records(path)
        if [r['date'] for r in ledger]!=[d.isoformat() for d in days]:
            raise ValueError('Incomplete close NAV '+name)
        nav=[D(r['equity']) for r in ledger]
        rows=episodes(days,nav)
        worst=max(rows,key=lambda r:r['depth'],default=None)
        depth=worst['depth'] if worst else D(0)
        if depth!=D(audits[name]['fraction']) or abs(depth+D(str(run['max_close_drawdown'])))>D('1e-12'):
            raise ValueError('Historical maximum drawdown mismatch '+name)
        all_rows.extend(dict(run=name,**r) for r in rows)
        summaries[name]=dict(episodes=len(rows),recovered=sum(r['recovery'] is not None for r in rows),
            underwater_closes=sum(r['underwater_closes'] for r in rows),max_depth=str(depth),
            longest_completed_sessions=max((r['peak_to_end'] for r in rows if r['recovery']),default=None),
            open_peak=str(rows[-1]['peak']) if rows and not rows[-1]['recovery'] else None,
            open_elapsed_sessions=rows[-1]['peak_to_end'] if rows and not rows[-1]['recovery'] else None)
        if name==MAIN:
            main_nav=nav
    output.mkdir(parents=True,exist_ok=False)
    with (output/'episodes.csv').open('x',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(all_rows[0]),lineterminator='\n')
        writer.writeheader()
        writer.writerows(all_rows)
    create(output/'summary.json',dict(accounts=summaries,dates=[str(days[0]),str(days[-1])],sessions=len(days),
           sha256={p.relative_to(ROOT).as_posix():sha(p) for p in source_paths}))
    plot(output,days,main_nav)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True,type=Path)
    build(parser.parse_args().output)
