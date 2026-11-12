"""Verify episodes from contiguous underwater runs and holdings from archived disclosures."""
import argparse
from decimal import Decimal as D
from itertools import groupby
from pathlib import Path
import tempfile
import numpy as np
import pandas as pd

from review_recovery import HISTORY, ROOT, read, records, sha
from build_holdings_audit import build as extract_h1
from extract_holdings import extract as extract_q3

REPORT=ROOT/'reports/2026-11-07-recovery'


def check(actual,expected,label):
    if actual!=expected:
        raise ValueError(f'{label}: {actual!r} != {expected!r}')


def close(actual,expected,label):
    if not np.isclose(float(actual),float(expected),rtol=0,atol=1e-12):
        raise ValueError(label)


def verify(folder):
    summary=read(folder/'summary.json')
    for name,digest in summary['sha256'].items():
        check(sha(ROOT/name),digest,name)
    rows=records(folder/'episodes.csv')
    check(set(summary['accounts']),{r['run'] for r in read(HISTORY/'results.json')['results']},'accounts')
    checked=complete=observations=0
    for name,account in summary['accounts'].items():
        nav=pd.read_csv(HISTORY/(name+'_daily.csv'),index_col='date',parse_dates=['date']).equity
        values=nav.to_numpy()
        days=nav.index
        mask=values < np.maximum.accumulate(values)
        actual=[r for r in rows if r['run']==name]
        groups=[list(indices) for low,indices in groupby(range(len(nav)),key=mask.__getitem__) if low]
        check(len(actual),len(groups),'number of episodes')
        finished=[]
        for r,group in zip(actual,groups):
            first,last=group[0],group[-1]
            p=first-1
            t=first+int(values[first:last+1].argmin())
            recovered=last<len(nav)-1
            e=last+int(recovered)
            if recovered:
                finished.append(e-p)
                complete+=1
            for field,i in [('peak',p),('first_below',first),('trough',t),('observed_through',e)]:
                check(r[field],str(days[i].date()),field)
            check(r['recovery'],str(days[e].date()) if recovered else '', 'recovery')
            check(r['trough_to_recovery'],str(e-t) if recovered else '', 'trough to recovery')
            for field,expected in [('underwater_closes',len(group)),('peak_to_trough',t-p),
                 ('peak_to_end',e-p),('elapsed_calendar_days',(days[e]-days[p]).days)]:
                check(int(r[field]),expected,field)
            for field,i in [('peak_nav',p),('trough_nav',t),('ending_nav',e)]:
                check(D(r[field]),D(str(values[i])),field)
            close(r['depth'],1-values[t]/values[p],'depth')
            checked+=1
        observations+=len(nav)
        check(account['episodes'],len(groups),'episodes')
        check(account['underwater_closes'],int(mask.sum()),'underwater days')
        check(account['recovered'],len(finished),'recovered')
        close(account['max_depth'],max(1-values/np.maximum.accumulate(values)),'max depth')
        check(account['longest_completed_sessions'],max(finished,default=None),'longest')
        check(account['open_peak'],actual[-1]['peak'] if mask[-1] else None,'open peak')
        check(account['open_elapsed_sessions'],len(groups[-1]) if mask[-1] else None,'open duration')
    check(len(rows),checked,'total coverage')

    comp=read(folder/'disclosures.json')
    for name,digest in comp['sources'].items():
        check(sha(ROOT/name),digest,name)
    q=extract_q3()['funds']
    with tempfile.TemporaryDirectory() as tmp:
        extract_h1(Path(tmp))
        h=read(Path(tmp)/'holdings.json')
        stocks=records(Path(tmp)/'stocks_2026h1.csv')
    hstocks={r['code']:r for r in stocks if r['sleeve']=='index'}
    qstocks={r['code']:r for r in q['510300']['listed_positions']}
    codes={c for c,r in hstocks.items() if int(r['rank'])<=10}
    stock=comp['stock']
    check(stock['shared_top10'],len(codes&qstocks.keys()),'shared stocks')
    check({r['code'] for r in stock['rows']},codes|qstocks.keys(),'disclosed codes')
    check(len(stock['rows']),len(codes|qstocks.keys()),'unique stocks')
    for r in stock['rows']:
        c=r['code']
        pre=D(hstocks[c]['fair_value'])/D(h['stock']['nav']) if c in hstocks else D(0)
        post=D(qstocks[c]['nav_fraction']) if c in qstocks else None
        check(D(r['june_weight']),pre,'H1 weight')
        check(r['june_index_rank'],int(hstocks[c]['rank']) if c in hstocks else None,'H1 rank')
        check(r['september_top10_rank'],qstocks[c]['rank'] if c in qstocks else None,'Q3 rank')
        check(r['september_weight'],str(post) if post is not None else None,'Q3 weight')
        check(r['delta_pp'],str((post-pre)*100) if post is not None else None,'stock weight change')
    close(stock['june_top10'],sum(D(hstocks[c]['fair_value']) for c in codes)/D(h['stock']['nav']),'June top ten')
    close(stock['september_top10'],q['510300']['listed_nav_fraction'],'September top ten')
    a=h['bond']['known_issue_nav_lower_bounds']
    b=h['q3_separate_observation']['known_issue_nav_lower_bounds']
    issues=comp['bond']['issues']
    check({r['issue'] for r in issues},a.keys()|b.keys(),'issue coverage')
    check(len(issues),len(a.keys()|b.keys()),'unique issues')
    tails=[D(h['bond']['undisclosed_bond_value'])/D(h['bond']['nav']),D(q['511010']['unlisted_security_nav_fraction'])]
    for field,expected in zip(('june_unlisted_fraction','september_unlisted_fraction'),tails):
        close(comp['bond'][field],expected,field)
    for r in issues:
        left,right=D(a.get(r['issue'],0)),D(b.get(r['issue'],0))
        check(D(r['june_disclosed']),left,'June issue')
        check(D(r['september_disclosed']),right,'September issue')
        scenarios=[(right+y-left-x)*100 for x in (0,tails[0]) for y in (0,tails[1])]
        close(r['change_min_pp'],min(scenarios),'minimum')
        close(r['change_max_pp'],max(scenarios),'maximum')
        check(r['direction'],'increase' if min(scenarios)>0 else 'decrease' if max(scenarios)<0 else 'unknown','direction')
    return dict(accounts=len(summary['accounts']),observations=observations,episodes=checked,
                recovered=complete,ongoing=checked-complete,stock_codes=len(stock['rows']),issues=len(issues))


if __name__=='__main__':
    import json
    parser=argparse.ArgumentParser()
    parser.add_argument('--folder',type=Path,default=REPORT)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=verify(args.folder)
    if args.output:
        with args.output.open('x',encoding='utf-8',newline='\n') as f:
            f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
