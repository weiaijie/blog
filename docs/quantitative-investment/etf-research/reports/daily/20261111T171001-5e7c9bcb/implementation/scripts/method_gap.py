"""Daily signed P&L attribution between installments and a single initial allocation."""
import argparse
import csv
from pathlib import Path

import interactive_backtest as work
from method_windows import DEFAULTS, prepare, allocation_ledgers
from overlay_attribution import cumulative_ledger, daily_gap, interval

CASE = dict(DEFAULTS,start='2021-10-29',end='2022-10-31')
SYMBOLS = ('510300','511010')
ACCOUNTS = ('allocation','installments')


def gap_detail(params):
    config, days, _, simulate = prepare(params)
    base, _, bars, _ = work.inputs()
    books = allocation_ledgers(config, days, bars, simulate)
    daily = {name: book[0] for name,book in books.items()}
    ledgers = {name:cumulative_ledger(rows,orders,bars,base.dividends) for name,(rows,orders) in books.items()}
    period = interval(ledgers,days[0],days[-1])
    holding = period['differences']['installments-allocation']
    gaps = daily_gap(ledgers['installments'],ledgers['allocation'],holding,include_accounts=True)
    rows = []
    previous_gap = 0
    for i, gap in enumerate(gaps['days']):
        day = gap['date']
        assets = {}
        for symbol in SYMBOLS:
            bar = bars[symbol][day]
            asset = dict(open=bar.open,close=bar.close,previousClose=bars[symbol][days[i-1]].close if i else None,
                         difference=gap['byEtf'][symbol])
            for name in ACCOUNTS:
                holdings = 'units_'+symbol
                asset[name] = dict(before=daily[name][i-1][holdings] if i else 0,after=daily[name][i][holdings],
                                   **gap['targetBreakdown' if name=='installments' else 'referenceBreakdown']['byEtf'][symbol])
            assets[symbol] = asset
        width_change = abs(gap['cumulative'])-abs(previous_gap)
        rows.append(dict(date=day,assets=assets,change=gap['change'],cumulative=gap['cumulative'],
                         widthChange=width_change,equity={k:daily[k][i]['equity'] for k in ACCOUNTS}))
        previous_gap = gap['cumulative']
    widening = sorted((r for r in rows if r['widthChange']>0),key=lambda r:-r['widthChange'])
    return dict(parameters=params,direction='installments-allocation',start=days[0],end=days[-1],
                days=rows,widening=[r['date'] for r in widening[:3]],worsening=gaps['decreases'],
                improving=gaps['increases'],totals=holding['totals'],byEtf={s:holding['byEtf'][s] for s in SYMBOLS},
                accounts={k:dict(pnl=period['accounts'][k]['accountChange'],orders=books[k][1]) for k in ACCOUNTS})


def export_rows(report):
    for day in report['days']:
        for symbol, asset in day['assets'].items():
            row=dict(date=day['date'],symbol=symbol,previous_close=asset['previousClose'],open=asset['open'],close=asset['close'])
            for name in (*ACCOUNTS,'difference'):
                row.update({name+'_'+k:v for k,v in asset[name].items()})
            yield dict(**row,allocation_equity=day['equity']['allocation'],installments_equity=day['equity']['installments'],
                       day_gap=day['change'],cumulative_gap=day['cumulative'],absolute_gap_change=day['widthChange'])


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export',type=Path,required=True)
    args=parser.parse_args()
    result=gap_detail(CASE)
    rows=list(export_rows(result))
    with args.export.open('x',encoding='utf-8',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=rows[0],lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    print(work.encode({k:v for k,v in result.items() if k not in ('days','accounts')}).decode())
    for row in result['days']:
        if row['date'] in result['widening']+result['worsening']+result['improving']:
            print(row['date'],row['change'],row['cumulative'],[(s,a['difference']['net']) for s,a in row['assets'].items()])
    for name,a in result['accounts'].items():
        print(name,a['pnl'],[(str(o['day']),o['symbol'],o['side'],o['filled'],str(o['modeled_price'])) for o in a['orders']])
