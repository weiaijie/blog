import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from interactive_backtest import DEFAULTS, InputError, backtest, compare_windows, same_window


class SameWindowTests(unittest.TestCase):
    def test_reference_selection_replays_each_portfolio_from_shared_start(self):
        params = dict(DEFAULTS, start='2023-10-30', capital='100000', weights='1,1,1,3|3,1,0,6|1,0,0,1')
        report = compare_windows(params)
        bounds = set()
        for anchor in report['portfolios']:
            for years, period in anchor['periods'].items():
                query = report['overlays'][anchor['id']][years]
                bounds.add((query['start'],query['end']))
                self.assertEqual(query,dict(params,start=period['worstStart'],end=period['worstEnd']))
                result = same_window(query)
                for p,vector in zip(result['portfolios'],params['weights'].split('|'),strict=True):
                    single = backtest(dict(query,weights=vector))
                    self.assertEqual(p['summary'],single['summary'])
                    self.assertEqual(p['daily'][0]['nav'],1)
                    self.assertEqual(len(p['daily']),len(result['portfolios'][0]['daily']))
                    peak = Decimal(1)
                    for point, archived in zip(p['daily'],single['daily'],strict=True):
                        nav = archived['equity']/Decimal(query['capital'])
                        peak = max(peak,nav)
                        self.assertEqual(point,dict(**archived,nav=nav))
                        self.assertEqual(point['drawdown'],nav/peak-1)
                    if p['id']==anchor['id']:
                        self.assertEqual(p['summary'],period['worstReplay']['summary'])
                eligible = [p for p in result['portfolios'] if p['recoveryState']=='recovered']
                dates = [p['summary']['recovery'] for p in eligible]
                self.assertEqual(result['leaders']['firstRecovery'],
                                 [p['id'] for p in eligible if p['summary']['recovery']==min(dates)])
        self.assertGreater(len(bounds),2)

    def test_ties_flat_curves_and_missing_windows(self):
        params = dict(DEFAULTS,start='2026-10-01',capital='1',weights='1,0,0,1|1,0,0,1')
        self.assertIsNone(compare_windows(params)['overlays']['A'][1])
        report = same_window(params)
        self.assertEqual(report['leaders'],dict(highestPnl=['A','B'],shallowestDrawdown=['A','B'],firstRecovery=[]))
        self.assertTrue(all(p['recoveryState']=='no_drawdown' for p in report['portfolios']))
        with self.assertRaises(InputError):
            same_window(dict(params,weights='1,0,0,1'))
