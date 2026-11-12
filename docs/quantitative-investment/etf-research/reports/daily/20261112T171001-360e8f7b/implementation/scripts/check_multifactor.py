"""Reproduce the fixed research example and compare with the same-capital buy-and-hold account."""
import json

import interactive_backtest as work
from model_replay import replay
from multifactor_strategy import MODEL

CASE = dict(work.DEFAULTS, weights='1,0,0,1', start='2021-10-29', end='2022-10-31', rebalance='signal')


def check_case(case):
    result = {}
    for model in (MODEL, 'allocation'):
        params = dict(case, model=model, step='all', rebalance='signal' if model == MODEL else 'hold')
        frames = replay(params)['frames']
        orders = [order for row in frames for order in row['orders']]
        signals = [row for row in frames if row['nextPlan']]
        for prev, row in zip(frames, frames[1:]):
            for order in row['orders']:
                if order['signal'] != prev['date'] or order['target'] != prev['nextPlan']['target'][order['symbol']]:
                    raise ValueError('Opening order differs from the preceding close decision')
        result[model] = dict(sessions=len(frames), plans=len(signals),
                             filled=sum(o['filled'] > 0 for o in orders),
                             unfilled_or_partial=sum(o['filled'] < o['requested'] for o in orders),
                             commissions=sum(o['fee'] for o in orders), endEquity=frames[-1]['equity'],
                             pnl=frames[-1]['pnl'], maxDrawdown=min(f['drawdown'] for f in frames))
        if model == MODEL:
            result[model]['firstSwitch'] = next((dict(signal=prev['decision'], plan=prev['nextPlan'],
                execution=day['date'], orders=day['orders']) for prev, day in zip(frames, frames[1:])
                if prev['decision']['transition']=='switch'), None)
    return result


if __name__ == '__main__':
    long_case = dict(CASE, start=work.OPTIONS['trendFirst'], end=work.OPTIONS['last'])
    print(json.dumps({span['start']+'/'+span['end']: check_case(span) for span in (CASE,long_case)},
                     default=str, indent=2, ensure_ascii=False))
