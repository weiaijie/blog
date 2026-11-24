"""Exercise the November 23 profile through the public replay, archives and Agent metadata."""
from datetime import date
from decimal import Decimal
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import data_change_report as comparison
import factor_lab
import interactive_backtest as work
import method_windows
import recent_backtest as api
from build_entry_windows import entry_schedule
from research_profile import LATEST, NOV23, using


class Nov23ProfileTests(unittest.TestCase):
    def test_model_order_history_is_identical_on_common_prefix(self):
        for model in work.OPTIONS['replayModels']:
            p = dict(work.DEFAULTS, start='2026-11-12', end='2026-11-20', weights='1,0,0,1',
                     model=model, step='all', rebalance='signal' if model.startswith('multifactor') else 'monthly')
            if model == 'installments':
                p['installments'] = '3'
            self.assertEqual(api.calculate('replay',p,LATEST)['frames'],api.calculate('replay',p,NOV23)['frames'],model)

    def test_options_and_cutoffs_match_the_selected_version(self):
        opts = api.options(NOV23)
        self.assertEqual(opts['last'], '2026-11-23')
        self.assertEqual(opts['evidence']['addedSessions'], ['2026-11-23'])
        self.assertEqual(opts['replayEndpoint'], '/api/v4/backtest/replay')
        self.assertNotIn('dataChangeEndpoint',opts)
        self.assertEqual(api.options(LATEST)['dataChangeEndpoint'],'/api/v3/backtest/data-change')
        p = dict(work.DEFAULTS,start='2026-11-20',end='2026-11-23',weights='0,1,0,1')
        books = api.calculate('account', p, NOV23)
        self.assertEqual(books['admittedThrough'], '2026-11-23')
        self.assertEqual(books['summary']['end'], date(2026,11,23))
        self.assertEqual([(o['symbol'],o['filled'],o['reason']) for o in books['orders']],
                         [('513500',20200,'filled'),('511010',300,'filled')])
        with self.assertRaises(work.InputError):
            api.calculate('account',p,LATEST)
        with self.assertRaises(work.InputError):
            api.calculate('account',dict(p,end='2026-11-24'),NOV23)

    def test_sealed_model_results_have_independently_counted_endpoints(self):
        with using(NOV23):
            sessions = tuple(d for d in work.inputs()[0].sessions if str(d)>=method_windows.DEFAULTS['start'])
        endpoints = {year:[] for year in (1,2)}
        for days, ends in entry_schedule(sessions):
            for year, offset in ends.items():
                endpoints[year].append((days[0],days[offset]))
        for op, defaults in [('method-windows',method_windows.DEFAULTS),('technical-factors',factor_lab.DEFAULTS)]:
            with patch.dict(api.OPERATIONS, {op:lambda p:self.fail('Missed version-specific archive')}):
                new = api.calculate(op,dict(defaults,end='2026-11-23'),NOV23)
                old = api.calculate(op,dict(defaults,end='2026-11-20'),LATEST)
            self.assertEqual(new['dataVersion'],NOV23)
            for year, windows in endpoints.items():
                added = [(start,end) for start,end in windows if end > date(2026,11,20)]
                for model, metrics in new['periods'][str(year)].items():
                    before = old['periods'][str(year)][model]
                    self.assertEqual(metrics['count'],len(windows))
                    self.assertEqual(metrics['count']-before['count'],len(added))
                    scenario = comparison.SCENARIOS['domestic-'+model]
                    outcomes = []
                    for start,end in added:
                        replay = api.calculate('replay',comparison.replay_params(scenario,start,end),NOV23)
                        outcomes.append(comparison.measure(start,end,year,replay['frames'][-1]['equity']))
                    self.assertEqual(metrics['profitable']-before['profitable'],sum(w['pnl']>0 for w in outcomes))
                    self.assertEqual(metrics['reached']-before['reached'],
                                     sum(w['annualized_return']>=Decimal('.04') for w in outcomes))
                    self.assertEqual(Decimal(str(metrics['worstPnl'])),
                                     min(Decimal(str(before['worstPnl'])),*(w['pnl'] for w in outcomes)))
