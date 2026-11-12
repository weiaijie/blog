"""Explain profitable two-year factor windows below 4% versus same-entry buy-and-hold."""
import argparse
from collections import Counter, defaultdict
from decimal import Decimal as D
import json
from pathlib import Path

from build_entry_windows import TARGET, entry_schedule
from etf_research.accounting import Costs
from method_windows import DEFAULTS, FACTOR_MODEL, archived_entries, prepare
from model_replay import replay
from multifactor_strategy import STOCK, BOND

NO_COST = Costs(0, 0, 0, 0)


def schedules(sessions, decisions):
    actual, keep_stock = {}, {}
    previous = None
    entered_stock = False
    for signal, opening in zip(sessions, sessions[1:]):
        regime = decisions[signal]['regime']
        if regime == previous:
            continue
        entry = dict(denominators={BOND:1} if regime == 'bonds' else {STOCK:2,BOND:2})
        actual[opening] = entry
        # Same initial target and first stock entry; then retain the balanced holdings.
        if not keep_stock or (regime == 'balanced' and not entered_stock):
            keep_stock[opening] = entry
        if regime == 'balanced':
            entered_stock = True
        previous = regime
    return actual, keep_stock


def friction(orders):
    commission = sum((o['fee'] for o in orders),D(0))
    slip = sum(((o['modeled_price']-o['open'])*o['filled']*(1 if o['side']=='buy' else -1)
                for o in orders),D(0))
    return commission, slip


def exposure(factor, fixed, bars, events):
    """Allocate gross P&L differences by actual intraday/overnight exposure and dividend entitlement."""
    parts = defaultdict(lambda: {STOCK:D(0),BOND:D(0)})
    episodes = []
    tags = {}
    state = 'other'
    def accrue(tag, symbol, amount):
        parts[tag][symbol] += amount

    for i in range(1,len(factor)):
        f, b = factor[i], fixed[i]
        f0, b0 = factor[i-1], fixed[i-1]
        day, prev = f['date'], f0['date']
        prior_state = state
        if f['units_'+STOCK] > 0:
            state = 'other'
        elif f0['units_'+STOCK] > 0:
            state = len(episodes)
            episodes.append(dict(signal=prev,entry=day,exit=None))
        elif state == 'other' and f['units_'+BOND] > 0:
            state = 'initialBonds'
        if isinstance(prior_state,int) and prior_state != state:
            episodes[prior_state]['exit'] = day
        if isinstance(state,int) and f['units_'+BOND] <= 0:
            raise ValueError(f'Cannot classify a stock exit without a bond position on {day}')
        tags[day] = state
        for symbol in (STOCK,BOND):
            units = 'units_'+symbol
            bar = bars[symbol][day]
            accrue(prior_state,symbol,(f0[units]-b0[units])*(bar.open-bars[symbol][prev].close))
            accrue(state,symbol,(f[units]-b[units])*(bar.close-bar.open))
    positions = {f['date']:(f,b) for f,b in zip(factor,fixed,strict=True)}
    for e in events:
        if e.symbol in (STOCK,BOND) and e.record_date in positions and e.ex_date <= factor[-1]['date']:
            f,b = positions[e.record_date]
            accrue(tags.get(e.record_date,'other'),e.symbol,(f['units_'+e.symbol]-b['units_'+e.symbol])*e.per_share)
    stock = bond = D(0)
    for j, episode in enumerate(episodes):
        s,b = parts[j][STOCK], parts[j][BOND]
        episode.update(stock=s,bond=b,net=s+b)
        stock += s
        bond += b
    return dict(exitStock=stock,exitBond=bond,initialBonds=sum(parts['initialBonds'].values()),
                otherExposure=sum(parts['other'].values()),exits=len(episodes),
                worstEpisode=min(episodes,key=lambda e:e['net'],default=None))


def build():
    config, days, initial, simulate = prepare(DEFAULTS)
    config.pop('installments')
    frames = replay(dict(config,model=FACTOR_MODEL,rebalance='signal',step='all'))['frames']
    decisions = {f['date']:f['decision'] for f in frames}
    archive = archived_entries()
    rows = []
    for sessions, ends in entry_schedule(days):
        if 2 not in ends:
            continue
        start, end = sessions[0],sessions[ends[2]]
        entry = archive[str(start),2]
        nav, benchmark = D(entry[FACTOR_MODEL]), D(entry['allocation'])
        threshold = initial*(1+TARGET)**(D((end-start).days)/D('365.25'))
        if not initial < nav < threshold:
            continue
        actual, keep = schedules(sessions,decisions)
        factor, orders = simulate(sessions,schedule=actual)
        fixed, fixed_orders = simulate(sessions)
        if (factor[-1]['equity'],fixed[-1]['equity'],str(end)) != (nav,benchmark,entry['end']):
            raise ValueError(f'Archived accounts differ on {start}')
        parts = exposure(factor,fixed,simulate.keywords['bars'],simulate.keywords['events'])
        fc,fs = friction(orders)
        bc,bs = friction(fixed_orders)
        switch_commission,switch_slippage = friction([o for o in orders if o['day'] != sessions[1]])
        switch_cost = switch_commission + switch_slippage
        gap = nav-benchmark
        cost = fc+fs-bc-bs
        exit_net = parts['exitStock']+parts['exitBond']
        if exit_net+parts['initialBonds']+parts['otherExposure']-cost != gap:
            raise ValueError(f'Attribution mismatch on {start}')
        nocost = simulate(sessions,schedule=actual,costs=NO_COST)[0][-1]['equity']
        retained = simulate(sessions,schedule=keep)[0][-1]['equity']
        rows.append(dict(start=start,end=end,factorEquity=nav,allocationEquity=benchmark,gap=gap,
                         threshold=threshold,allocationReached=benchmark>=threshold,
                         **parts,exitNet=exit_net,missedRally=parts['exitStock']<0 and exit_net<0,
                         factorCommission=fc,factorSlippage=fs,allocationCommission=bc,allocationSlippage=bs,
                         switchCommission=switch_commission,switchSlippage=switch_slippage,
                         switchAddbackReached=nav+switch_cost>=threshold,
                         excessCost=cost,noCostEquity=nocost,noCostReached=nocost>=threshold,
                         retainEquity=retained,retainReached=retained>=threshold))
    counts = Counter()
    for row in rows:
        for key in ('allocationReached','missedRally','noCostReached','retainReached','switchAddbackReached'):
            counts[key] += row[key]
        counts['behind'] += row['gap']<0
        counts['extraCost'] += row['excessCost']>0
        counts['bothReached'] += row['noCostReached'] and row['retainReached']
        counts['missedAndExtraCost'] += row['missedRally'] and row['excessCost']>0
        counts['costReversesRanking'] += row['gap']<0 and row['gap']+row['excessCost']>=0
    rows.sort(key=lambda row:row['gap'])
    top = sorted(rows,key=lambda row:-abs(row['gap']))[:3]
    return dict(parameters=DEFAULTS,years=2,counts=dict(windows=len(rows),**counts),
                largestAbsolute=[r['start'] for r in top],largestLag=[r['start'] for r in rows if r['gap']<0][:3],
                windows=rows)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export',required=True,type=Path)
    args=parser.parse_args()
    result=build()
    with args.export.open('x',encoding='utf-8',newline='\n') as file:
        json.dump(result,file,default=str,ensure_ascii=False,separators=(',',':'))
        file.write('\n')
    print(result['counts'],result['largestAbsolute'],result['largestLag'])
