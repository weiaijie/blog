from datetime import date, timedelta
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from check_multifactor import CASE
import interactive_backtest as work
from model_replay import replay
from multifactor_strategy import MODEL, STOCK, BOND, factor_schedule


class MultifactorTests(unittest.TestCase):
    def test_dividend_neutral_prices_ties_and_announcement_cutoff(self):
        days = [date(2020,1,1) + timedelta(days=i) for i in range(123)]
        bars = {s:{d:SimpleNamespace(close=D(100)) for d in days} for s in (STOCK,BOND)}
        bars[STOCK][days[-1]].close = D(99)
        dividend = SimpleNamespace(symbol=STOCK, ex_date=days[-1], announcement_date=days[-2], per_share=D(1))
        observations, plans = factor_schedule(days[:120], days[120:], days[120:], bars, [dividend])
        final = observations[days[-1]]
        self.assertEqual([(f['value'], f['passed']) for f in final['factors']], [(0,False),(0,False),(0,True)])
        self.assertEqual(final['transition'], 'hold')
        self.assertEqual(list(plans), [days[121]])
        dividend.announcement_date = days[-1] + timedelta(days=1)
        observations, _ = factor_schedule(days[:120], days[120:], days[120:], bars, [dividend])
        self.assertLess(observations[days[-1]]['factors'][0]['value'], 0)

    def test_real_signal_and_execution_block(self):
        params = dict(CASE, model=MODEL, step='6')
        rows = replay(params)['frames']
        decision, next_open = rows[3], rows[4]
        self.assertEqual(str(decision['date']), '2021-11-03')
        self.assertEqual(decision['decision']['votes'], 1)
        self.assertEqual(decision['nextPlan']['target'], {STOCK:0, BOND:700})
        self.assertEqual([(o['side'],o['filled']) for o in next_open['orders']], [('sell',10000),('buy',300)])
        base, calendar, bars, halts = work.inputs()
        forced = set(halts) | {(next_open['date'], STOCK)}
        with patch.object(work,'inputs',return_value=(base,calendar,bars,forced)):
            blocked = replay(params)['frames']
        self.assertEqual(blocked[:4],rows[:4])
        self.assertEqual(blocked[4]['orders'][0]['reason'],'opening_halt')
        self.assertEqual(blocked[4]['orders'][0]['filled'],0)
        self.assertEqual(blocked[4]['holdings'][STOCK],10000)
        self.assertFalse(blocked[4]['nextPlan'])
        self.assertEqual(blocked[5]['orders'],[])

    def test_full_period_votes_against_independent_rolling_series(self):
        import pandas as pd
        base, _, bars, _ = work.inputs()
        days = base.sessions
        dividends = {(e.symbol,e.ex_date): float(e.per_share) for e in base.dividends
                     if e.announcement_date <= e.ex_date}
        levels, returns = {}, {}
        for sym in (STOCK,BOND):
            close = pd.Series([float(bars[sym][day].close) for day in days],index=days)
            cash = pd.Series([dividends.get((sym,day),0.0) for day in days],index=days)
            returns[sym] = (close + cash) / close.shift() - 1
            levels[sym] = (1 + returns[sym].fillna(0)).cumprod()
        indicators = [levels[STOCK] / levels[STOCK].rolling(120).mean() - 1,
                      levels[STOCK].pct_change(60) - levels[BOND].pct_change(60),
                      returns[STOCK].rolling(20).std() * 252**.5]
        decisions, _ = factor_schedule(days[:120],days[120:],days[120:],bars,base.dividends)
        for day, decision in decisions.items():
            values = [series[day] for series in indicators]
            self.assertEqual(decision['votes'],sum(map(int,[values[0]>0,values[1]>0,values[2]<.25])))
            for f,v in zip(decision['factors'],values):
                self.assertAlmostEqual(float(f['value']),v,places=10)

    def test_model_requires_own_scope_and_frequency(self):
        for change in [dict(weights='1,1,1,3'), dict(rebalance='monthly'), dict(start=work.OPTIONS['domesticFirst'])]:
            with self.subTest(change=change), self.assertRaises(work.InputError):
                replay(dict(CASE, model=MODEL, step='1') | change)
