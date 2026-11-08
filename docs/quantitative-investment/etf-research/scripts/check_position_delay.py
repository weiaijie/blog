"""Verify attribution against the frozen ledger and delay contrasts against sealed endpoints."""
import argparse
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal as D
from itertools import combinations
from pathlib import Path

from build_position_delay import (AUDIT, CASES, FILLS, METRICS, ROOT, SENS, SNAP, SYMS, TARGETS,
                                 group, load_long_history, read, records, sha)
from etf_research.baselines import run as replay


def equal(actual, expected, label):
    if actual != expected:
        raise ValueError(f'{label}: {actual} != {expected}')


def near(actual, expected, label, tolerance=D('1e-22')):
    if abs(D(actual)-D(expected)) > tolerance:
        raise ValueError(f'{label}: {actual} != {expected}')


def reference_metrics(account):
    return dict(ending_nav=D(account['ending_equity']),net_return=D(str(account['total_return'])),
                annual_return=D(str(account['annualized_scenario_return'])),
                max_drawdown=-D(str(account['max_close_drawdown'])),trades=account['trades'],
                commission=D(account['commissions']),slippage=D(account['slippage_cost']),tax=D(account['sell_tax']),
                cash_limited_orders=account['cash_limited_orders'],excluded_orders=account['excluded_orders'])


def verify_case(data, name, result, target_rows, detail, summaries):
    by_date = {r['date']:r for r in result['daily']}
    days = data.sessions
    index = {d:i for i,d in enumerate(days)}
    reason = {(d['day'],d['symbol']):d['reason'] for d in result['decisions']}
    costs, income = Counter(), Counter()
    for entry in result['journal']:
        day = entry['day']
        if entry['kind']=='trade':
            costs[day] += (entry['commission'] + entry['tax']
                           + abs(entry['fill_price']-entry['raw_price'])*entry['units'])
        elif entry['kind']=='dividend_receivable':
            income[day] += entry['amount']
    equal(len(detail),2*len(target_rows),name)
    collected = defaultdict(lambda:defaultdict(list))
    for n, batch in enumerate(target_rows):
        sd = date.fromisoformat(batch['signal_date'])
        day = date.fromisoformat(batch['execution_day'])
        prev = days[index[day]-1]
        prior, close = by_date[prev], by_date[day]
        signal_nav = by_date[sd]['equity']
        # Mark yesterday's actual positions to today's open, credit today's ex-date entitlement.
        before = prior['equity'] + income[day] + sum(prior['units_'+s]*(data.bars[s][day].open-data.bars[s][prev].close)
                                                     for s in SYMS)
        after = before - costs[day]
        for j,(s,prefix) in enumerate(zip(SYMS,('stock','bond'))):
            row = detail[2*n+j]
            label = f'{name} {day} {s}'
            equal((row['symbol'],row['signal_date'],row['execution_day']),(s,str(sd),str(day)),label)
            w = D(batch[prefix+'_weight'])
            target = int(batch[prefix+'_target'])
            units = close['units_'+s]
            op, cp = data.bars[s][day].open, data.bars[s][sd].close
            why = reason.get((day,s),'unchanged')
            equal(row['reason'],why,label)
            numeric = dict(signal_nav=signal_nav,open_nav_before=before,open_nav_after=after,target_weight=w,
                           held_units=units,target_units=target,signal_price=cp,open_price=op)
            for key,value in numeric.items():
                equal(D(row[key]),value,label+' '+key)
            # Trace signed residuals at successive valuation/holding stages, all in CNY.
            chain = [D(0), target*cp-w*signal_nav, target*op-w*signal_nav, target*op-w*before,
                     units*op-w*before, units*op-w*after]
            lot,price,nav,shortfall,cost = [b-a for a,b in zip(chain,chain[1:])]
            bucket = {'cash_limited_partial_or_zero':'cash_limit','known_ex_dividend_day':'ex_guard',
                      'conservative_9pct_buffer':'move_guard'}.get(why)
            expected = dict(lot=lot,price_move=price,nav_move=nav,cost_nav=cost)
            for key in ('cash_limit','ex_guard','move_guard'):
                expected[key] = shortfall if key==bucket else 0
            equal(sum(expected.values()),chain[-1],label+' residual')
            for k,v in expected.items():
                equal(D(row[k]),v,label+' '+k)
            equal(D(row['gap_cny']),chain[-1],label+' gap')
            near(row['actual_weight'],units*op/after,label)
            near(row['gap_pp'],(units*op/after-w)*100,label)
            expected.update(waiting=price+nav,gap=chain[-1])
            for k,v in expected.items():
                collected[s][k].append(D(v)*100/after)
    equal([r['symbol'] for r in summaries],list(SYMS),name+' summary coverage')
    for row in summaries:
        for k,values in collected[row['symbol']].items():
            equal(int(row['batches']),len(values),name)
            near(row[k+'_mean_pp'],sum(values)/len(values),name+' '+k)
            near(row[k+'_abs_mean_pp'],sum(map(abs,values))/len(values),name+' abs '+k)


def verify(folder):
    data = load_long_history(SNAP)
    frozen = {r['run']:r for r in read(SENS)['results']}
    targets = group(records(TARGETS),'run')
    detail = group(records(folder/'positions.csv'),'run')
    attr = group(records(folder/'attribution.csv'),'run')
    accounts = records(folder/'accounts.csv')
    pairs = records(folder/'delay_pairs.csv')
    prefixes = read(folder/'inputs.json')
    paths = (TARGETS,FILLS,AUDIT,SENS)
    equal(prefixes,dict(source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in paths},
                        market_manifests=data.provenance['manifests_sha256'],sessions=len(data.sessions),
                        start=str(data.sessions[0]),end=str(data.sessions[-1]),
                        position_rows=sum(map(len,detail.values())),batches=sum(map(len,targets.values())),
                        groups=len(CASES)//3),'input coverage')
    names = [f'{s}_{f}_{c}_d{d}' for s,f,c,d in CASES]
    equal([r['run'] for r in accounts],names,'scenario order')
    for source in (frozen,targets,detail,attr):
        equal(set(source),set(names),'account coverage')
    def check_metrics(row,expected,tags):
        for key in METRICS:
            # The archived return and drawdown ratios are JSON floats.
            tol = D('1e-14') if key in ('net_return','annual_return','max_drawdown') else D(0)
            near(row[key],expected[key],tags+' '+key,tol)
    expected_pairs = []
    for row,(s,f,c,d) in zip(accounts,CASES):
        name = row['run']
        equal((row['strategy'],row['fee'],int(row['capital']),int(row['delay'])),(s,f,c,d),name)
        check_metrics(row,reference_metrics(frozen[name]),name)
        replayed = replay(data,s,f,D(c),execution_delay=d)
        verify_case(data,name,replayed,targets[name],detail[name],attr[name])
        if d==1:
            expected_pairs.extend((s,f,c,a,b) for a,b in combinations((1,2,3),2))
    equal(len(pairs),len(expected_pairs),'pair count')
    for row,(s,f,c,a,b) in zip(pairs,expected_pairs):
        equal((row['strategy'],row['fee'],int(row['capital']),int(row['earlier']),int(row['later'])),
              (s,f,c,a,b),'pair identity')
        left = reference_metrics(frozen[f'{s}_{f}_{c}_d{a}'])
        right = reference_metrics(frozen[f'{s}_{f}_{c}_d{b}'])
        check_metrics(row,{k:right[k]-left[k] for k in METRICS},str((s,f,c,a,b)))
    print(f"PASS {prefixes['position_rows']} exposures, {len(accounts)} scenarios, "
          f"{len(pairs)} paired contrasts in {prefixes['groups']} groups")


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--folder',required=True,type=Path)
    verify(p.parse_args().folder)
