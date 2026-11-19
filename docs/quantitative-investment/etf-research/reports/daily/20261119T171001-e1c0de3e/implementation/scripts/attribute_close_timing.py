"""Reconcile the historical premium-gap P&L using dated comparison marks."""
import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal as D
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from close_timing_sources import PEAK,TROUGH,archived,audit_inputs
from compare_three_markets import csv_out

METHODS=('documented_nav','iopv','es_hour','es_3m')


def difference(row,method):
    nav=row['expost_nav']
    if method.startswith('es_'):
        before,after=row[method+'_close'],row[method+'_us']
        if before is None or after is None:
            return None
        # Ex-post timing sensitivity: hold FX and tracking fixed within this interval.
        return nav*(before/after-1)
    ref=row[method]
    return ref-nav if ref is not None else None


def coefficients(intervals):
    # Summation by parts. Interior unknown marks cancel only at constant holdings.
    coeff=defaultdict(int)
    for r in intervals:
        coeff[r['date']]+=r['units']
        coeff[r['previous']]-=r['units']
    return {d:q for d,q in sorted(coeff.items()) if q}


def linked(intervals,levels):
    weights=coefficients(intervals)
    if any(levels.get(d) is None for d in weights):
        return None
    return sum((q*levels[d] for d,q in weights.items()),D(0))


def february_table(rows):
    lines = [
        '# 513500 在 2025 年 2 月的境内收盘观察',
        '',
        '境内截止为北京时间 15:00，即 UTC 07:00、纽约 02:00。净值与 IOPV 单位为人民币元/份，ES 单位为指数点。净值日期取当时有档案支持的申赎清单。修改时间取该清单文件的 Last-Modified，精确首发时间未知。IOPV 为交易所日终字段，最后播发秒数未知。',
        '',
        '两个期货栏分别取截至境内收盘已结束的 3 分钟和 1 小时 K 线收盘价。事后净值用于与上期筛选口径对照。',
        '',
        '| 日期 | 清单净值所属日 | 清单净值 | 文件修改（北京） | 场内收盘 | 日终 IOPV | 对 IOPV 溢价 | 对事后净值溢价 | ES 3分钟 | ES 1小时 |',
        '|---|---|---:|---|---:|---:|---:|---:|---:|---:|',
    ]
    for r in rows:
        if str(r['date']).startswith('2025-02'):
            fields = [r['date'], r['documented_nav_date'], r['documented_nav'],
                      r['pcf_last_modified'][11:19], r['close'], r['iopv'],
                      format(r['close_iopv_premium_pct'], '.2f')+'%',
                      format(r['expost_premium_pct'], '.2f')+'%',
                      r['es_3m_close'], r['es_hour_close']]
            lines.append('| ' + ' | '.join(str(v) if v is not None else '未知' for v in fields) + ' |')
    return '\n'.join(lines)+'\n'


def build(out):
    quotes=audit_inputs()
    by_day={r['date']:r for r in quotes}
    levels={m:{d:difference(r,m) for d,r in by_day.items()} for m in METHODS}
    intervals=[]
    for r in archived('drawdown'):
        d,prev=date.fromisoformat(r['date']),date.fromisoformat(r['previous'])
        q=int(r['opening_stock_units'])
        a,b=by_day[prev],by_day[d]
        original=q*((b['close']-b['expost_nav'])-(a['close']-a['expost_nav']))
        if original!=D(r['premium_gap']):
            raise ValueError('Frozen daily gap changed '+str(d))
        item=dict(date=d,previous=prev,units=q,original_gap_pnl=original)
        for m,values in levels.items():
            delta=None if values[d] is None or values[prev] is None else q*(values[d]-values[prev])
            item[m+'_timing']=delta
            item[m+'_remaining']=None if delta is None else original-delta
        intervals.append(item)
    if (intervals[0]['previous'],intervals[-1]['date'])!=(PEAK,TROUGH):
        raise ValueError('Wrong peak/trough')
    summary={}
    for period,batch in [('all',intervals),('february',[r for r in intervals if r['date'].strftime('%Y-%m')=='2025-02'])]:
        original=sum(r['original_gap_pnl'] for r in batch)
        detail={}
        for m,values in levels.items():
            total=linked(batch,values)
            observed=[r for r in batch if r[m+'_timing'] is not None]
            if len(observed)==len(batch) and abs(total-sum(r[m+'_timing'] for r in batch))>D('1e-15'):
                raise ValueError('Holdings bridge disagreement')
            detail[m]=dict(timing_cny=total,remaining_cny=original-total if total is not None else None,
                           directly_valued_intervals=len(observed),unvalued_intervals=len(batch)-len(observed))
        summary[period]=dict(original_gap_pnl=original,intervals=len(batch),methods=detail,
                             nonzero_endpoint_coefficients={str(d):q for d,q in coefficients(batch).items()},
                             causal_timing_amount=None)
    summary['coverage']={k:dict(Counter(r['es_crosscheck'] for r in group)) for k,group in
                         [('selected',quotes),('high',[r for r in quotes if r['high_expost']]),
                          ('february',[r for r in quotes if str(r['date']).startswith('2025-02')])]}
    out.mkdir(parents=True,exist_ok=False)
    (out/'february.md').write_text(february_table(quotes), encoding='utf8')
    csv_out(out/'close_observations.csv',quotes)
    csv_out(out/'intervals.csv',intervals)
    (out/'summary.json').write_text(json.dumps(summary,default=str,indent=2)+'\n',encoding='utf8')
    print('Matched',len(quotes),'closes;',len(intervals),'account intervals; original gap',summary['all']['original_gap_pnl'])


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output',required=True,type=Path)
    build(p.parse_args().output)
