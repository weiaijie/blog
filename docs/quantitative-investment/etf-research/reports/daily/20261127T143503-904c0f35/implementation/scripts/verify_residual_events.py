"""Verify frozen-account residuals, rankings, sources and unallocated intervals independently."""
import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal as D
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'reports/2026-11-08-close-timing'
SNAP=ROOT/'data/snapshots'
PREFIX='2026-11-08-residual-events-0712'


def read(path):
    with path.open(encoding='utf8',newline='') as f:
        return list(csv.DictReader(f))


def equal(actual,expected):
    if abs(actual-D(expected))>D('0.00000001'):
        raise ValueError(f'{actual} differs from {expected}')


def verify(report):
    source={r['date']:r for r in read(OLD/'close_observations.csv')}
    ledger=read(ROOT/'reports/2026-11-08-nav-fx/drawdown.csv')
    daily=read(report/'daily.csv')
    spans=read(report/'missing_spans.csv')
    summary=json.loads((report/'summary.json').read_bytes())
    assert len(daily)==len(ledger)==72
    for model in ('es_3m','es_hour'):
        values={}
        for day,r in source.items():
            close,us=r[model+'_close'],r[model+'_us']
            values[day]=(D(r['close'])*D(us)-D(r['expost_nav'])*D(close))/D(us) if close and us else None
        known={}
        absent=set()
        for orig,row in zip(ledger,daily,strict=True):
            d,p=orig['date'],orig['previous']
            assert d==row['date'] and p==row['previous'] and orig['opening_stock_units']==row['units']
            assert row['causal_cny']=='' and not row['original_gap']==''
            equal(D(row['original_gap']),orig['premium_gap'])
            if values[d] is None or values[p] is None:
                absent.add(d)
                assert row[model+'_remaining']==row[model+'_loss_rank']==''
            else:
                amount=int(orig['opening_stock_units'])*(values[d]-values[p])
                equal(amount,row[model+'_remaining'])
                known[d]=amount
        ranked=sorted((d for d in known if known[d]<0),key=lambda d:(known[d],d))
        for r in daily:
            wanted=str(ranked.index(r['date'])+1) if r['date'] in ranked else ''
            assert wanted==r[model+'_loss_rank']
        covered=set()
        total=sum(known.values(),D(0))
        for s in (s for s in spans if s['model']==model):
            block=[r for r in ledger if s['first_unallocated']<=r['date']<=s['last_unallocated']]
            assert len(block)==int(s['session_count']) and s['previous']==block[0]['previous']
            coeff=defaultdict(int)
            for r in block:
                assert r['date'] in absent and r['date'] not in covered
                covered.add(r['date'])
                coeff[r['date']]+=int(r['opening_stock_units'])
                coeff[r['previous']]-=int(r['opening_stock_units'])
            combined=sum(q*values[d] for d,q in coeff.items() if q)
            equal(combined,s['combined_cny'])
            total+=combined
        assert covered==absent
        equal(total,summary[model]['net'])
        equal(total,json.loads((OLD/'summary.json').read_bytes())['all']['methods'][model]['remaining_cny'])
        equal(sum(known[d] for d in ranked[:10]),summary[model]['top10_loss'])
    # Check all 73 close-of-clearing share balances independently of the derived file.
    shares={}
    for suffix in ('m','n'):
        for f in (SNAP/(PREFIX+suffix)).glob('shares_*.body'):
            doc=json.loads(f.read_bytes())
            selected,=[r for r in doc['result'] if r['SEC_CODE']=='513500']
            shares[selected['STAT_DATE']]=D(selected['TOT_VOL'])*10000
    assert len(shares)==73
    for row in daily:
        d=row['date']
        equal(shares[d],row['closing_shares'])
        equal(shares[d]-shares[row['previous']],row['net_shares'])
        equal(D(row['net_shares']),row['effective_cap'])
        assert int(row['effective_cap'])==(int(row['listed_cap']) if row['creation']=='是' else 0)
    notices=read(report/'notices.csv')
    assert len({n['url'] for n in notices})==len(notices)==115
    indexed={r['date']:r for r in daily}
    assert [r['date'] for r in daily if r['halt_registry_start']]==['2024-12-17']
    assert [r['date'] for r in daily if r['redemption_conflict']=='True']==['2025-01-20']
    assert indexed['2025-02-12']['distinct_warning_texts']=='1'
    assert indexed['2025-02-21']['press_signed_dates']=='2025-02-20'
    assert indexed['2025-02-25']['press_signed_dates']=='2025-02-24'
    assert indexed['2025-02-28']['sse_warning_count']=='0'
    assert summary['causal_cny'] is None
    print('Verified 72 held intervals, two full residuals, all daily ranks, nine missing spans, 73 share balances and key notice distinctions.')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('report',type=Path)
    verify(parser.parse_args().report)
