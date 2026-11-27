"""Reconcile the 26 November version against the preceding frozen report and explicit daily replays."""
from datetime import date
from decimal import Decimal
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import data_change_report as change
import factor_lab
import interactive_backtest as work
import method_windows
import recent_backtest as api
from build_entry_windows import entry_schedule
from research_profile import NOV23, NOV26, using


class November26Tests(unittest.TestCase):
    def test_version_boundary_and_per_symbol_opening_orders(self):
        opts = api.options(NOV26)
        self.assertEqual(opts['replayEndpoint'], '/api/v5/backtest/replay')
        self.assertEqual(opts['evidence']['priorThrough'], '2026-11-23')
        self.assertEqual(opts['last'], '2026-11-26')
        self.assertNotIn('dataChangeEndpoint', opts)
        start = '2026-11-23'
        for end in ('2026-11-24', '2026-11-25', '2026-11-26'):
            p = dict(work.DEFAULTS, start=start, end=end, weights='0,1,0,1')
            result = api.calculate('account', p, NOV26)
            self.assertEqual(str(result['summary']['end']), end)
            orders = {o['symbol']: o for o in result['orders']}
            self.assertGreater(orders['511010']['filled'], 0)
            if end in opts['evidence']['openingHalts']:
                self.assertEqual((orders['513500']['filled'], orders['513500']['reason']), (0, 'opening_halt'))
            else:
                self.assertGreater(orders['513500']['filled'], 0)
            with self.assertRaises(work.InputError):
                api.calculate('account',p,NOV23)
            start = end
        with self.assertRaises(work.InputError):
            api.calculate('account',dict(p,end='2026-11-27'),NOV26)

    def test_old_order_history_matches_all_seven_model_replays(self):
        for model in change.LABELS:
            scenario = change.SCENARIOS['domestic-'+model]
            p = change.replay_params(scenario,date(2026,11,13),date(2026,11,23))
            self.assertEqual(api.calculate('replay',p,NOV23)['frames'],api.calculate('replay',p,NOV26)['frames'],model)

    def test_archives_match_independent_new_maturities(self):
        with using(NOV26):
            sessions = tuple(d for d in work.inputs()[0].sessions if str(d)>=method_windows.DEFAULTS['start'])
        periods = {1:[], 2:[]}
        for days, offsets in entry_schedule(sessions):
            for year, offset in offsets.items():
                if days[offset] > date(2026,11,23):
                    periods[year].append((days[0], days[offset]))
        for op, defaults in [('method-windows',method_windows.DEFAULTS),('technical-factors',factor_lab.DEFAULTS)]:
            new = api.calculate(op, dict(defaults,end='2026-11-26'), NOV26)
            old = api.calculate(op, dict(defaults,end='2026-11-23'), NOV23)
            self.assertEqual(new['dataVersion'], NOV26)
            for year, windows in periods.items():
                for model, metrics in new['periods'][str(year)].items():
                    scenario = change.SCENARIOS['domestic-'+model]
                    old_period = old['periods'][str(year)][model]
                    outcomes = []
                    for start,end in windows:
                        replay = api.calculate('replay',change.replay_params(scenario,start,end),NOV26)
                        outcomes.append(change.measure(start,end,year,replay['frames'][-1]['equity']))
                    self.assertEqual(metrics['count']-old_period['count'],len(windows))
                    self.assertEqual(metrics['profitable']-old_period['profitable'],sum(w['pnl']>0 for w in outcomes))
                    self.assertEqual(metrics['reached']-old_period['reached'],
                                     sum(w['annualized_return']>=Decimal('.04') for w in outcomes))
                    self.assertEqual(Decimal(str(metrics['worstPnl'])),
                                     min([Decimal(str(old_period['worstPnl']))]+[w['pnl'] for w in outcomes]))
