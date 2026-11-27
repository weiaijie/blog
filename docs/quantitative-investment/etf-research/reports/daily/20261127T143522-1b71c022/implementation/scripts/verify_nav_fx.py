"""Independent check of dated evidence, alternative P&L identities and frozen accounts."""
import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import date
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from market_evidence import evidence, verified_inputs


def read_rows(path):
    with path.open(encoding='utf8') as f:
        return list(csv.DictReader(f))


def near(x,y):
    if abs(D(x)-D(y))>D('1e-16'):
        raise ValueError(f'Reconciliation mismatch: {x} vs {y}')


def verify(folder):
    base = ROOT/'reports/2026-11-08-three-markets'
    domestic,days,bars,_ = verified_inputs(evidence())
    source = read_rows(folder/'market.csv')
    quotes = {}
    for r in source:
        d = date.fromisoformat(r['date'])
        s = r['symbol']
        if (s,d) in quotes:
            raise ValueError('Repeated market observation')
        quotes[s,d] = r
        near(r['close_cny'],bars[s][d].close)
        # This immutable vintage has complete manager and both distributor unit NAVs on all market days.
        near(r['manager_nav'],r['ths_nav'])
        near(r['manager_nav'],r['eastmoney_nav'])
        near(r['manager_nav'],r['nav_cny'])
        near(r['safe_cny_per_fc'],r['pbc_cny_per_fc'])
        near(r['safe_cny_per_fc'],r['cny_per_fc'])
        near((D(r['premium_pct'])/100+1)*D(r['nav_cny']),r['close_cny'])
    if set(quotes)!={(s,d) for d in days for s in ('513500','159920')}:
        raise ValueError('Market coverage')
    def chosen(name):
        return [r for r in read_rows(base/(name+'.csv')) if (r['group'],r['years'])==('513500','2')]
    account = {r['date']:r for r in chosen('daily')}
    orders = chosen('orders')
    meta, = chosen('accounts')
    active = sorted(k for k in account if meta['peak']<=k<=meta['trough'])
    output = read_rows(folder/'drawdown.csv')
    if [r['date'] for r in output]!=active[1:]:
        raise ValueError('Drawdown interval coverage')
    total = defaultdict(D)
    nav_bridge = D(0)
    symmetric_premium = D(0)
    for prev,cur,row in zip(active,active[1:],output):
        d0,d1 = map(date.fromisoformat,(prev,cur))
        acct0,acct1 = account[prev],account[cur]
        a,b = quotes['513500',d0],quotes['513500',d1]
        q0,q1 = (int(r['units_513500']) for r in (acct0,acct1))
        dq = q1-q0
        n0,n1 = D(a['nav_cny']),D(b['nav_cny'])
        x0,x1 = D(a['cny_per_fc']),D(b['cny_per_fc'])
        p0,p1 = D(a['close_cny']),D(b['close_cny'])
        # End-value less start-value less net purchases at end mark.
        nav_pnl = q1*n1-q0*n0-dq*n1
        stock_pnl = q1*p1-q0*p0-dq*p1
        native = q0*(n1/x1-n0/x0)*(x0+x1)/2
        near(row['nav_in_fx_units'],native)
        near(row['fx_translation'],nav_pnl-native)
        near(row['premium_gap'],stock_pnl-nav_pnl)
        nav_bridge += nav_pnl
        ratio_nav = q0*(n1-n0)*(p0/n0+p1/n1)/2
        symmetric_premium += stock_pnl-ratio_nav
        # Independently reconstruct NAV using ending stock, bond, cash and receivables.
        def equity(acct,day):
            return (D(acct['cash'])+D(acct['receivables'])+
                    sum(int(acct['units_'+s])*bars[s][day].close for s in ('513500','511010')))
        near(equity(acct1,d1)-equity(acct0,d0),row['account_change'])
        near(row['account_change'],D(acct1['equity'])-D(acct0['equity']))
        trades = [t for t in orders if t['day']==cur and int(t['filled'])]
        near(row['commission'],-sum(D(t['fee']) for t in trades))
        intraday = slip = D(0)
        for t in trades:
            units = int(t['filled'])*(1 if t['side']=='buy' else -1)
            raw = bars[t['symbol']][d1]
            intraday += units*(raw.close-raw.open)
            slip += units*(raw.open-D(t['modeled_price']))
        near(row['slippage'],slip)
        near(row['rebalance_intraday'],intraday)
        near(row['bond_price'],int(acct0['units_511010'])*(bars['511010'][d1].close-bars['511010'][d0].close))
        near(row['dividend_entitlement'],sum(e.per_share*int(account[str(e.record_date)]['units_'+e.symbol])
                                              for e in domestic.dividends if e.ex_date==d1 and e.symbol in ('513500','511010')))
        for k in ('nav_in_fx_units','fx_translation','premium_gap','bond_price','dividend_entitlement',
                  'commission','slippage','rebalance_intraday','stock_without_nav_split','nav_without_fx_split'):
            total[k] += D(row[k])
        for k in ('stock_without_nav_split','nav_without_fx_split','residual'):
            near(row[k],0)
    result = json.loads((folder/'attribution.json').read_text())
    difference = D(account[active[-1]]['equity'])-D(account[active[0]]['equity'])
    near(sum(total.values()),difference)
    near(difference/D(account[active[0]]['equity']),meta['max_drawdown'])
    near(nav_bridge,total['nav_in_fx_units']+total['fx_translation'])
    for k,v in total.items():
        near(result['pnl_cny'][k],v)
        near(result['peak_percentage_points'][k],100*v/D(account[active[0]]['equity']))
    near(result['pnl_cny']['account_change'],difference)
    near(result['symmetric_rate_premium_cny'],symmetric_premium)
    peak,trough = date.fromisoformat(active[0]),date.fromisoformat(active[-1])
    fixed = sum(int(account[active[0]]['units_'+s])*(bars[s][trough].close-bars[s][peak].close)
                for s in ('513500','511010'))
    fixed += sum(e.per_share*int(account[min(str(peak),str(e.record_date))]['units_'+e.symbol])
                 for e in domestic.dividends if peak<e.ex_date<=trough and e.symbol in ('513500','511010'))
    near(result['constant_peak_positions_pnl'],fixed)
    near(result['actual_minus_constant_peak_positions'],difference-fixed)
    print('PASS',len(quotes),'fund dates,',len(output),'daily bridges and archived maximum drawdown')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('folder',type=Path)
    verify(p.parse_args().folder)
