"""Ex-post reconciliation of the archived two-year S&P ETF/bond account drawdown."""
import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from market_evidence import evidence, verified_inputs
from nav_fx_sources import market_rows, responses
from compare_three_markets import csv_out

BASE = ROOT/'reports/2026-11-08-three-markets'
PEAK, TROUGH = date(2024,12,16), date(2025,4,7)
STOCK, BOND = '513500','511010'
PARTS = ('nav_in_fx_units','fx_translation','nav_without_fx_split','premium_gap','stock_without_nav_split',
         'bond_price','dividend_entitlement','rebalance_intraday','slippage','commission')


def account_files():
    manifest = json.loads((BASE/'manifest.json').read_text())
    selected = []
    for name in ('accounts','daily','orders'):
        path = BASE/(name+'.csv')
        if hashlib.sha256(path.read_bytes()).hexdigest() != manifest[path.relative_to(ROOT).as_posix()]:
            raise ValueError('Archived account input changed '+name)
        with path.open(encoding='utf8') as f:
            selected.append([r for r in csv.DictReader(f) if r['group']==STOCK and r['years']=='2'])
    meta, history, orders = selected
    if len(meta)!=1 or (meta[0]['peak'],meta[0]['trough']) != (str(PEAK),str(TROUGH)):
        raise ValueError('Different maximum drawdown in archived account')
    by_date = {date.fromisoformat(r['date']):r for r in history}
    by_trade = defaultdict(list)
    for r in orders:
        by_trade[date.fromisoformat(r['day'])].append(r)
    return by_date,by_trade


def stock_parts(q, prev, curr):
    p0,p1 = prev['close_cny'],curr['close_cny']
    n0,n1 = prev['nav_cny'],curr['nav_cny']
    x0,x1 = prev['cny_per_fc'],curr['cny_per_fc']
    if n0 is None or n1 is None:
        return {'stock_without_nav_split':q*(p1-p0)}
    parts = {'premium_gap':q*((p1-n1)-(p0-n0))}
    if x0 is None or x1 is None:
        parts['nav_without_fx_split'] = q*(n1-n0)
    else:
        u0,u1 = n0/x0,n1/x1
        parts['fx_translation'] = q*(u0+u1)/2*(x1-x0)
        parts['nav_in_fx_units'] = q*(n1-n0)-parts['fx_translation']
    return parts


def reconcile(days, bars, events, market, history, orders):
    selected = [d for d in days if PEAK<=d<=TROUGH]
    if selected[0]!=PEAK or selected[-1]!=TROUGH:
        raise ValueError('Peak or trough missing')
    listed = {r['date']:r for r in market if r['symbol']==STOCK}
    peak_equity = D(history[PEAK]['equity'])
    daily = []
    for prior,day in zip(selected,selected[1:]):
        prev,cur = history[prior],history[day]
        q0 = {s:int(prev['units_'+s]) for s in (STOCK,BOND)}
        share_change = dict.fromkeys(q0,0)
        components = dict.fromkeys(PARTS,D(0))
        components.update(stock_parts(q0[STOCK],listed[prior],listed[day]))
        components['bond_price'] = q0[BOND]*(bars[BOND][day].close-bars[BOND][prior].close)
        for e in events:
            if e.ex_date==day and e.symbol in q0:
                components['dividend_entitlement'] += int(history[e.record_date]['units_'+e.symbol])*e.per_share
        for r in orders.get(day,[]):
            s = r['symbol']
            quantity = int(r['filled'])*(1 if r['side']=='buy' else -1)
            share_change[s] += quantity
            opening = bars[s][day].open
            if opening!=D(r['open']):
                raise ValueError('Opening price mismatch')
            components['rebalance_intraday'] += quantity*(bars[s][day].close-opening)
            components['slippage'] += quantity*(opening-D(r['modeled_price']))
            components['commission'] -= D(r['fee'])
        if any(q0[s]+share_change[s]!=int(cur['units_'+s]) for s in q0):
            raise ValueError('Position conservation failed')
        change = D(cur['equity'])-D(prev['equity'])
        residual = change-sum(components.values())
        if abs(residual)>D('1e-16'):
            raise ValueError('Daily P&L mismatch on '+str(day))
        daily.append(dict(date=day,previous=prior,opening_stock_units=q0[STOCK],opening_bond_units=q0[BOND],
                          stock_units_change=share_change[STOCK],bond_units_change=share_change[BOND],
                          equity=D(cur['equity']),account_change=change,**components,residual=residual))
    totals = {k:sum(r[k] for r in daily) for k in (*PARTS,'account_change')}
    last_equity = D(history[TROUGH]['equity'])
    if totals['account_change'] != last_equity-peak_equity:
        raise ValueError('Cumulative P&L mismatch')
    held_change = sum(int(history[PEAK]['units_'+s])*(bars[s][TROUGH].close-bars[s][PEAK].close) for s in (STOCK,BOND))
    for e in events:
        if PEAK < e.ex_date <= TROUGH and e.symbol in (STOCK,BOND):
            record = min(PEAK,e.record_date)
            held_change += int(history[record]['units_'+e.symbol])*e.per_share
    endpoints = {str(d):[r for r in market if r['date']==d] for d in (PEAK,TROUGH)}
    # Sensitivity: allocate the NAV/premium-rate interaction symmetrically, using previous close holdings.
    alternative = None
    if all(listed[d]['nav_cny'] is not None for d in selected):
        alternative = D(0)
        for prev,day in zip(selected,selected[1:]):
            v,w = listed[prev],listed[day]
            alternative += int(history[prev]['units_'+STOCK])*(w['premium_pct']-v['premium_pct'])/100*(
                v['nav_cny']+w['nav_cny'])/2
    summary = dict(peak=PEAK,trough=TROUGH,peak_equity=peak_equity,trough_equity=last_equity,
                   intervals=len(daily),pnl_cny=totals,
                   peak_percentage_points={k:v/peak_equity*100 for k,v in totals.items()},
                   constant_peak_positions_pnl=held_change,actual_minus_constant_peak_positions=totals['account_change']-held_change,
                   symmetric_rate_premium_cny=alternative,endpoints=endpoints,
                   actual_currency_exposure_pnl=None,synchronous_intraday_premium_pnl=None)
    return daily,summary


def build(out):
    domestic,days,bars,_ = verified_inputs(evidence())
    market = market_rows(responses(),days,bars)
    history,orders = account_files()
    daily,summary = reconcile(days,bars,domestic.dividends,market,history,orders)
    summary['coverage'] = {s:dict(Counter(r['nav_status']+'/'+r['fx_status'] for r in market if r['symbol']==s))
                           for s in (STOCK,'159920')}
    out.mkdir(parents=True,exist_ok=False)
    csv_out(out/'market.csv',market)
    csv_out(out/'drawdown.csv',daily)
    (out/'attribution.json').write_text(json.dumps(summary,default=str,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(len(market),'fund dates;',len(daily),'P&L intervals;',summary['pnl_cny']['account_change'],'RMB')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    build(parser.parse_args().output)
