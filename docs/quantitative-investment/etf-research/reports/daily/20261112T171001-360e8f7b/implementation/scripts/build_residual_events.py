"""Rank observable daily residual P&L and reconcile the unallocatable holiday spans."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from decimal import Decimal as D
from itertools import groupby
from pathlib import Path

from residual_event_sources import (ROOT, catalog, halt_registry, issuer_entries, offerings,
                                    outstanding, press_by_day)

BASE = ROOT/'reports/2026-11-08-close-timing'
MODELS = ('es_3m','es_hour')


def archived(name):
    p = BASE/name
    hashes = json.loads((BASE/'manifest.json').read_bytes())
    if hashlib.sha256(p.read_bytes()).hexdigest()!=hashes[p.relative_to(ROOT).as_posix()]:
        raise ValueError('Frozen input changed: '+name)
    with p.open(encoding='utf8',newline='') as stream:
        return list(csv.DictReader(stream))


def write_rows(path,rows):
    with path.open('x',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def level(row,model):
    a,b=row[model+'_close'],row[model+'_us']
    if a and b:
        return D(row['close'])-D(row['expost_nav'])*D(a)/D(b)
    return None


def rank_and_link(rows,obs,model):
    key=model+'_remaining'
    rank_key=model+'_loss_rank'
    available=[r for r in rows if r[key] is not None]
    losses=sorted((r for r in available if r[key]<0),key=lambda r:(r[key],r['date']))
    for rank,r in enumerate(losses,1):
        r[rank_key]=rank
    blocks=[]
    for missing,group in groupby(rows,key=lambda r:r[key] is None):
        if not missing:
            continue
        batch=list(group)
        value=D(0)
        for units,block in groupby(batch,key=lambda r:r['units']):
            span=list(block)
            start=level(obs[span[0]['previous']],model)
            end=level(obs[span[-1]['date']],model)
            if start is None or end is None:
                value=None
                break
            value+=units*(end-start)
        blocks.append(dict(model=model,previous=batch[0]['previous'],first_unallocated=batch[0]['date'],
                           last_unallocated=batch[-1]['date'],session_count=len(batch),combined_cny=value))
    gross_loss=sum((r[key] for r in losses),D(0))
    positive=sum((r[key] for r in available if r[key]>0),D(0))
    total=None if any(b['combined_cny'] is None for b in blocks) else (
        gross_loss+positive+sum(b['combined_cny'] for b in blocks))
    return blocks,dict(observable=len(available),missing=len(rows)-len(available),
                       losing_days=len(losses),gross_loss=gross_loss,positive_offsets=positive,
                       directly_allocated=gross_loss+positive,net=total,
                       top10_loss=sum(r[key] for r in losses[:10]))


def build(out):
    obs={r['date']:r for r in archived('close_observations.csv')}
    spans=archived('intervals.csv')
    dates=[spans[0]['previous'],*(r['date'] for r in spans)]
    pcf=offerings(dates,obs)
    units=outstanding(dates)
    halt=halt_registry()
    notices=catalog()
    all_issuer=issuer_entries()
    issues,copies=press_by_day()
    rows=[]
    for span in spans:
        d,prev=span['date'],span['previous']
        cur,old=pcf[d],pcf[prev]
        delta=units[d]-units[prev]
        same=[n for n in notices if n['catalog_date']==d and n['risk']]
        prior=[n for n in notices if n['catalog_date']<d and n['risk']]
        active=[n for n in notices if n['event'] and n['effect_from']<=d<=n['effect_through']]
        redemption_closed=any(n['event'] in ('both_closed','redemption_closed') for n in active)
        row=dict(date=d,previous=prev,units=int(span['units']),original_gap=D(span['original_gap_pnl']))
        for model in MODELS:
            val=span[model+'_remaining']
            row[model+'_remaining']=D(val) if val else None
            row[model+'_loss_rank']=None
        row.update(previous_iopv_premium_pct=obs[prev]['close_iopv_premium_pct'],
                   iopv_premium_pct=obs[d]['close_iopv_premium_pct'],previous_effective_cap=old['effective_cap'],
                   creation=cur['creation'],listed_cap=cur['listed_cap'],effective_cap=cur['effective_cap'],
                   previous_shares=units[prev],closing_shares=units[d],net_shares=delta,
                   net_equals_open_cap=delta==cur['listed_cap'] if cur['creation']=='是' else None,
                   pcf_redemption=cur['redemption'],
                   redemption_conflict=redemption_closed and cur['redemption']=='是',
                   effective_notice_urls=' '.join(n['url'] for n in active),pcf_source=cur['pcf_source'],
                   halt_registry_start=halt.get(d,{}).get('stopTime'),
                   sse_warning_count=len(same),distinct_warning_texts=len({n['text_sha256'] for n in same}),issuer_warning_count=sum(
                       r['originalTime']==d and '溢价' in r['title'] for r in all_issuer),
                   same_day_sse_notices=' '.join(n['url'] for n in same),
                   previous_warning=prior[-1]['catalog_date'] if prior else None,
                   previous_warning_url=prior[-1]['url'] if prior else None,
                   press_clock=None,press_signed_dates=None,press_url=None,
                   newspaper_signed_dates=None,newspaper_url=None,causal_cny=None)
        if d in copies:
            row['press_clock'],copy=copies[d]
            row['press_signed_dates']=' '.join(sorted(copy['signed_notices']))
            row['press_url']=copy['url']
        if d in issues:
            row['newspaper_signed_dates']=' '.join(sorted(issues[d]['signed_notices']))
            row['newspaper_url']=issues[d]['url']
        rows.append(row)
    blocks=[]
    summary={}
    totals=json.loads((BASE/'summary.json').read_bytes())['all']['methods']
    for model in MODELS:
        spans_missing,model_summary=rank_and_link(rows,obs,model)
        if model_summary['net'] is None or abs(model_summary['net']-D(totals[model]['remaining_cny']))>D('1e-16'):
            raise ValueError('Daily allocation does not reconcile '+model)
        blocks.extend(spans_missing)
        summary[model]=model_summary
    focus=sorted((r for r in rows if r['es_3m_loss_rank'] and r['es_3m_loss_rank']<=10),
                 key=lambda r:r['es_3m_loss_rank'])
    if {r['date'] for r in focus}!=set(issues):
        raise ValueError('Press investigation does not cover the ranked dates')
    cohort={}
    for key,group in groupby(sorted(rows,key=lambda r:r['creation']),key=lambda r:r['creation']):
        group=list(group)
        status=Counter('unknown' if r['es_3m_remaining'] is None else
                       'loss' if r['es_3m_remaining']<0 else 'gain' if r['es_3m_remaining']>0 else 'flat'
                       for r in group)
        cohort[key]=dict(days=len(group),net_equals_effective_cap=sum(r['net_shares']==r['effective_cap'] for r in group),
                         pnl_sign=dict(status))
    summary.update(creation_cohorts=cohort,source_pdfs=len(notices),causal_cny=None)
    out.mkdir(parents=True,exist_ok=False)
    write_rows(out/'daily.csv',rows)
    write_rows(out/'missing_spans.csv',blocks)
    write_rows(out/'notices.csv',notices)
    (out/'summary.json').write_text(json.dumps(summary,default=str,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('Ranked',len(rows),'sessions;',len(notices),'official notices;',len(blocks),'unallocated spans')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True,type=Path)
    build(parser.parse_args().output)
