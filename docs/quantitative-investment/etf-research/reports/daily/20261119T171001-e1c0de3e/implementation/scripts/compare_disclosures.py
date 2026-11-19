"""Compare like-for-like H1 and Q3 disclosures, retaining truncated-list uncertainty."""
import argparse
from decimal import Decimal as D
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from etf_research.bond_issues import identity_map
from etf_research.publication import read,create,sha
from build_period_review import records

H1=ROOT/'reports/2026-11-06-research-audit'
Q3=ROOT/'data/reference/holdings_2026q3.json'


def compare():
    h=read(H1/'holdings.json')
    q=read(Q3)['funds']
    for path,digest in h['sources_sha256'].items():
        if sha(ROOT/path)!=digest:
            raise ValueError('H1 evidence mismatch '+path)
    for fund in q.values():
        if sha(ROOT/fund['pdf_path'])!=fund['pdf_sha256']:
            raise ValueError('Q3 report mismatch')
    rows=[r for r in records(H1/'stocks_2026h1.csv') if r['sleeve']=='index']
    if len(rows)!=300 or len({r['code'] for r in rows})!=300 or q['510300']['coverage']!='index top ten stocks':
        raise ValueError('Stock sleeve scope changed')
    hnav,qnav=D(h['stock']['nav']),D(q['510300']['nav'])
    june={r['code']:r for r in rows}
    sept={r['code']:r for r in q['510300']['listed_positions']}
    top={r['code'] for r in rows if int(r['rank'])<=10}
    if len(top)!=10 or len(sept)!=10:
        raise ValueError('Top ten scope changed')
    stocks=[]
    for code in sorted(top|set(sept)):
        a,b=june.get(code),sept.get(code)
        # H1 discloses the complete index sleeve; Q3 is truncated.
        pre=D(a['fair_value'])/hnav if a else D(0)
        post=D(b['fair_value'])/qnav if b else None
        stocks.append(dict(code=code,name=(b or a)['name'],june_index_rank=int(a['rank']) if a else None,
                     september_top10_rank=b['rank'] if b else None,june_weight=str(pre),
                     september_weight=str(post) if post is not None else None,
                     delta_pp=str(100*(post-pre)) if post is not None else None))
    aliases=identity_map(ROOT/'data/snapshots/2026-11-07-bond-identities-000043')
    def bond_bounds(positions,nav,total,known):
        nav=D(nav)
        amounts={}
        for row in positions:
            issue=aliases[row['code']]
            amounts[issue]=amounts.get(issue,D(0))+D(row['fair_value'])
        tail=D(total)-sum(amounts.values())
        if tail<0 or any(abs(amounts[k]/nav-D(v))>D('1e-24') for k,v in known.items()):
            raise ValueError('Bond grouping mismatch')
        return {k:v/nav for k,v in amounts.items()}, tail/nav
    a,tail_a=bond_bounds(h['bond']['listed_positions'],h['bond']['nav'],h['bond']['bond_total'],h['bond']['known_issue_nav_lower_bounds'])
    fund=q['511010']
    # Q3 residual was recorded as a NAV fraction. Keep that precision throughout.
    b,tail_b=bond_bounds(fund['listed_positions'],fund['nav'],D(fund['security_nav_fraction'])*D(fund['nav']),
                         h['q3_separate_observation']['known_issue_nav_lower_bounds'])
    issues=[]
    for name in sorted(a.keys()|b.keys()):
        low_a,low_b=a.get(name,D(0)),b.get(name,D(0))
        low,high=100*(low_b-low_a-tail_a),100*(low_b+tail_b-low_a)
        issues.append(dict(issue=name,june_disclosed=str(low_a),september_disclosed=str(low_b),
                           change_min_pp=str(low),change_max_pp=str(high),
                           direction='increase' if low>0 else 'decrease' if high<0 else 'unknown'))
    return dict(report_dates=[h['report_date'],fund['report_date']],announcement_dates={
        s:[h['announcement_dates'][s],q[s]['announcement_date']] for s in q},
        sources={p.relative_to(ROOT).as_posix():sha(p) for p in (H1/'holdings.json',H1/'stocks_2026h1.csv',Q3)},
        stock=dict(shared_top10=len(top&set(sept)),june_top10=str(sum(D(june[c]['fair_value']) for c in top)/hnav),
                   september_top10=fund_weight(q['510300']),rows=stocks),
        bond=dict(june_unlisted_fraction=str(tail_a),september_unlisted_fraction=str(tail_b),issues=issues))


def fund_weight(fund):
    return str(sum(D(r['fair_value']) for r in fund['listed_positions'])/D(fund['nav']))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    create(parser.parse_args().output, compare())
