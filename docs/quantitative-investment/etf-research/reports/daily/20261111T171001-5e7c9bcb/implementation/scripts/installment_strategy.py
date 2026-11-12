"""Emit monthly allocation targets from a Backtrader close-by-close strategy."""
from fractions import Fraction

import backtrader as bt
import pandas as pd


class MonthlyInstallments(bt.Strategy):
    params = (('next_session', None), ('installments', 3), ('rebalance', 'monthly'))

    def __init__(self):
        self.schedule = {}
        self.batch = 0
        self.last_month = None

    def next(self):
        execution = self.p.next_session.get(self.data.datetime.date(0))
        if execution is None:
            return
        month = (execution.year, execution.month)
        if month == self.last_month:
            return
        self.last_month = month
        if self.batch < self.p.installments:
            self.batch += 1
            reason = 'installment'
        elif self.p.rebalance == 'monthly':
            reason = 'monthly'
        else:
            return
        self.schedule[execution] = (self.batch, reason)


def installment_schedule(days, visible, quotes, installments, rebalance, denominators):
    # Only the next exchange date is known in advance. No future price is in the feed.
    frame = pd.DataFrame({'close': [float(quotes[d].close) for d in visible]},
                         index=pd.DatetimeIndex(visible))
    engine = bt.Cerebro(stdstats=False, preload=False, runonce=False)
    engine.adddata(bt.feeds.PandasData(dataname=frame))
    engine.addstrategy(MonthlyInstallments, next_session=dict(zip(visible, days[1:])),
                       installments=installments, rebalance=rebalance)
    strategy, = engine.run()
    result = {}
    for day, (batch, reason) in strategy.schedule.items():
        scale = Fraction(installments, batch)
        result[day] = dict(denominators={s:den*scale for s,den in denominators.items()},
                           batch=batch, installments=installments, reason=reason)
    return result
