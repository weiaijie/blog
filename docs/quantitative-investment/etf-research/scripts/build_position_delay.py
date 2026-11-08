"""Attribute execution-open position gaps and pair the three frozen delay paths."""
import argparse
import csv
from collections import defaultdict
from datetime import date
from decimal import Decimal as D
from itertools import combinations
from pathlib import Path
from tempfile import TemporaryDirectory

from build_signal_audit import CASES, FILLS, HIST, ROOT, SNAP, SYMS, read, save, sha, write_csv
from etf_research.long_history import load_long_history
from etf_research.signal_audit import close_book

TARGETS = ROOT/'reports/2026-11-07-signal-audit/targets.csv'
SENS = HIST/'sensitivity.json'
AUDIT = HIST/'audit.json'
PARTS = ('lot', 'price_move', 'nav_move', 'cash_limit', 'ex_guard', 'move_guard', 'cost_nav')
METRICS = ('ending_nav','net_return','annual_return','max_drawdown','trades','commission','slippage',
           'tax','cash_limited_orders','excluded_orders')
REASONS = {'cash_limited_partial_or_zero':'cash_limit', 'known_ex_dividend_day':'ex_guard',
           'conservative_9pct_buffer':'move_guard'}


def records(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def group(rows, key):
    result = defaultdict(list)
    for row in rows:
        result[row[key]].append(row)
    return result


def require(ok, label):
    if not ok:
        raise ValueError(str(label))


def components(weight, signal_nav, before_nav, after_nav, signal_price, opening, target, held, reason):
    values = dict(lot=target*signal_price-weight*signal_nav,
                  price_move=target*(opening-signal_price), nav_move=-weight*(before_nav-signal_nav),
                  cash_limit=D(0), ex_guard=D(0), move_guard=D(0), cost_nav=weight*(before_nav-after_nav))
    difference = (held-target)*opening
    if difference:
        require(reason in REASONS, ('Unclassified position gap',reason,difference))
        values[REASONS[reason]] = difference
    else:
        require(reason in ('filled','unchanged'), ('Unexpected zero gap',reason))
    require(sum(values.values()) == held*opening-weight*after_nav, 'Exposure identity failed')
    return values


def case_attribution(data, name, capital, targets, fills, decisions):
    by_day = {date.fromisoformat(day):rows for day,rows in group(fills,'day').items()}
    nav, holdings = close_book(data, capital, by_day)
    idx = {str(d):i for i,d in enumerate(data.sessions)}
    actions = {(row['day'],row['symbol']):row for row in decisions}
    require(len(actions)==len(decisions),name+' duplicate decision')
    details = []
    for batch in targets:
        date_text = batch['execution_day']
        require(date_text and batch['state'] != 'pending',name+' requires observed execution')
        i = idx[date_text]
        j = idx[batch['signal_date']]
        require(i-j==int(batch['delay']) and nav[j]==D(batch['signal_nav']),name+' signal')
        day = data.sessions[i]
        marks = [data.bars[s][day] for s in SYMS]
        after = nav[i] + sum(n*(b.open-b.close) for n,b in zip(holdings[i],marks))
        costs = sum((D(f['commission'])+D(f['sell_tax'])-D(f['signed_slippage']) for f in by_day.get(day,())),D(0))
        before = after+costs
        require(after>0 and before>0,name+' NAV')
        for k,(sym,prefix) in enumerate(zip(SYMS,('stock','bond'))):
            action = actions.pop((date_text,sym),None)
            prior, held = holdings[i-1][k], holdings[i][k]
            target = int(batch[prefix+'_target'])
            weight = D(batch[prefix+'_weight'])
            signal_price = D(batch[prefix+'_close'])
            require(prior==int(batch[prefix+'_before']) and signal_price==data.bars[sym][data.sessions[j]].close,name)
            require(target==int((weight*nav[j])//(signal_price*100))*100,name+' lots')
            if action:
                require((action['signal_date'],action['target_units'],action['requested_units'],action['filled_units'])==
                        (batch['signal_date'],target,abs(target-prior),abs(held-prior)),name+' decision')
                reason = action['reason']
            else:
                require(prior==target==held,name+' missing decision')
                reason = 'unchanged'
            opening = marks[k].open
            parts = components(weight,nav[j],before,after,signal_price,opening,target,held,reason)
            actual = held*opening/after
            details.append(dict(run=name,signal_date=batch['signal_date'],execution_day=date_text,symbol=sym,
                                target_weight=weight,actual_weight=actual,signal_nav=nav[j],open_nav_before=before,
                                open_nav_after=after,signal_price=signal_price,open_price=opening,target_units=target,
                                held_units=held,reason=reason,**parts,gap_cny=sum(parts.values()),
                                gap_pp=100*sum(parts.values())/after))
    require(not actions,name+' unmatched decisions')
    return nav, details


def summarize(rows):
    summaries = []
    for symbol, items in group(rows,'symbol').items():
        fields = {col:[r[col]*100/r['open_nav_after'] for r in items] for col in PARTS}
        fields['waiting'] = [(r['price_move']+r['nav_move'])*100/r['open_nav_after'] for r in items]
        fields['gap'] = [r['gap_pp'] for r in items]
        result = dict(run=items[0]['run'],symbol=symbol,batches=len(items))
        for key, values in fields.items():
            result[key+'_mean_pp'] = sum(values)/len(values)
            result[key+'_abs_mean_pp'] = sum(map(abs,values))/len(values)
        summaries.append(result)
    return summaries


def build(out):
    data = load_long_history(SNAP)
    ledgers = read(AUDIT)
    frozen = {r['run']:r for r in read(SENS)['results']}
    targets = group(records(TARGETS),'run')
    fills = group(records(FILLS),'run')
    expected = {f'{s}_{f}_{c}_d{d}' for s,f,c,d in CASES}
    require(set(ledgers)==set(targets)==set(frozen)==expected and set(fills)<=expected,'Account coverage')
    details, summaries, metrics = [], [], []
    elapsed = (data.sessions[-1]-data.sessions[0]).days
    for s, fee, capital, delay in CASES:
        name = f'{s}_{fee}_{capital}_d{delay}'
        orders = ledgers[name]['decisions']
        trades = fills.get(name,[])
        nav, rows = case_attribution(data,name,capital,targets[name],trades,orders)
        details.extend(rows)
        summaries.extend(summarize(rows))
        peak = nav[0]
        depth = D(0)
        for value in nav:
            peak = max(peak,value)
            depth = max(depth,1-value/peak)
        ratio = nav[-1]/capital
        metrics.append(dict(run=name,strategy=s,fee=fee,capital=capital,delay=delay,
            ending_nav=nav[-1],net_return=ratio-1,annual_return=ratio**(D('365.25')/elapsed)-1,max_drawdown=depth,
            trades=len(trades),commission=sum(D(f['commission']) for f in trades),
            slippage=-sum(D(f['signed_slippage']) for f in trades),tax=sum(D(f['sell_tax']) for f in trades),
            cash_limited_orders=sum(o['reason']=='cash_limited_partial_or_zero' for o in orders),
            excluded_orders=sum(o['reason'] in ('known_ex_dividend_day','conservative_9pct_buffer') for o in orders)))
    pairs = []
    for i in range(0,len(metrics),3):
        same = metrics[i:i+3]
        require([x['delay'] for x in same]==[1,2,3] and len({(x['strategy'],x['capital'],x['fee']) for x in same})==1,
                'Unpaired scenarios')
        for a,b in combinations(same,2):
            pairs.append(dict(strategy=a['strategy'],capital=a['capital'],fee=a['fee'],earlier=a['delay'],
                              later=b['delay'],**{key:b[key]-a[key] for key in METRICS}))
    out.mkdir()
    for filename,rows in [('positions',details),('attribution',summaries),('accounts',metrics),('delay_pairs',pairs)]:
        write_csv(out/(filename+'.csv'),rows)
    save(out/'inputs.json',dict(source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in (TARGETS,FILLS,AUDIT,SENS)},
                               market_manifests=data.provenance['manifests_sha256'],sessions=len(data.sessions),
                               start=str(data.sessions[0]),end=str(data.sessions[-1]),position_rows=len(details),
                               batches=len(details)//2,groups=len(metrics)//3))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    output = parser.parse_args().output
    if output.exists():
        parser.error('Use a new output directory')
    output.parent.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(dir=output.parent) as temp:
        stage = Path(temp)/'data'
        build(stage)
        stage.rename(output)
